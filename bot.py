import discord
import archive
import hearts
import params

client_intents = discord.Intents()
client_intents.guilds = True
client_intents.members = True
client_intents.messages = True
client_intents.message_content = True
client_intents.guild_messages = True
client_intents.guild_reactions = True

client = discord.Client(intents = client_intents, max_messages=100000)
tree = discord.app_commands.CommandTree(client)

token = ""
with open('token.txt') as f:
    token = f.read()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    a = discord.Activity(type=discord.ActivityType.watching, name="for ❤️")
    await client.change_presence(status=discord.Status.online, activity=a)

    await archive.initialize(client)

    await tree.sync()

@client.event
async def on_message(request):
    if type(request.channel) == discord.DMChannel: #ignore dms
        return
    
    if type(request.channel) != discord.TextChannel: #ignore unknown channels
        return
        
    if type(request.author) != discord.member.Member: #ignore non guild users
        return
    
    reply = await archive.on_message(client, request)
    if reply:
        await request.reply(reply)

    reply = await hearts.on_message(client, request)
    if reply:
        await request.reply(reply)

@client.event
async def on_raw_reaction_add(payload):
    await archive.on_reaction_add(client, payload)
    await hearts.on_reaction_add(client, payload)


@client.event
async def on_raw_reaction_remove(payload):
    await archive.on_reaction_remove(client, payload)

@tree.context_menu(name="Parameters", auto_locale_strings=False)
async def parameters(interaction: discord.Interaction, message: discord.Message):
    await params.parameters(interaction, message, False)

@tree.context_menu(name="Raw Parameters", auto_locale_strings=False)
async def raw_parameters(interaction: discord.Interaction, message: discord.Message):
    await params.parameters(interaction, message, True)

client.run(token)