from . import setup

async def on_startup():
    print("Bot is starting...")
    setup()

async def on_shutdown():
    print("Bot is shutting down...")