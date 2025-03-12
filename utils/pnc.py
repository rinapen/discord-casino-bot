import datetime
from database.db import users_collection, user_transactions_collection

def get_daily_profit():
    """本日の利益（収益 - 支出）を計算"""
    now = datetime.datetime.now()
    start_of_day = int(datetime.datetime(now.year, now.month, now.day, 0, 0, 0).timestamp() * 1000)
    end_of_day = int(datetime.datetime(now.year, now.month, now.day, 23, 59, 59).timestamp() * 1000)

    transactions = user_transactions_collection.find({
        "timestamp": {"$gte": start_of_day, "$lte": end_of_day}
    })

    total_income = sum(txn["amount"] for txn in transactions if txn["type"] == "in")
    total_expense = sum(txn["amount"] for txn in transactions if txn["type"] == "out")

    return total_income - total_expense 

def get_total_pnc():
    """全ユーザーのPNC合計を取得"""
    total = list(users_collection.aggregate([
        {"$group": {"_id": None, "total_pnc": {"$sum": "$balance"}}}
    ])) 

    return total[0]["total_pnc"] if total else 0

def get_monthly_revenue():
    """過去30日間の総売上（`income` タイプの合計）を取得"""
    today = datetime.datetime.now()
    start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    transactions = user_transactions_collection.find({"timestamp": {"$gte": start_date}})
    total_income = sum(txn["amount"] for txn in transactions if txn["type"] == "income")

    return total_income