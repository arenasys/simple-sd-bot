import discord
import db as database
import requests
from bs4 import BeautifulSoup

EMOJIS = "❤️ 💖 ⭐ 👅 🥵 😳 😍 💦 👍 👌 😭 💢 ♥️ ❤️‍🔥 💕 💗 💓 💞 💟 😻 🫶 🖤 💙 🤎 💝 💚 😘 ❤️‍🩹 🧡 💜 🤍 💛 💘 🔥 💯 🌊 👍🏻 🍑 🙌 🎉 🐱 🍦 😻 "
NITRO = []

db = database.load('hearts.db')
if not db:
    db = {"guilds": {}}
    database.dump(db, 'hearts.db')

async def setup_hearts(client, guild_id, hearts_id, hearts_number):
    if str(guild_id) in db["guilds"]:
        return
    
    data = {
        "hearts": hearts_id,
        "required": hearts_number,
        "channels": [],
        "history": []
    }

    db["guilds"][str(guild_id)] = data
    database.dump(db, 'hearts.db')

async def add_channel(client, guild_id, channel_id):
    if not str(guild_id) in db["guilds"]:
        return

    guild_data = db["guilds"][str(guild_id)]

    if not channel_id in guild_data["channels"]:
        guild_data["channels"] += [channel_id]
        database.dump(db, 'hearts.db')

    channel = client.get_guild(guild_id).get_channel(channel_id)

    print("start", channel.name)
    history = [m async for m in channel.history(limit=None)][::-1]
    for message in history:
        await check_for_reacts(client, message)
    print("finish", channel.name)

async def on_message(client, message):
    if not message.author.guild_permissions.administrator:
        return

    command = message.content.lower()

    if command.startswith("^setup"):
        hearts_id = int(command.split()[1][2:-1])
        hearts_number = int(command.split()[2])
        await setup_hearts(client, message.guild.id, hearts_id, hearts_number)

    if command.startswith("^add"):
        channel_id = int(command.split()[1][2:-1])
        await add_channel(client, message.guild.id, channel_id)

async def on_reaction_add(client, payload):
    guild_id = payload.guild_id

    if not str(guild_id) in db["guilds"]:
        return

    guild_data = db["guilds"][str(guild_id)]
    hearts_id = guild_data["hearts"]

    await check_for_delete(client, payload)

    if not payload.channel_id in guild_data["channels"]:
        return

    if payload.message_id in guild_data["history"]:
        return
    
    channel_id = payload.channel_id
    channel = client.get_guild(guild_id).get_channel(channel_id)
    message = await channel.fetch_message(payload.message_id)

    await check_for_reacts(client, message)

async def check_for_delete(client, payload):
    if str(payload.emoji) != "❌":
        return

    guild_id = payload.guild_id
    guild_data = db["guilds"][str(guild_id)]
    hearts_id = guild_data["hearts"]
    hearts = client.get_guild(guild_id).get_channel(hearts_id)

    if payload.channel_id != hearts_id:
        return

    message = await hearts.fetch_message(payload.message_id)
    embed = message.embeds
    if not embed:
        return
    embed = embed[0]
    author_id = embed.author.icon_url.split("/")[4]

    if author_id != str(payload.user_id):
        return

    await message.delete()

async def check_for_reacts(client, message):
    guild_data = db["guilds"][str(message.guild.id)]

    if message.id in guild_data["history"]:
        return

    if not message.attachments and not message.embeds:
        return

    total = []
    for r in message.reactions:
        valid = str(r.emoji) + " " in EMOJIS or getattr(r.emoji, "name", "") in NITRO
        if not valid:
            continue
        total += [user.id async for user in r.users()]
    total = len(set(total))
    
    if total < guild_data["required"]:
        return

    url = None

    for a in message.attachments:
        if "image" in a.content_type:
            url = a.url
            break
    
    for e in message.embeds:
        if e.type == "image":
            url = e.url
            break
    
    if url:
        await heart_message(client, message, url)
    
async def get_imgur(url):
    return BeautifulSoup(requests.get(url.replace('mobile.', '')).text, 'html.parser').find('meta', attrs={'property': 'og:image'}).get('content').replace('?fb', '')

async def heart_message(client, message, url):
    guild_id = message.guild.id
    channel_id = message.channel.id
    message_id = message.id
    author = message.author

    embed = discord.Embed()
    embed.color = 0xfc0362
    embed.set_author(name=f'{author.display_name}', icon_url=f'{author.display_avatar.url}')
    embed.add_field(name='Sauce??', value=f'[Jump to ](https://discordapp.com/channels/{guild_id}/{channel_id}/{message_id})<#{channel_id}>')

    if url.startswith(r"https://imgur.com"):
        url = await get_imgur(url)

    embed.set_image(url=url)

    guild_data = db["guilds"][str(guild_id)]
    hearts_id = guild_data["hearts"]
    hearts = client.get_guild(guild_id).get_channel(hearts_id)

    await hearts.send(embed=embed)

    guild_data["history"] += [message_id]
    database.dump(db, 'hearts.db')
