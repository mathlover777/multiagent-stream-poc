from agent_helper import Agent
from typing import Annotated
from enum import Enum

class TemparatureUnit(Enum):
    c = "c"
    f = "f"

def is_holiday(
    temparature: Annotated[int, "Temparature"],
    unit: Annotated[TemparatureUnit, "Unit of the temparature"],
    **kwargs):
    """
    To determine if its holiday as per temperature
    """
    if unit == "f":
        temparature = (temparature - 32) * 5/9
    return {
        "is_holiday": temparature > 35
    }

def get_weather(
        location: Annotated[str, "name of the city"],
        unit: Annotated[TemparatureUnit, "Unit of the temparature"],
        **kwargs):
    if location.lower() == "kolkata":
        temp = 40
    else:
        temp = 30
    if unit == "f":
        temp = temp * 9/5 + 32
    return {
        "temp": temp
    }


weather_agent = Agent(
    name="weather_agent",
    instructions=(
        "You are a weather agent. You will find temprarature using get_weather tool. "
        "If You are not sure, you can transfer to triage agent or holiday agent"
        ".if you are doing transfer then you can do only one transfer at a time"
    ),
    functions=[get_weather]
)

holiday_agent = Agent(
    name="holiday_agent",
    instructions=(
        "Given a days weather you will use is_holiday tool to determine if it is a holiday. "
        "If You are not sure, you can transfer to triage agent or weathr agent"
        "If you do not have the weather you can let the triage know that"
        ".if you are doing transfer then you can do only one transfer at a time"
    ),
    functions=[is_holiday]
)

triage_agent = Agent(
    name="triage_agent",
    instructions=(
        "You are a triage agent. You will help the user with their problem."
        " You will redirect user to specific agent. Holiday depends on temparature. So you can use weather_agent or holiday_agent"
        "Also if the user asks about holiday, you can first use the weather agent to get weather then use holiday agent to check if it is a holiday"
        ". Also plan the solution properly before agent transfer, so that other agents know the full plan. By plan I mean describe it in text first"
        ".if you are doing transfer then you can do only one transfer at a time"
    ),
)

def transfer_to_weather_agent():
    return weather_agent


def transfer_to_holiday_agent():
    return holiday_agent


def transfer_to_triage_agent():
    return triage_agent


triage_agent.add_tool(transfer_to_weather_agent)
triage_agent.add_tool(transfer_to_holiday_agent)

holiday_agent.add_tool(transfer_to_weather_agent)
holiday_agent.add_tool(transfer_to_triage_agent)

weather_agent.add_tool(transfer_to_holiday_agent)
weather_agent.add_tool(transfer_to_triage_agent)


sole_weather_agent = Agent(
    name="weather_agent",
    instructions=(
        "You are a weather agent. You will find temprarature using get_weather tool. Your name is Ding"
    ),
    functions=[get_weather]
)