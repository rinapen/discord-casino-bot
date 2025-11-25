import datetime
from datetime import timedelta
from typing import Optional, Any

import pymongo
from pymongo.collection import Collection
from pymongo.database import Database

import config

_client: Optional[pymongo.MongoClient] = None
_db: Optional[Database] = None


def get_client() -> pymongo.MongoClient:
    global _client
    if _client is None:
        _client = pymongo.MongoClient(config.MONGO_URI)
    return _client


def get_database() -> Database:
    global _db
    if _db is None:
        _db = get_client()[config.DB_NAME]
    return _db

def get_collection(collection_name: str) -> Collection:
    return get_database()[collection_name]

tokens_collection = get_collection(config.TOKENS_COLLECTION)
blacklist_collection = get_collection(config.BLACKLIST_COLLECTION)
financial_transactions_collection = get_collection(config.FINANCIAL_TRANSACTIONS_COLLECTION)
casino_transactions_collection = get_collection(config.CASINO_TRANSACTION_COLLECTION)
users_collection = get_collection(config.USERS_COLLECTION)
casino_stats_collection = get_collection(config.CASINO_STATS_COLLECTION)
models_collection = get_collection(config.MODELS_COLLECTION)
bet_history_collection = get_collection(config.BET_HISTORY_COLLECTION)
bot_state_collection = get_collection(config.BOT_STATE_COLLECTION)

payin_settings_collection = get_collection("payin_settings")
invited_users_collection = get_collection("invited_users")
invites_collection = get_collection("invites")
invite_redeem_collection = get_collection("invite_redeem")
active_users_collection = get_collection("active_users")
pf_collection = get_collection("pf_params")
casino_tables_collection = get_collection("casino_tables")
prize_pockets_collection = get_collection("prize_pockets")
carry_over_points_collection = get_collection("carry_over_points")
accounts_collection = get_collection("accounts")
exchanged_accounts_collection = get_collection("exchanged_accounts")

def load_pf_params(user_id: int) -> tuple[Optional[str], int]:
    doc = pf_collection.find_one({"user_id": user_id})
    if doc:
        return doc.get("client_seed"), doc.get("nonce", 0)
    return None, 0


def save_pf_params(user_id: int, client_seed: str, server_seed: str, nonce: int) -> None:
    pf_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "client_seed": client_seed,
                "server_seed": server_seed,
                "nonce": nonce
            }
        },
        upsert=True
    )

def get_user_balance(user_id: int) -> Optional[int]:
    """残高を取得"""
    user = users_collection.find_one({"user_id": user_id})
    return user["balance"] if user else None


def update_user_balance(user_id: int, amount: int) -> None:
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

def get_user_streaks(user_id: int, game_type: str) -> tuple[int, int]:
    """ゲームタイプごとのユーザーの連勝・連敗記録を取得"""
    user = users_collection.find_one({"user_id": user_id}, {"streaks": 1})
    
    if not user or "streaks" not in user:
        return 0, 0

    game_streaks = user.get("streaks", {}).get(game_type, {})
    return game_streaks.get("win_streak", 0), game_streaks.get("lose_streak", 0)

def register_user(user_id: int, sender_external_id: str) -> None:
    """新規ユーザーを登録"""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "sender_external_id": sender_external_id,
            "balance": 0
        }},
        upsert=True
    )

def get_user_transactions(
    user_id: int,
    game_type: Optional[str] = None,
    days: Optional[int] = None
) -> list[dict[str, Any]]:
    doc = financial_transactions_collection.find_one({"user_id": user_id})

    if not doc or "transactions" not in doc:
        return []

    transactions = doc["transactions"]

    if game_type:
        transactions = [t for t in transactions if t.get("type") == game_type]

    if days:
        threshold = datetime.datetime.now() - timedelta(days=days)
        transactions = [t for t in transactions if t.get("timestamp") and t["timestamp"] >= threshold]

    return transactions

async def save_account_panel_message_id(message_id: int) -> None:
    bot_state_collection.update_one(
        {"_id": "account_panel"},
        {"$set": {"message_id": message_id}},
        upsert=True
    )


async def get_account_panel_message_id() -> Optional[int]:
    doc = bot_state_collection.find_one({"_id": "account_panel"})
    return doc["message_id"] if doc and "message_id" in doc else None

def get_all_user_balances() -> list[tuple[int, int]]:
    """全ユーザーのuser_idと残高を取得する"""
    cursor = users_collection.find({}, {"user_id": 1, "balance": 1})
    return [(doc["user_id"], doc.get("balance", 0)) for doc in cursor]

# カジノテーブル
def save_casino_table(
    channel_id: int,
    category_id: int,
    table_number: int,
    channel_name: str,
    category_name: str
) -> None:
    casino_tables_collection.insert_one({
        "channel_id": channel_id,
        "category_id": category_id,
        "table_number": table_number,
        "channel_name": channel_name,
        "category_name": category_name,
        "created_at": datetime.datetime.now()
    })


def get_all_casino_tables() -> list[dict[str, Any]]:
    return list[dict[str, Any]](casino_tables_collection.find({}))


def delete_casino_table(channel_id: int) -> None:
    casino_tables_collection.delete_one({"channel_id": channel_id})


def clear_all_casino_tables() -> int:
    result = casino_tables_collection.delete_many({})
    return result.deleted_count


def get_casino_table_count() -> int:
    return casino_tables_collection.count_documents({})