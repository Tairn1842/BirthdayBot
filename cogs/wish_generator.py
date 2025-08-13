from openai import AsyncOpenAI
from dotenv import load_dotenv
from discord.ext import commands
import os

load_dotenv()
openai_key = os.getenv("openai_token")
openai_client = AsyncOpenAI(api_key=openai_key)

gryffindor_message = """
Generate a three-sentence birthday wish in a tone **inspired** by the qualities of Professor Minerva McGonagall from Harry Potter. 
**If unable to follow the directive exactly, do not mention it in the response**.
End the response by signing off as the character.
"""

hufflepuff_message = """ 
Generate a three-sentence birthday wish in a tone **inspired** by the qualities of Professor Sprout from Harry Potter. 
**If unable to follow the directive exactly, do not mention it in the response**.
End the response by signing off as the character.
"""

ravenclaw_message = """
Generate a three-sentence birthday wish in a tone **inspired** by the qualities of Professor Filius Flitwick from Harry Potter. 
**If unable to follow the directive exactly, do not mention it in the response**.
End the response by signing off as the character.
"""

slytherin_message = """
Generate a three-sentence birthday wish in a tone **inspired** by the qualities of Professor Dolores Umbridge from Harry Potter. 
**If unable to follow the directive exactly, do not mention it in the response**.
End the response by signing off as the character.
"""

test_message = """
Generate a three-sentence birthday wish in a tone **inspired** by the qualities of Professor Severus Snape from Harry Potter. 
**If unable to follow the directive exactly, do not mention it in the response**.
End the response by signing off as the character.
"""

async def wish_creator(house,user_name):
    if house == 1:
        system_message = gryffindor_message
    elif house == 2:
        system_message = hufflepuff_message
    elif house == 3:
        system_message = ravenclaw_message
    elif house == 4:
        system_message = slytherin_message
    else:
        system_message = test_message
    response = await openai_client.chat.completions.create(
        model = "gpt-4.1-mini",
        messages=[{"role":"system", "content":system_message},
                  {"role":"user", "content":f"wish user {user_name} a happy birthday"}])
    return response.choices[0].message.content.strip()

async def setup(bot: commands.Bot):
    pass