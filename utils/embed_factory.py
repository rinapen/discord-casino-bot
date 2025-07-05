import discord
from utils.embed import create_embed

class EmbedFactory:
    @staticmethod
    def already_registered():
        return create_embed("登録済みです", "あなたはすでにアカウントを紐づけています。", discord.Color.red())

    @staticmethod
    def registration_prompt(amount: int):
        return create_embed(
            "登録受付け",
            f"### **20秒以内に**{amount}**円のPayPayリンクを送信してください。**",
            discord.Color.orange()
        )

    @staticmethod
    def error(message="予期せぬエラーが発生しました"):
        return create_embed("❌ エラー", message, discord.Color.red())

    @staticmethod
    def success(title="✅ 成功", message="操作が正常に完了しました"):
        return create_embed(title, message, discord.Color.green())

    @staticmethod
    def warning(message="⚠️ 注意が必要です"):
        return create_embed("⚠️ 警告", message, discord.Color.yellow())

    @staticmethod
    def not_registered():
        return create_embed("未登録アカウント", "この操作にはアカウントの登録が必要です。", discord.Color.red())