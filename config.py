import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "paypay_bot")
TOKENS_COLLECTION = os.getenv("TOKENS_COLLECTION", "tokens")
USERS_COLLECTION = os.getenv("USERS_COLLECTION", "users")
TRANSACTIONS_COLLECTION = os.getenv("TRANSACTIONS_COLLECTION", "transactions")

MIN_INITIAL_DEPOSIT = 100  # 初期入金の最低金額
TAX_RATE = 0.1  # 10% の税金
FEE_RATE = 0.05  # 5% の手数料

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PAYPAY_PHONE = os.getenv("PAYPAY_PHONE")
PAYPAY_PASSWORD = os.getenv("PAYPAY_PASSWORD")