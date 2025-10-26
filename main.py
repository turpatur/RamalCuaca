import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv 
import os 
from aiohttp import request
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta, timezone
from aiohttp import ClientSession


load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!p', intents=intents)
URL = os.getenv('URL')

WEATHER_CODE_MAP = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫",
    48: "Depositing rime fog 🌫❄️",
    51: "Light drizzle 🌦",
    53: "Moderate drizzle 🌦",
    55: "Dense drizzle 🌧",
    56: "Light freezing drizzle ❄️🌧",
    57: "Dense freezing drizzle ❄️🌧",
    61: "Slight rain 🌧",
    63: "Moderate rain 🌧",
    65: "Heavy rain 🌧💧",
    66: "Light freezing rain ❄️🌧",
    67: "Heavy freezing rain ❄️🌧",
    71: "Slight snow fall ❄️",
    73: "Moderate snow fall ❄️",
    75: "Heavy snow fall ❄️❄️",
    77: "Snow grains ❄️",
    80: "Slight rain showers 🌦",
    81: "Moderate rain showers 🌧",
    82: "Violent rain showers 🌧🌩",
    85: "Slight snow showers 🌨",
    86: "Heavy snow showers 🌨❄️",
    95: "Thunderstorm ⚡",
    96: "Thunderstorm with slight hail ⛈️",
    99: "Thunderstorm with heavy hail ⛈️",
}

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


@bot.command(name="cuaca")
async def get_weather(ctx):
    """Get current weather for Jakarta (GMT+7) using Open-Meteo API.""" 
    WIB = timezone(timedelta(hours=7))
    now_local = datetime.now(WIB)
    now_utc = now_local.astimezone(timezone.utc)
    start_date = now_utc.strftime("%Y-%m-%d")
    end_date = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "latitude": -6.4,
        "longitude": 106.8186,
        "hourly": "rain,precipitation,weather_code",
        "start_date": start_date,
        "end_date": end_date,
        "models": "metno_seamless",
    }

    url = "https://api.open-meteo.com/v1/forecast"

    async with ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                await ctx.send(f"⚠️ API error: {resp.status}")
                return
            data = await resp.json()

    hourly = data["hourly"]
    df = pd.DataFrame({
        "date": pd.to_datetime(hourly["time"], utc=True),
        "rain": hourly["rain"],
        "precipitation": hourly["precipitation"],
        "weather_code": hourly["weather_code"],
    }).set_index("date").sort_index()

    # interpolate per-minute and find nearest to current UTC time
    interp_df = df.resample("1min").interpolate(method="linear")
    nearest_idx = interp_df.index.get_indexer([now_utc], method="nearest")[0]
    weather_now = interp_df.iloc[[nearest_idx]]
    weather_now.index = weather_now.index.tz_convert(WIB)

    code = round(float(weather_now["weather_code"].iloc[0]))
    weather_desc = WEATHER_CODE_MAP.get(code, f"Unknown ({code})")

    msg = (
        f"📍 **Weather forecast (Depok)**\n"
        f"🕒 Time: `{weather_now.index[0].strftime('%Y-%m-%d %H:%M:%S %Z')}`\n"
        f"🌤 Condition: **{weather_desc}**\n"
        f"🌧 Rain: `{weather_now['rain'].iloc[0]:.2f} mm`\n"
        f"💧 Precipitation: `{weather_now['precipitation'].iloc[0]:.2f} mm`"
    )

    await ctx.send(msg)
    
if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
