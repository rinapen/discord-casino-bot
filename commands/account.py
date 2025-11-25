from decimal import Decimal

import discord

from config import MIN_INITIAL_DEPOSIT
from database.db import (
    update_user_balance,
    get_user_balance,
    register_user,
    users_collection,
    active_users_collection,
)
from utils.embed import create_embed
from utils.emojis import PNC_EMOJI_STR
from utils.pnc import jpy_to_pnc
from utils.embed_factory import EmbedFactory
from utils.logs import log_transaction


class AccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RegisterButton())
        self.add_item(PayinButton())

class RegisterButton(discord.ui.Button):
    """登録ボタン"""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="登録")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if users_collection.find_one({"user_id": user_id}):
            await interaction.response.send_message(
                embed=create_embed("登録済みです", "あなたはすでにアカウントを登録しています。", discord.Color.red()),
                ephemeral=True
            )
            return

        sender_id = f"user_{user_id}"
        existing = users_collection.find_one({"user_id": user_id})

        if existing:
            await interaction.response.send_message(
                embed=create_embed("登録済みです", "あなたはすでにアカウントを登録しています。", discord.Color.red()),
                ephemeral=True
            )
            return

        active_data = active_users_collection.find_one({"user_id": user_id})
        restored_balance = int(active_data["balance"]) if active_data and "balance" in active_data else 0

        register_user(user_id, sender_id)
        update_user_balance(user_id, restored_balance)

        await interaction.response.send_message(
            embed=create_embed("[✓] 登録完了", "登録が正常に完了しました。", discord.Color.green()),
            ephemeral=True
        )


class PayinButton(discord.ui.Button):
    """入金ボタン"""
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="入金")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PayinModal())


class PayinModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="入金")
        
        self.amount_input = discord.ui.TextInput(
            label="入金額（円）",
            placeholder="例: 1000",
            required=True,
            max_length=10
        )
        self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        await interaction.response.defer(ephemeral=True)

        user_info = users_collection.find_one({"user_id": user_id})
        if not user_info:
            embed = EmbedFactory.require_registration_prompt()
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            jpy_amount = Decimal(self.amount_input.value.strip())
            
            if jpy_amount <= 0:
                embed = create_embed("", "入金額は正の数値を入力してください。", discord.Color.red())
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
        except (ValueError, AttributeError):
            embed = create_embed("", "有効な数値を入力してください。（例: 1000）", discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        total_pnc = jpy_to_pnc(jpy_amount)
        net_pnc = total_pnc

        gross_min_jpy = Decimal(MIN_INITIAL_DEPOSIT) / Decimal(10)
        if jpy_amount < gross_min_jpy:
            shortfall = gross_min_jpy - jpy_amount
            shortfall_pnc = jpy_to_pnc(shortfall)

            embed = create_embed(
                "",
                f"最低入金PNC: `{int(MIN_INITIAL_DEPOSIT):,}`（約 ¥{int(gross_min_jpy):,}）が必要です。\n"
                f"不足分: 約 ¥{int(shortfall):,} ≒ {PNC_EMOJI_STR}`{int(shortfall_pnc)}`",
                discord.Color.yellow()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        update_user_balance(user_id, int(net_pnc))
        log_transaction(user_id=user_id, type="payin", amount=int(jpy_amount), payout=int(net_pnc))

        embed = discord.Embed(title="[✓] 入金完了", color=discord.Color.green())
        embed.add_field(name="入金額", value=f"`¥{int(jpy_amount):,}` → {PNC_EMOJI_STR} `{int(total_pnc):,}`", inline=True)
        embed.add_field(name="現在の残高", value=f"{PNC_EMOJI_STR}`{get_user_balance(user_id):,}`", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)
