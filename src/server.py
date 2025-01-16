from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
import os
from openai import OpenAI
import json
from pymongo import MongoClient
from agents import weather_agent, holiday_agent, triage_agent, sole_weather_agent
from chat_streamer import ChatStreamMongoMemory

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DATABASE")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
chats_collection = db[os.getenv("CHATS_COLLECTION")]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

print("MONGO_URI", MONGO_URI)

app = FastAPI()

@app.get("/hello")
async def hello():
    return JSONResponse(content={"message": "Hello, FastAPI is working!"})

multi_agent_chat_streamer = ChatStreamMongoMemory(
    client=openai_client,
    agents=[weather_agent, holiday_agent, triage_agent],
    triage_agent=triage_agent,
    chats_collection=chats_collection
)

@app.get("/chat-complete-multi-agent")
async def chat_complete_multi_agent(request: Request, chat_id: str = Query(...), message: str = Query(...)):
    print("Chat ID", chat_id)
    print("Message", message)
    async def event_generator():
        async for event in multi_agent_chat_streamer.stream_chat(chat_id, message):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


solo_chat_streamer = ChatStreamMongoMemory(
    client=openai_client,
    agents=[sole_weather_agent],
    triage_agent=sole_weather_agent,
    chats_collection=chats_collection
)

@app.get("/chat-complete-single-agent")
async def chat_complete_single_agent(request: Request, chat_id: str = Query(...), message: str = Query(...)):
    print("Chat ID", chat_id)
    print("Message", message)
    async def event_generator():
        async for event in solo_chat_streamer.stream_chat(chat_id, message):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
