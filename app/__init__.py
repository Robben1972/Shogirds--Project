from aiogram import Bot, Dispatcher
from config import Config
from .utils.db import init_db
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def setup():
    init_db()
    from .handlers import start, content, image, instagram, saved, bio, scenario, stories
    dp.include_routers(
        start.router,
        content.router,
        image.router,
        instagram.router,
        saved.router,
        bio.router,
        scenario.router,
        stories.router
    )

__all__ = ['bot', 'dp', 'setup']