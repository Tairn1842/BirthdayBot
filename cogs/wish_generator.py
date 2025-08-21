from openai import AsyncOpenAI
from dotenv import load_dotenv
from discord.ext import commands
import os, random, re

load_dotenv()
wisher_client = AsyncOpenAI(api_key=os.getenv("openai_api_key"))
wisher_model = "gpt-4.1"


magical_characters = ["Albus Dumbledore", "Minerva McGonagall", "Oliver Wood", "Percy Weasley", "Remus Lupin", 
                      "Sirius Black", "Molly Weasley", "Arthur Weasley", "Professor Sprout", "Newt Scamander", 
                      "Nymphadora Tonks", "Fillius Flitwick", "Gilderoy Lockhart", "Helena Ravenclaw", 
                      "Lord Voldermort", "Lucius Malfoy", "Bellatrix Lestrange", "Dolores Umbridge", 
                      "Severus Snape", "Horace Slughorn", "Rubeus Hagrid", "Sybill Trewalney", "Alastor Moody", 
                      "Cedric Diggory", "Harry Potter", "Ron Weasley", "Hermione Granger", "Fred Weasley", "Geroge Weasley", 
                      "Ginny Weasley", "Dobby", "Neville Longbottom", "Luna Lovegood", "Draco Malfoy"]
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
        max_output_tokens=512, 
        store=False
    )
    ai_response = response.output_text.strip()
    return ai_response

async def setup(bot: commands.Bot):
    pass