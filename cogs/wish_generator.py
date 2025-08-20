from together import AsyncTogether
from dotenv import load_dotenv
from discord.ext import commands
import os, random, re

load_dotenv()
wisher_client = AsyncTogether(api_key=os.getenv("together_token"))
wisher_model = "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"


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
    response = await wisher_client.chat.completions.create(
        model = wisher_model,
        messages=[{"role":"system", "content":system_message},
                  {"role":"user", "content":"wish the user a happy birthday"}])
    ai_response = response.choices[0].message.content
    clean = re.sub(r"<think>.*?</think>", "", ai_response, flags=re.DOTALL).strip()
    return clean

async def setup(bot: commands.Bot):
    pass