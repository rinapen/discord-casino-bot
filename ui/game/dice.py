import discord
from discord import File
import random
import asyncio

from database.db import update_user_balance
from utils.emojis import DICE_EMOJI, PNC_EMOJI_STR, WIN_EMOJI   
from utils.embed import create_embed
from utils.logs import send_casino_log
from utils.color import BASE_COLOR_CODE
from config import DICE_FOLDER, CURRENCY_NAME

ongoing_games = {}
class ContinueButton(discord.ui.View):
    def __init__(self, user_id, bet_amount, point):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.point = point

    @discord.ui.button(emoji=DICE_EMOJI, style=discord.ButtonStyle.success)
    async def continue_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("あなたのゲームではありません。", ephemeral=True)
            return

        def roll():
            return random.randint(1, 6), random.randint(1, 6)

        die1, die2 = roll()
        total = die1 + die2

        gif_path1 = f"{DICE_FOLDER}/gif/{die1}.gif"
        gif_path2 = f"{DICE_FOLDER}/gif/{die2}.gif"
        gif_files = [File(gif_path1, filename="dice1.gif"), File(gif_path2, filename="dice2.gif")]

        rolling_embed = create_embed(f"{CURRENCY_NAME}ダイス 続行", f"### 目標ポイント[**{self.point}**]\nサイコロを振っています...", BASE_COLOR_CODE)
        rolling_embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.display_avatar.url
        )
        rolling_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1219916908485283880/1389815902278647818/ChatGPT_Image_202572_12_51_52.png")
        await interaction.response.edit_message(embed=rolling_embed, attachments=gif_files, view=None)

        await asyncio.sleep(1.5)

        result_path1 = f"{DICE_FOLDER}/png/{die1}.png"
        result_path2 = f"{DICE_FOLDER}/png/{die2}.png"
        result_files = [File(result_path1, filename="die1.png"), File(result_path2, filename="die2.png")]

        embed_color = discord.Color.from_str("#26ffd4")
        description = f"### 目標ポイント[**{self.point}**]\n# {die1} + {die2} = **{total}**"
        result_text = ""
        next_view = None

        if total == self.point:
            winnings = self.bet_amount * 2
            update_user_balance(self.user_id, winnings)
            result_text = f"\n\n### {PNC_EMOJI_STR}`{winnings}` **WIN**"

            await send_casino_log(
                interaction=interaction,
                winorlose="WIN",
                emoji=WIN_EMOJI,
                price=winnings - self.bet_amount,
                description="",
                color=discord.Color.from_str("#26ffd4")
            )

            ongoing_games.pop(self.user_id, None)

        elif total == 7:
            embed_color = discord.Color.red()
            result_text = f"\n\n7が出て敗北しました。\n### {PNC_EMOJI_STR}`{self.bet_amount}` **LOSE**"
            ongoing_games.pop(self.user_id, None)

        else:
            result_text = "\n\n### まだ勝負はついていません。\nもう一度ボタンを押して続けてください。"
            next_view = ContinueButton(self.user_id, self.bet_amount, self.point)

        final_embed = create_embed(f"{CURRENCY_NAME}ダイス 継続結果", description + result_text, embed_color)
        final_embed.set_author(
            name=interaction.user.name,
            icon_url=interaction.user.display_avatar.url
        )
        final_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1219916908485283880/1389815902278647818/ChatGPT_Image_202572_12_51_52.png")
        await interaction.edit_original_response(embed=final_embed, attachments=result_files, view=next_view)