import discord
import random

from database.db import update_user_balance
from utils.emojis import PNC_EMOJI_STR, WIN_EMOJI
from utils.logs import send_casino_log
from config import FRONT_IMG, BACK_IMG, THUMBNAIL_URL

class CoinFlipView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet
        self.add_item(CoinFlipButton("表", user, bet))
        self.add_item(CoinFlipButton("裏", user, bet))

class CoinFlipButton(discord.ui.Button):
    def __init__(self, label, user, bet):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.label = label
        self.user = user
        self.bet = bet

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            embed = discord.Embed(
                description="❌ あなたのゲームじゃないヨ！",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        win = random.random() < 0.5
        outcome = self.label if win else ("表" if self.label == "裏" else "裏")
        win = (outcome == self.label)

        embed = discord.Embed(
            title="PNCフリップ",
            description=(
                f"あなたの選択: **{self.label}**\n"
                f"結果: **{outcome}**\n"
                f"### {PNC_EMOJI_STR}`{self.bet}` {'**WIN**' if win else '**LOSE**'}"
            ),
            color=discord.Color.from_str("#26ffd4") if win else discord.Color.from_str("#ff3d74")
        )
        embed.set_author(name=f"{self.user.name}", icon_url=self.user.display_avatar.url)
        embed.set_thumbnail(url=THUMBNAIL_URL)
        embed.set_image(url=FRONT_IMG if outcome == "表" else BACK_IMG)

        if win:
            update_user_balance(self.user.id, self.bet)
            try:
                await send_casino_log(
                    interaction,
                    winorlose="WIN",
                    emoji=WIN_EMOJI,
                    price=self.bet * 2,
                    description="",
                    color=discord.Color.from_str("#26ffd4"),
                )
            except Exception as e:
                print(f"[ERROR] send_casino_log failed: {e}")
        else:
            update_user_balance(self.user.id, -self.bet)

        self.view.clear_items()
        await interaction.response.edit_message(embed=embed, view=self.view)