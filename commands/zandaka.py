import discord
from discord import app_commands
from database import get_user_balance, users_collection, user_transactions_collection
from bot import bot
from utils import create_embed

@bot.tree.command(name="zandaka", description="口座残高を表示")
async def zandaka(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_info = users_collection.find_one({"user_id": user_id})

    if not user_info:
        embed = create_embed("", "あなたの口座は登録されていません。\n `/kouza` で口座を開設してください。", discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    balance = get_user_balance(user_id)

    embed = discord.Embed(title="口座残高", description=f"# {balance:,}PNC",color=discord.Color.green())

    transactions = list(user_transactions_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(5))

    if transactions:
        history_text = ""
        for txn in transactions:
            type_emoji = "📥" if txn["type"] == "in" else "📤" if txn["type"] == "out" else "🔄"
            history_text += f"{type_emoji} `{txn['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}` - `{txn['type'].capitalize()}`: `{txn['amount']:,} pnc`\n"
        embed.add_field(name="**直近の取引履歴**", value=history_text, inline=False)
    else:
        embed.add_field(name="**直近の取引履歴**", value="取引履歴がありません。", inline=False)

    embed.set_footer(text=f"{interaction.user.display_name}様 | ID: {interaction.user.name}")

    await interaction.response.send_message(embed=embed, ephemeral=True)