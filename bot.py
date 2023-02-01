import discord
import hearts

client_intents = discord.Intents()
client_intents.guilds = True
client_intents.members = True
client_intents.messages = True
client_intents.message_content = True
client_intents.guild_messages = True
client_intents.guild_reactions = True

client = discord.Client(intents = client_intents, max_messages=100000)

token = ""

with open('token.txt') as f:
    token = f.read()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    a = discord.Activity(type=discord.ActivityType.watching, name="for ❤️")
    await client.change_presence(status=discord.Status.online, activity=a)

@client.event
async def on_message(request):
    if type(request.channel) == discord.DMChannel: #ignore dms
        return
    
    if type(request.channel) != discord.TextChannel: #ignore unknown channels
        return
        
    if type(request.author) != discord.member.Member: #ignore non guild users
        return

    reply = await hearts.on_message(client, request)
    if reply:
        await request.reply(reply)

@client.event
async def on_raw_reaction_add(payload):
    await hearts.on_reaction_add(client, payload)

client.run(token)