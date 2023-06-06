import discord
import requests
from bs4 import BeautifulSoup

import PIL.Image
import io

async def get_image_from_url(url):
    h = requests.head(url)
    header = h.headers
    content_type = header.get('content-type')
    if content_type == "image/png":
        return (url, io.BytesIO(requests.get(url).content))
    elif content_type == "text/html":
        response = requests.get(url)
        soup = BeautifulSoup(response.text, features="html.parser")
        url = soup.find("meta", property="og:image")
        if url != None:
            url = url.get('content')
        if url != None:
            url = url.rsplit("?", 1)[0]
            return (url, io.BytesIO(requests.get(url).content))
    return None

async def get_images(message):
    images = []

    for a in message.attachments:
        if a.content_type == "image/png":
            data = await a.read()
            images += [(a.url, io.BytesIO(data))]
    
    for e in message.embeds:
        if e.type == "image":
            image = await get_image_from_url(e.url)
            if image:
                images += [image]
        elif e.type == "rich":
            image = await get_image_from_url(e.image.url)
            if image:
                images += [image]
    
    return images

def truncate(string, limit):
    if len(string) < limit:
        return string
    else:
        return string[:limit-3] + "..."

async def parameters(interaction: discord.Interaction, message: discord.Message, raw):        
    await interaction.response.defer(ephemeral=True, thinking=True)

    images = await get_images(message)

    if not images:
        await interaction.followup.send('No PNG image!', ephemeral=True)
        return

    embeds = []
    for url, image in images:
        if raw:
            embeds += [await get_raw_embed(url, image, message)]
        else:
            embeds += [await get_pretty_embed(url, image, message)]

    await interaction.followup.send(embeds=embeds, ephemeral=True)

async def get_pretty_embed(url, image, message):    
    error = ""
    try:
        metadata = ""
        with PIL.Image.open(image) as img:
            if "parameters" in img.info:
                metadata = img.info["parameters"].strip()

        if metadata == "":
            error = "No metadata found!"
        else:
            positive, other = metadata.split("Negative prompt: ", 1)
            negative, other = other.rsplit("\n", 1)
    except Exception:
        error = f'Unknown metadata format!\n```\n{truncate(metadata, 3072)}\n```'

    embed = discord.Embed()
    embed.color = 0xfc0362
    embed.set_author(name=f'{message.author.display_name}', icon_url=f'{message.author.display_avatar.url}')

    embed.set_thumbnail(url=url)

    if not error:
        keys = []
        values = {}
        for pair in other.split(", "):
            key, value = pair.split(": ", 1)
            keys += [key]
            values[key] = value

        embed.add_field(name="Prompt", value=truncate(positive, 1024), inline=False)
        embed.add_field(name="Negative Prompt", value=truncate(negative, 1024), inline=False)

        for key in keys:
            embed.add_field(name=key, value=truncate(values[key], 1024), inline=True)
    else:
        embed.description = error
        
    return embed

async def get_raw_embed(url, image, message):
    error = ""
    try:
        metadata = ""
        with PIL.Image.open(image) as img:
            if "parameters" in img.info:
                metadata = img.info["parameters"].strip()
        if metadata == "":
            error = "No metadata found!"
    except Exception:
        error = f'Error reading metadata!'

    embed = discord.Embed()
    embed.color = 0xfc0362
    embed.set_author(name=f'{message.author.display_name}', icon_url=f'{message.author.display_avatar.url}')
    embed.set_thumbnail(url=url)

    if not error:
        embed.description = f"```\n{truncate(metadata, 3072)}\n```"
    else:
        embed.description = error
    
    return embed