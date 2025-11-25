import discord

from database.db import get_user_balance
from utils.emojis import PNC_EMOJI_STR
from utils.embed_factory import EmbedFactory
from ui.game.flip import CoinFlipView
from config import MIN_BET, THUMBNAIL_URL, FLIP_GIF_URL, CURRENCY_NAME

async def on_coinflip_command(message: discord.Message) -> None:
    try:
        bet = int(message.content.split()[1])
    except (IndexError, ValueError):
        embed = discord.Embed(
            description="`?フリップ <掛け金>`の形式で入力してください。",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
        return

    min_bet = MIN_BET["flip"]    
    if bet < min_bet:
        embed = EmbedFactory.bet_too_low(min_bet=MIN_BET)
        await message.channel.send(embed=embed)
        return
    
    balance = get_user_balance(message.author.id)
    if balance is None:
        embed = EmbedFactory.not_registered()
        await message.channel.send(embed=embed)
        return
        
    if bet > balance:
        embed = EmbedFactory.insufficient_balance(balance=balance)
        await message.channel.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"{CURRENCY_NAME}フリップ",
        description=f"**掛け金**\n### {PNC_EMOJI_STR}`{bet}`",
        color=0x393a41
    )
    embed.set_author(name=f"{message.author.name}", icon_url=message.author.display_avatar.url)
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_image(url=FLIP_GIF_URL)

    view = CoinFlipView(message.author, bet)
    await message.channel.send(embed=embed, view=view)