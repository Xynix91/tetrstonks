import discord
from discord.ext import tasks, commands
from server.stonksapi import pay_dividends, make_sell_offer, retract_sell_offer, buy_stocks, get_offers, get_leaderboard, get_investor, update_cache
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
    
    @tasks.loop(minutes=5)
    async def update_cache(self):
        update_cache()
        print('Updated cache!')

    async def on_ready(self):
        self.daily_dividend.start()
        self.update_cache.start()
        print(f'Logged on as {self.user}!')

intents = discord.Intents.default()
intents.message_content = True

bot = StonksBot()

@bot.command()
async def buy(ctx, stock, value):
    buy_stocks(str(ctx.author.id), stock, float(value))
    await ctx.channel.send(f"{ctx.author.name} bought {value} of {stock} stock!")

@bot.command()
async def selloffer(ctx, stock, price, maximum):
    price = float(price)
    maximum = float(maximum)
    make_sell_offer(str(ctx.author.id), stock, float(price), float(maximum))
    await ctx.channel.send(f"{ctx.author.name} is now selling {maximum/price} {stock} stocks for {price} coins each!")

@bot.command()
async def retractoffer(ctx, stock):
    retract_sell_offer(str(ctx.author.id), stock)
    await ctx.channel.send(f"{ctx.author.name} has retracted their selling offer of {stock} stocks.")

@bot.command()
async def leaderboard(ctx):
    lb_data = get_leaderboard()
    lines = []
    for i in lb_data:
        username = await bot.fetch_user(i['id'])
        lines.append(f"{username}: {i['balance']} coins")
    await ctx.channel.send("\n".join(lines))

@bot.command(aliases=['investorinfo'])
async def playerinfo(ctx, id=None):
    if id is None:
        id = ctx.author.id
    elif type(id) != int and id[:2] == "<@" and id[-1] == ">":
        id = id[2:-1]
    player_data = get_investor(id)
    lines = []
    username = await bot.fetch_user(id)
    lines.append(str(username))
    lines.append(f"Balance: {player_data['balance']}")
    lines.append("")
    lines.append("Portfolio:")
    for stock, value in player_data['portfolio'].items():
        lines.append(f"{stock}: {value}")
    await ctx.channel.send("\n".join(lines))

@bot.command()
async def showoffers(ctx, page=1):
    offer_data = get_offers()
    lines = []
    for i in offer_data:
        if i['seller'] == "bank":
            username = "The Bank"
        else:
            username = await bot.fetch_user(i['seller'])
        lines.append(f"{username}: {i['quantity']} {i['stock']} stocks for {i['price']} each")
    if (page - 1) * 10 < len(offer_data):
        await ctx.channel.send("\n".join(lines[(page - 1 * 10):min(page * 10, len(offer_data))]))

bot.run(TOKEN)
