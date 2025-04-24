import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = "sqlite:///bot.db"
    MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
    GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")