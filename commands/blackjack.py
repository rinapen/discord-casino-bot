import discord
import random
from discord import app_commands
from bot import bot
from database.db import get_user_balance, update_user_balance
from utils.embed import create_embed
from utils.logs import send_casino_log
from config import WIN_EMOJI, LOSE_EMOJI, DRAW_EMOJI

BASE_COLOR_CODE = 0x2b2d31
VALID_BETS = [50, 100, 200, 500, 1000]
SUITS = ["S", "C", "D", "H"]

CARD_VALUES = {str(i): i for i in range(2, 11)}
CARD_VALUES.update({"J": 10, "Q": 10, "K": 10, "A": 11})

games = {}

def draw_card():
    """ランダムなカードを引く"""
    rank = random.choice(list(CARD_VALUES.keys()))
    suit = random.choice(SUITS)
    return (rank, suit, CARD_VALUES[rank])

def calculate_hand_value(hand):
    """手札の合計値を計算"""
    value = sum(card[2] for card in hand)
    aces = sum(1 for card in hand if card[0] == "A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

class BlackjackGame:
    def __init__(self, user_id, bet, win_streak, lose_streak):
        self.user_id = user_id
        self.bet = bet
        self.win_streak = win_streak
        self.lose_streak = lose_streak
        self.player_hand = [draw_card(), draw_card()]
        self.dealer_hand = [draw_card(), draw_card()]
        self.finished = False

    def hit(self):
        """プレイヤーがヒットする"""
        if self.finished:
            return None
        self.player_hand.append(draw_card())

        if calculate_hand_value(self.player_hand) > 21:
            self.finished = True  # バースト
            return "bust"
        return self.player_hand

    def dealer_turn(self):
        """ディーラーのターン（高額ベットほど強化）"""
        min_hit_score = 18
        max_stop_score = 20

        # **高額ベットでディーラーの強化**
        if self.bet >= 500:
            min_hit_score = 19
            max_stop_score = 21

        while calculate_hand_value(self.dealer_hand) < min_hit_score:
            self.dealer_hand.append(draw_card())

        # **ディーラーが20 or 21 で止まりやすくする**
        if random.random() < 0.6:
            while calculate_hand_value(self.dealer_hand) < max_stop_score:
                self.dealer_hand.append(draw_card())

    def get_result(self):
        """勝敗判定"""
        player_score = calculate_hand_value(self.player_hand)
        dealer_score = calculate_hand_value(self.dealer_hand)

        if player_score > 21:
            return "bust"
        if dealer_score > 21 or player_score > dealer_score:
            return "win"
        if player_score < dealer_score:
            return "lose"
        return "draw"

@bot.tree.command(name="blackjack", description="ブラックジャックを開始")
@app_commands.describe(amount="ベット額")
@app_commands.choices(amount=[app_commands.Choice(name=f"{b} PNC", value=b) for b in VALID_BETS])
async def blackjack(interaction: discord.Interaction, amount: int):
    user_id = interaction.user.id
    balance = get_user_balance(user_id)
    if balance < amount:
        embed = create_embed("❌ 残高不足", f"現在の残高: `{balance:,} PNC`\nベット額を減らしてください。", discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    win_streak = 0  # 連勝記録
    lose_streak = 0  # 連敗記録

    games[user_id] = BlackjackGame(user_id, amount, win_streak, lose_streak)
    game = games[user_id]

    embed = create_blackjack_embed(game, False, BASE_COLOR_CODE)
    await interaction.response.send_message(embed=embed, view=BlackjackView(user_id))

def create_blackjack_embed(game, reveal_dealer, color, result=None, payout=None, balance=None):
    """ブラックジャックの手札をEmbedで表示"""
    player_hand = " | ".join(f"{card[0]}{card[1]}" for card in game.player_hand)
    dealer_hand = " | ".join(f"{card[0]}{card[1]}" for card in game.dealer_hand) if reveal_dealer else f"{game.dealer_hand[0][0]}{game.dealer_hand[0][1]} ❓"

    embed = discord.Embed(title="ブラックジャック", color=color)
    embed.add_field(name="**ベット額**", value=f"`{game.bet} PNC`", inline=False)
    embed.add_field(name="**プレイヤーの手札**", value=f"{player_hand} （合計: `{calculate_hand_value(game.player_hand)}`）", inline=False)
    embed.add_field(name="**ディーラーの手札**", value=f"{dealer_hand}", inline=False)

    if result:
        embed.add_field(name="**結果**", value=f"`{result}`", inline=False)
        if payout is not None:
            if payout > 0:
                embed.add_field(name="✅ **獲得**", value=f"`{payout} PNC`", inline=False)
            elif payout < 0:
                embed.add_field(name="❌ **損失**", value=f"`{-payout} PNC`", inline=False)

    if balance is not None:
        embed.set_footer(text=f"現在の残高: {balance} PNC")

    return embed

class BlackjackView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="1枚引く", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        game = games.get(user_id)
        if game is None:
            return
        
        if game.hit() == "bust":
            update_user_balance(user_id, -game.bet)
            balance = get_user_balance(user_id)
            await interaction.message.edit(embed=create_blackjack_embed(game, True, discord.Color.red(), result="bust", payout=-game.bet, balance=balance), view=None)
        else:
            await interaction.message.edit(embed=create_blackjack_embed(game, False, BASE_COLOR_CODE))

    @discord.ui.button(label="決定", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user_id = interaction.user.id
        game = games.get(user_id)
        if game is None:
            return

        game.dealer_turn()
        game.finished = True
        result = game.get_result()

        payout = game.bet * (2 if result == "win" else -1)
        update_user_balance(user_id, payout)
        balance = get_user_balance(user_id)

        await interaction.message.edit(embed=create_blackjack_embed(game, True, discord.Color.green() if payout > 0 else discord.Color.red(), result=result, payout=payout, balance=balance), view=None)
