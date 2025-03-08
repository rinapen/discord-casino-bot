import discord
import re
from discord import app_commands
from bot import bot
from database import register_user, update_user_balance, users_collection, log_transaction
from paypay_session import paypay_session
from config import MIN_INITIAL_DEPOSIT
from decimal import Decimal, ROUND_HALF_UP
from PayPaython_mobile.main import PayPayError 

PAYPAY_LINK_REGEX = r"^https://pay\.paypay\.ne\.jp/[a-zA-Z0-9]+$"

def create_embed(title, description, color):
    return discord.Embed(title=title, description=description, color=color)

class RegisterModal(discord.ui.Modal, title="🏦 口座開設"):
    def __init__(self):
        super().__init__()
        self.email = discord.ui.TextInput(label="📧 メールアドレス", placeholder="example@mail.com")
        self.password = discord.ui.TextInput(label="🔑 パスワード", placeholder="パスワード", style=discord.TextStyle.short)
        self.deposit_link = discord.ui.TextInput(label="💰 入金リンク（最低 116 pay 必須）", placeholder="PayPay送金リンクを入力")
        self.add_item(self.email)
        self.add_item(self.password)
        self.add_item(self.deposit_link)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        await interaction.response.defer(ephemeral=True)

        if users_collection.find_one({"user_id": user_id}):
            embed = create_embed("", "あなたはすでに口座を開設しています。", discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        if not re.match(PAYPAY_LINK_REGEX, self.deposit_link.value):
            embed = create_embed("", "無効なリンクです。有効な PayPay リンクを入力してください。", discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            deposit_info = paypay_session.paypay.link_check(self.deposit_link.value)
            amount = Decimal(deposit_info.amount)
        except PayPayError as e:
            error_code = e.args[0].get("error", {}).get("backendResultCode", "不明")

            if error_code == "02100029":
                embed = create_embed("", "このリンクはすでに使用済みです。別のリンクを入力してください。", discord.Color.yellow())
            else:
                embed = create_embed("", f"PayPayリンクの確認中にエラーが発生しました。\nエラーコード: `{error_code}`", discord.Color.red())

            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        fee = max((amount * Decimal(0.14)).quantize(Decimal("1"), rounding=ROUND_HALF_UP), Decimal(10))
        net_amount = amount - fee  # **受取額 = 入金額 - 手数料**

        min_required_amount = Decimal(MIN_INITIAL_DEPOSIT) + fee

        if amount < min_required_amount:
            embed = create_embed(
                "",
                f"初期入金額が不足しています。最低 `{int(min_required_amount):,}pnc` が必要です。",
                discord.Color.yellow()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        paypay_session.paypay.link_receive(self.deposit_link.value)

        register_user(user_id, self.email.value, self.password.value, deposit_info.sender_external_id)

        update_user_balance(user_id, int(net_amount))

        log_transaction(user_id, "deposit", int(amount), int(fee), int(net_amount))

        embed = discord.Embed(title="🏦 口座開設完了", color=discord.Color.green())
        embed.add_field(name="📥 **入金額**", value=f"`{int(amount):,}pnc`", inline=True)
        embed.add_field(name="💸 **手数料**", value=f"`{int(fee):,}pnc`", inline=True)
        embed.add_field(name="💰 **初期残高**", value=f"`{int(net_amount):,}pnc`", inline=False)
        embed.set_footer(text="口座を開設しました。")

        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="register", description="口座を開設")
async def register(interaction: discord.Interaction):
    modal = RegisterModal()
    await interaction.response.send_modal(modal)