import discord
from discord import app_commands
from database import get_user_balance, users_collection
from bot import bot 

def create_embed(title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="ご利用ありがとうございます！")
    return embed

@bot.tree.command(name="balance", description="現在の残高を表示")
async def balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_info = users_collection.find_one({"user_id": user_id})

    if not user_info:
        embed = create_embed("", "あなたの口座は登録されていません。\n `/register` で口座を開設してください。", discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    balance = get_user_balance(user_id)

    embed = discord.Embed(title="💰 現在の残高", color=discord.Color.green())
    embed.add_field(name="💵 **残高**", value=f"`{balance:,}pnc`", inline=False)
    embed.set_footer(text=f"{interaction.user.display_name}様")

    await interaction.response.send_message(embed=embed, ephemeral=True)