import asyncio
from app import bot, dp
from app.bot import on_startup, on_shutdown

async def main():
    await on_startup()
    await dp.start_polling(bot, on_shutdown=on_shutdown)

if __name__ == "__main__":
    asyncio.run(main())