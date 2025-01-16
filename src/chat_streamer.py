from abc import ABC, abstractmethod
import json
import time
from agent_helper import Agent

class BaseMultiAgentChatStreamer(ABC):
    """
    Abstract base class for chat streaming logic.
    Enforces the implementation of message history and save methods.
    """
    def __init__(self, client, agents, triage_agent):
        self.agent_map = {agent.name: agent for agent in agents}
        self.tool_map = {}
        for agent in agents:
            self.tool_map.update(agent.tool_map)
        self.client = client
        self.triage_agent = triage_agent

    @abstractmethod
    def get_message_history(self, chat_id):
        """
        Fetch message history for a given chat ID.
        Must be implemented in subclasses.
        """
        pass

    @abstractmethod
    def append_messages(self, chat_id, messages):
        """
        Save messages for a given chat ID.
        Must be implemented in subclasses.
        """
        pass

    def __get_chat_messages(self, messages):
        return [
            {key: msg[key] for key in ("role", "content", "tool_calls", "tool_call_id") if key in msg}
            for msg in messages
        ]

    def __process_tool_calls(self, function_arguments, function_names, tool_call_ids, current_agent, new_messages):
        for index in function_names:
            args = json.loads(function_arguments[index])
            function_name = function_names[index]
            tool_call_id = tool_call_ids[index]
            yield {'event': 'init_func', 'function_name': function_name, 'args': args, 'index': index}
            resp = self.tool_map[function_name](**args)
            if type(resp) is Agent:
                current_agent = resp
                yield {'event': 'agent_transfer', 'agent': current_agent.name}
                function_call_result_message = {
                    "role": "tool",
                    "content": "Transferred to agent " + current_agent.name,
                    "tool_call_id": tool_call_id,
                    "agent": current_agent.name,
                }
            else:
                yield {'event': 'complete', 'response': resp}
                function_call_result_message = {
                    "role": "tool",
                    "content": json.dumps(resp),
                    "tool_call_id": tool_call_id,
                    "agent": current_agent.name,
                }
            new_messages.append({
                "at": int(time.time()), **function_call_result_message
            })
        yield current_agent

    async def stream_chat(self, chat_id, message):
        message_history = self.get_message_history(chat_id)
        new_messages = [{"role": "user", "content": message}]
        ai_resp = ""
        pending_tool_calls = False
        processing_complete = False

        current_agent = (
            self.agent_map[message_history[-1]["agent"]]
            if message_history and message_history[-1].get("agent")
            else self.triage_agent
        )

        while not processing_complete:
            stream = self.client.chat.completions.create(
                model="gpt-4o",
                messages=self.__get_chat_messages(
                    [{"role": "system", "content": current_agent.instructions}]
                    + message_history
                    + new_messages
                ),
                tools=current_agent.tools,
                stream=True,
            )
            function_arguments, function_names, tool_call_ids = {}, {}, {}
            is_collecting_function_args = False

            for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason
                if delta.content is not None:
                    yield {'msg': delta.content}
                    ai_resp += delta.content
                if delta.tool_calls:
                    pending_tool_calls = True
                    is_collecting_function_args = True
                    tool_call = delta.tool_calls[0]
                    index = tool_call.index
                    if tool_call.id:
                        tool_call_ids[index] = tool_call.id
                    if tool_call.function.name:
                        function_names[index] = tool_call.function.name
                        yield {'function_name': tool_call.function.name, 'index': index}
                    if tool_call.function.arguments:
                        if index not in function_arguments:
                            function_arguments[index] = ""
                        function_arguments[index] += tool_call.function.arguments
                if finish_reason == "stop" and not pending_tool_calls:
                    processing_complete = True
                if finish_reason == "tool_calls" and is_collecting_function_args:
                    if ai_resp:
                        yield {'event': 'mid', 'response': ai_resp}
                        ai_resp = ""
                        new_messages.append({
                            'role': 'assistant',
                            'content': ai_resp,
                            "at": int(time.time())
                        })
                    new_messages.append({
                        "role": "assistant",
                        "agent": current_agent.name,
                        "tool_calls": [
                            {
                                "id": tool_call_ids[index],
                                "type": "function",
                                "function": {
                                    "arguments": function_arguments[index],
                                    "name": function_names[index],
                                },
                            }
                            for index in function_names
                        ],
                        "at": int(time.time())
                    })
                    for result in self.__process_tool_calls(
                        function_arguments, function_names, tool_call_ids, current_agent, new_messages
                    ):
                        if type(result) is Agent:
                            current_agent = result
                        else:
                            yield result
                    function_arguments, function_names, tool_call_ids = {}, {}, {}
                    pending_tool_calls = False
        new_messages.append({
            "role": "assistant", "content": ai_resp, "agent": current_agent.name,  "at": int(time.time())
        })
        self.append_messages(chat_id, new_messages)
        yield {'event': 'complete', 'response': ai_resp}

class ChatStreamMongoMemory(BaseMultiAgentChatStreamer):
    def __init__(self, client, agents, triage_agent, chats_collection):
        super().__init__(client, agents, triage_agent)
        self.chats_collection = chats_collection

    def get_message_history(self, chat_id):
        db_messages = list(self.chats_collection.find({"chat_id": chat_id}, sort=[("_id", 1)]))
        print("History Messages", db_messages, flush=True)
        return db_messages

    def append_messages(self, chat_id, new_messages):
        self.chats_collection.insert_many(
            [{"chat_id": chat_id, **message} for message in new_messages])
