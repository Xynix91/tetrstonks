import discord
from discord.ext import tasks, commands
import asyncio
import datetime
import pytz

TOKEN = open('token.txt').read()
MIDNIGHT_TIME = datetime.time(hour=0)
class StonksClient(discord.Client):
    @tasks.loop(time=MIDNIGHT_TIME)
    async def daily_msg(self):
        print("hi")
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.daily_msg.start()

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        if message.content.startswith("$YourMom"):
            await message.channel.send("je moeder kanker")
        if message.content.startswith("$time"):
            await message.channel.send(datetime.datetime.now())    

intents = discord.Intents.default()
intents.message_content = True

client = StonksClient(intents=intents)
client.run(TOKEN)
