from aiogram.fsm.state import State, StatesGroup

class UserInfo(StatesGroup):
    name = State()
    surname = State()
    phone = State()

class ContentCreation(StatesGroup):
    theme = State()
    edit = State()

class ImageGeneration(StatesGroup):
    description = State()
    edit = State()

class InstagramAuth(StatesGroup):
    username = State()
    password = State()
    verification_code = State()

class InstagramUpload(StatesGroup):
    content_type = State()
    media = State()
    description_choice = State()
    description = State()
    schedule = State()