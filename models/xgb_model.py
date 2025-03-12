import xgboost as xgb
import numpy as np
from database.db import models_collection

def save_model_to_mongodb(model):
    """XGBoostモデルをMongoDBに保存"""
    if not hasattr(model, "booster_"):
        X_dummy = np.random.rand(10, 3)
        y_dummy = np.random.randint(2, size=10)
        model.fit(X_dummy, y_dummy)

    booster = model.get_booster()
    model_json = booster.save_raw("json")
    models_collection.update_one(
        {"name": "casino_winrate_model"},
        {"$set": {"model_data": model_json.decode()}},
        upsert=True
    )

def load_model_from_mongodb():
    """MongoDBからXGBoostモデルをロード"""
    model_data = models_collection.find_one({"name": "casino_winrate_model"})
    if not model_data:
        print("⚠ モデルがMongoDBに存在しません")
        return None

    model = xgb.Booster()
    model.load_model(bytearray(model_data["model_data"], "utf-8"))
    print("✅ XGBoostモデルをロードしました")
    return model