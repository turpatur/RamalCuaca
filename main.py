import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv 
import os 
from aiohttp import request

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!p', intents=intents)
URL = os.getenv('URL')

@bot.event
async def on_ready():
    print("Aman le")
    print(URL)

@bot.command(name="get")
async def get_fact(ctx):
    URL = os.getenv('URL')

    async with request("GET", URL, headers={}) as response: 
        if response.status == 200:
            data = await response.json()
            await ctx.send(data["data"][0])
        else:
            await ctx.send(f"Response error {response.status}")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
