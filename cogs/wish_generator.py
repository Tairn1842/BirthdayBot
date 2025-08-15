from openai import AsyncOpenAI
from dotenv import load_dotenv
from discord.ext import commands
import os, random

load_dotenv()
wisher_client = AsyncOpenAI(base_url="https://api.fireworks.ai/inference/v1", 
                            api_key=os.getenv("fireworks_token"))
wisher_model = "accounts/fireworks/models/gpt-oss-120b"

gryffindor_characters = ["Professor Albus Dumbledore", "Professor Minerva McGonagall", "Oliver Wood"]
hufflepuff_characters = ["Professor Sprout", "Newt Scamander", "Nymphadora Tonks"]
ravenclaw_characters = ["Professor Fillius Flitwick", "Professor Gilderoy Lockhart", "Cho Chang"]
slytherin_characters = ["Professor Severus Snape", "Professor Dolores Umbridge", "Professor Horace Slughorn"]

async def wish_creator(house):
    if house == 1:
        character = gryffindor_characters[random.randint(0,2)]
    elif house == 2:
        character = hufflepuff_characters[random.randint(0,2)]
    elif house == 3:
        character = ravenclaw_characters[random.randint(0,2)]
    elif house == 4:
        character = slytherin_characters[random.randint(0,2)]

    system_message = f"""
    Generate a three-sentence birthday wish in a tone **inspired** by the qualities of {character} from Harry Potter. 
    **If unable to follow the directive exactly, do not mention it in the response**.
    End the response by signing off as the character.
    """
    response = await wisher_client.chat.completions.create(
        model = wisher_model,
        messages=[{"role":"system", "content":system_message},
                  {"role":"user", "content":"wish the user a happy birthday"}])
    return response.choices[0].message.content.strip()

async def setup(bot: commands.Bot):
    pass