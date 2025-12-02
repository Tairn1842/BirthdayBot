from openai import AsyncOpenAI
from dotenv import load_dotenv
from discord.ext import commands
from .variables import magical_characters
import os, numpy as np

load_dotenv()
wisher_client = AsyncOpenAI(api_key=os.getenv("openai_api_key"))
wisher_model = "gpt-5.1"


async def wish_creator():
    character = np.random.choice(magical_characters)

    response = await wisher_client.responses.create(
    model="gpt-5.1",
    input=[
        {"role": "developer",
        "content": [{
            "type": "input_text",
            "text": "You will be assigned a character from the fictional series \"Harry Potter\"."
            "You will impersonate the character, and respond to the given prompt as the character would. Your response should not be verbose."
            "It should be no longer than 5 sentences. End the response by signing off as the character."
            }]
        },
        {"role": "user",
        "content": [{
            "type": "input_text",
            "text": f"Wish the user a happy birthday as {character}."
            }]
        }
        ],
    text={"format": {"type": "text"},"verbosity": "medium"},
    reasoning={"effort": "high"},
    tools=[{"type": "web_search"}],
    store=False,
    include=["reasoning.encrypted_content",
            "web_search_call.action.sources"]
        )
    ai_response = response.output_text.strip()
    return ai_response

async def setup(bot: commands.Bot):
    pass