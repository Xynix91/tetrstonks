import discord
from discord.ext import tasks, commands
from stonksapi import pay_dividends, make_sell_offer, retract_sell_offer, buy_stocks, show_offers, show_investors
import asyncio
import datetime
import pytz
import os

TOKEN = open("token.txt", "r").read()
MIDNIGHT_TIME = datetime.time(hour=0)
class StonksBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix="$",
            intents=intents,
            help_command=None,
        )

    @tasks.loop(time=MIDNIGHT_TIME)
    async def daily_dividend(self):
        pay_dividends()
    
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.daily_dividend.start()

intents = discord.Intents.default()
intents.message_content = True

bot = StonksBot()

@bot.command()
async def buy(ctx, stock, value):
    buy_stocks(ctx.author.id, stock, float(value))
    await ctx.channel.send(f"{ctx.author.name} bought {stock} for {value}!")

@bot.command()
async def selloffer(ctx, stock, price, maximum):
    make_sell_offer(ctx.author.id, stock, float(price), float(maximum))
    await ctx.channel.send(f"{ctx.author.name} is now selling {maximum/price} {stock} stocks for {price} coins each!")

@bot.command()
async def retractoffer(ctx, stock):
    retract_sell_offer(ctx.author.id, stock)
    await ctx.channel.send(f"{ctx.author.name} has retracted their selling offer of {stock} stocks.")

@bot.command()
async def showplayers(ctx):
    await ctx.channel.send(show_investors())

@bot.command()
async def showoffers(ctx):
    await ctx.channel.send(show_offers())

bot.run(TOKEN)
