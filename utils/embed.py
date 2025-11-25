from typing import Union
import discord

def create_embed(
    title: str,
    description: str,
    color: Union[discord.Color, int]
) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)