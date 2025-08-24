from openai import AsyncOpenAI
from dotenv import load_dotenv
from discord.ext import commands
from .variables import magical_characters
import os, random

load_dotenv()
wisher_client = AsyncOpenAI(api_key=os.getenv("openai_api_key"))
wisher_model = "o4-mini"


async def wish_creator():
    character = magical_characters[random.randint(0,(len(magical_characters)-1))]

    system_message = f"""
    Generate a three-sentence birthday wish in a tone **inspired** by the qualities of {character} from Harry Potter. 
    **If unable to follow the directive exactly, do not mention it in the response**.
    End the response by signing off as the character.
    """
    response = await wisher_client.responses.create(
        model = wisher_model,
        instructions=system_message,
        input="Wish the user a happy birthday!", 
        temperature=1,
        reasoning={"effort":"high"},
        max_output_tokens=2048, 
        store=False,
        service_tier="flex"
    )
    ai_response = response.output_text.strip()
    return ai_response

async def setup(bot: commands.Bot):
    pass