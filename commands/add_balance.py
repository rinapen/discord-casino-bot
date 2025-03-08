import discord
import re
from discord import app_commands
from database import update_user_balance, get_user_balance, users_collection, log_transaction
from paypay_session import paypay_session
from config import MIN_INITIAL_DEPOSIT
from bot import bot
from decimal import Decimal, ROUND_HALF_UP
from PayPaython_mobile.main import PayPayError

PAYPAY_LINK_REGEX = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"

def create_embed(title, description, color):
    return discord.Embed(title=title, description=description, color=color)

@bot.tree.command(name="add_balance", description="自分の口座に残高を追加")
@app_commands.describe(link="PayPayリンクを入力してください")
async def add_balance(interaction: discord.Interaction, link: str):
    user_id = interaction.user.id
    user_info = users_collection.find_one({"user_id": user_id})

    if not user_info:
        embed = create_embed("", "あなたの口座が見つかりません。\n `/register` で口座を開設してください。", discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not re.match(PAYPAY_LINK_REGEX, link):
        embed = create_embed("", "無効なリンクです。有効な PayPay リンクを入力してください。", discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    try:
        deposit_info = paypay_session.paypay.link_check(link)
        amount = Decimal(deposit_info.amount)
    except PayPayError as e:
        error_code = e.args[0].get("error", {}).get("backendResultCode", "不明")
        
        if error_code == "02100029":
            embed = create_embed("", "このリンクはすでに使用済みです。別のリンクを入力してください。", discord.Color.yellow())
        else:
            embed = create_embed("", f"PayPayリンクの確認中にエラーが発生しました。\nエラーコード: `{error_code}`", discord.Color.red())
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    fee = max((amount * Decimal(0.14)).quantize(Decimal("1"), rounding=ROUND_HALF_UP), Decimal(10))
    net_amount = amount - fee 

    min_required_amount = Decimal(MIN_INITIAL_DEPOSIT) + fee

    if amount < min_required_amount:
        embed = create_embed(
            "",
            f"最低入金額は `{int(min_required_amount):,} pnc` です。",
            discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    paypay_session.paypay.link_receive(link)
    update_user_balance(user_id, int(net_amount))
    
    log_transaction(user_id, "deposit", int(amount), int(fee), int(net_amount))
    embed = discord.Embed(title="💰 入金完了", color=discord.Color.green())
    embed.add_field(name="📥 **入金額**", value=f"`{int(amount):,}pay`", inline=True)
    embed.add_field(name="💸 **手数料**", value=f"`{int(fee):,}pay`", inline=True)
    embed.add_field(name="💰 **現在の残高**", value=f"`{get_user_balance(user_id):,}pnc`", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)