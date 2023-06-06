import discord
import db as database

db = database.load('archive.db')
if not db:
    db = {"guilds": {}}
    database.dump(db, 'archive.db')

async def initialize(client):
    return

async def setup_archive(client, guild_id, archive_id):
    if str(guild_id) in db["guilds"]:
        return

    guild = client.get_guild(guild_id)
    archive = guild.get_channel(archive_id)

    nominate = await archive.send("React with 📦 to enable archiving!\nReact any image in your archive with ❌ to delete.")
    await nominate.add_reaction('📦')
    await nominate.pin()

    data = {
        "nominate": nominate.id,
        "archive": archive_id,
        "users": {},
        "channels": []
    }

    db["guilds"][str(guild_id)] = data
    database.dump(db, 'archive.db')

async def add_channel(client, guild_id, channel_id):
    if not str(guild_id) in db["guilds"]:
        return

    db["guilds"][str(guild_id)]["channels"] += [channel_id]
    database.dump(db, 'archive.db')

async def create_archive(client, guild_id, user_id):
    guild = client.get_guild(guild_id)
    user = guild.get_member(user_id)
    name = user.display_name

    await delete_archive(client, guild_id, user_id)

    guild_data = db["guilds"][str(guild_id)]

    archive_id = guild_data["archive"]
    archive = guild.get_channel(archive_id)

    message = await archive.send(name + "'s archive")
    thread = await archive.create_thread(name=name, message=message, type=discord.ChannelType.public_thread)
    guild_data["users"][str(user_id)] = thread.id
    database.dump(db, 'archive.db')

    channels = guild_data["channels"]

    for channel_id in channels:
        channel = client.get_guild(guild_id).get_channel(channel_id)

        print("start", channel.name)
        history = [m async for m in channel.history(limit=None)][::-1]
        for m in history:
            if m.author.id == user_id:
                for a in m.attachments:
                    if "image" in a.content_type or "video" in a.content_type:
                        await thread.send(a.url)
                for e in m.embeds:
                    if e.type == "image" or e.type == "video":
                        await thread.send(e.url)
        print("finish", channel.name)

async def delete_archive(client, guild_id, user_id):
    guild_data = db["guilds"][str(guild_id)]

    if not str(user_id) in guild_data["users"]:
        return

    thread_id = guild_data["users"][str(user_id)]

    guild = client.get_guild(guild_id)
    
    if thread_id:
        archive_id = guild_data["archive"]
        archive = guild.get_channel(archive_id)

        await archive.get_partial_message(thread_id).delete()
        thread = archive.get_thread(thread_id)

        if thread:
            await thread.delete()

    del guild_data["users"][str(user_id)]
    database.dump(db, 'archive.db')
        
async def on_message(client, message):
    await on_command(client, message)

    if not message.attachments and not message.embeds:
        return

    guild = message.guild

    if not str(guild.id) in db["guilds"]:
        return
    
    guild_data = db["guilds"][str(guild.id)]

    if not message.channel.id in guild_data["channels"]:
        return 
    
    if not str(message.author.id) in guild_data["users"]:
        return 

    archive_id = guild_data["archive"]
    archive = guild.get_channel(archive_id)

    thread_id = guild_data["users"][str(message.author.id)]
    thread = archive.get_thread(thread_id)

    for a in message.attachments:
        if "image" in a.content_type or "video" in a.content_type:
            await thread.send(a.url)
    for e in message.embeds:
        if e.type == "image" or e.type == "video":
            await thread.send(e.url)

async def on_reaction_add(client, payload):
    guild_id = payload.guild_id

    if not str(guild_id) in db["guilds"]:
        return

    guild_data = db["guilds"][str(guild_id)]

    if payload.message_id == guild_data["nominate"] and str(payload.emoji) == "📦":
        await create_archive(client, guild_id, payload.user_id)
        return

    if str(payload.emoji) == "❌" and str(payload.user_id) in guild_data["users"]:
        if payload.channel_id == guild_data["users"][str(payload.user_id)]:
            thread_id = payload.channel_id
            thread = client.get_guild(guild_id).get_thread(thread_id)
            message = thread.get_partial_message(payload.message_id)

            await message.delete()

async def on_reaction_remove(client, payload):
    guild_id = payload.guild_id

    if not str(guild_id) in db["guilds"]:
        return

    guild_data = db["guilds"][str(guild_id)]

    if payload.message_id != guild_data["nominate"]:
        return

    if str(payload.emoji) != "📦":
        return

    await delete_archive(client, guild_id, payload.user_id)
    
async def on_command(client, message):
    if not message.author.guild_permissions.administrator:
        return

    command = message.content.lower()

    if command.startswith("$setup"):
        archive_id = int(command.split()[1][2:-1])
        await setup_archive(client, message.guild.id, archive_id)

    if command.startswith("$add"):
        channel_id = int(command.split()[1][2:-1])
        await add_channel(client, message.guild.id, channel_id)
    