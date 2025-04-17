from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Create Content"), KeyboardButton(text="Generate Image")],
            [KeyboardButton(text="Upload Instagram"), KeyboardButton(text="Saved Contents")],
            [KeyboardButton(text='Back')]
        ],
        resize_keyboard=True
    )

def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share Phone Number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def content_options():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Save", callback_data="save_content"),
         InlineKeyboardButton(text="Don't Save", callback_data="dont_save_content"),
         InlineKeyboardButton(text="Edit", callback_data="edit_content")]
    ])

def image_options():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Save", callback_data="save_image"),
         InlineKeyboardButton(text="Don't Save", callback_data="dont_save_image"),
         InlineKeyboardButton(text="Edit", callback_data="edit_image")]
    ])

def instagram_submenu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="back_to_main"),
         InlineKeyboardButton(text="Check", callback_data="check_scheduled"),
         InlineKeyboardButton(text="Upload", callback_data="upload_ig"),
         InlineKeyboardButton(text="Log out", callback_data="log_out")],
    ])

def upload_type():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Reels", callback_data="reels"),
         InlineKeyboardButton(text="Post", callback_data="post"),
         InlineKeyboardButton(text="Story", callback_data="story")], 
        [InlineKeyboardButton(text="Back", callback_data="back_to_ig")]
    ])

def yes_no():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yes", callback_data="yes"),
         InlineKeyboardButton(text="No", callback_data="no")]
    ])

def saved_contents_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Content", callback_data="view_content"),
         InlineKeyboardButton(text="Images", callback_data="view_images")]
    ])

def remove_keyboard():
    return ReplyKeyboardRemove()

def back_to_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Back"),]
        ],
        resize_keyboard=True
    )

def language_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 Uzbek", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Russian", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        ]
    ])
    return keyboard

def menu_keyboard(lang="en"):
    buttons = {
        "en": ["🛠 Settings", "💼 Services", "📥 Subscription", "🤖 Tech. support"],
        "uz": ["🛠 Sozlamalar", "💼 Xizmatlar", "📥 Obuna", "🤖 Tex. yordam"],
        "ru": ["🛠 Настройки", "💼 Услуги", "📥 Подписка", "🤖 Тех. поддержка"],
    }
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[lang][0], callback_data="menu_settings"),
            InlineKeyboardButton(text=buttons[lang][1], callback_data="menu_services"),
        ],
        [
            InlineKeyboardButton(text=buttons[lang][2], callback_data="menu_subscription"),
            InlineKeyboardButton(text=buttons[lang][3], callback_data="menu_tech_support"),
        ]
    ])
    return keyboard


def settings_keyboard(lang="en"):
    buttons = {
        "en": ["🌐 Change language", "💳 Balance settings", "🔙 Back"],
        "uz": ["🌐 Tilni o'zgartirish", "💳 Balans sozlamalari", "🔙 Orqaga"],
        "ru": ["🌐 Сменить язык", "💳 Настройки баланса", "🔙 Назад"],
    }
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[lang][0], callback_data="settings_change_language"),
            InlineKeyboardButton(text=buttons[lang][1], callback_data="settings_balance"),
        ],
        [
            InlineKeyboardButton(text=buttons[lang][2], callback_data="settings_back"),
        ]
    ])
    return keyboard

def balance_keyboard(lang="en"):
    buttons = {
        "en": ["💳 Pay", "🔙 Back"],
        "uz": ["💳 To'lov", "🔙 Orqaga"],
        "ru": ["💳 Оплатить", "🔙 Назад"],
    }
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[lang][0], callback_data="balance_pay"),
            InlineKeyboardButton(text=buttons[lang][1], callback_data="balance_back"),
        ]
    ])
    return keyboard

def subscription_keyboard(lang="en"):
    buttons = {
        "en": ["💳 Pay", "🔙 Back"],
        "uz": ["💳 To'lov", "🔙 Orqaga"],
        "ru": ["💳 Оплатить", "🔙 Назад"],
    }
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[lang][0], callback_data="subscription_pay"),
            InlineKeyboardButton(text=buttons[lang][1], callback_data="subscription_back"),
        ]
    ])
    return keyboard

def feedback_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Like", callback_data="feedback_like"),
            InlineKeyboardButton(text="👎 Dislike", callback_data="feedback_dislike"),
            InlineKeyboardButton(text="😐 Neutral", callback_data="feedback_neutral"),
        ]
    ])
    return keyboard