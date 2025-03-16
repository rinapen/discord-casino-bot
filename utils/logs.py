import discord
from bot import bot
import config
from config import WIN_EMOJI, LOSE_EMOJI, DRAW_EMOJI

async def send_casino_log(interaction: discord.Interaction, emoji: str, price: int, description: str, color: discord.Color):
    embed = discord.Embed(title=interaction.user.name, description=f"### {emoji} {price} PNC ", color=color)
    casino_channel = bot.get_channel(int(config.CASINO_LOG_CHANNEL_ID))
    if casino_channel:
        await casino_channel.send(embed=embed)

async def b_send_casino_log(interaction: discord.Interaction, bet: int, payout: int, description: str):
    """カジノログを送信する関数（出金額に基づいた損益計算）"""
    profit = payout - bet  # **損益を計算**
    abs_profit = abs(profit)  # **変動額の絶対値**

    if profit > 0:
        emoji = WIN_EMOJI
        color = discord.Color.green()
    elif profit < 0:
        emoji = LOSE_EMOJI
        color = discord.Color.red()
    else:
        emoji = DRAW_EMOJI
        color = discord.Color.gold()

    embed = discord.Embed(
        title=f"{interaction.user.name}",
        description=f"### {emoji} {abs_profit} PNC\n{description}",
        color=color
    )

    casino_channel = bot.get_channel(int(config.CASINO_LOG_CHANNEL_ID))
    if casino_channel:
        await casino_channel.send(embed=embed)


async def send_paypay_log(user, amount, fee, net_amount, is_register=False):
    """指定チャンネルに入金履歴を送信"""
    channel = bot.get_channel(int(config.PAYPAY_LOG_CHANNEL_ID))
    if channel:
        embed = discord.Embed(
            title="💰 入金履歴" if not is_register else "🆕 口座開設 & 入金履歴",
            color=discord.Color.blue() if not is_register else discord.Color.green()
        )
        embed.add_field(name="👤 ユーザー", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="💰 入金額", value=f"`{int(amount):,} pay`", inline=False)
        embed.add_field(name="💸 手数料", value=f"`{int(fee):,} pay`", inline=False)
        embed.add_field(name="🏦 受取額", value=f"`{int(net_amount):,} pnc`", inline=False)
        await channel.send(embed=embed)