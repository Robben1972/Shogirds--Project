from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import json
import os

# Load the buttons.json file
with open(os.path.join('lang', 'buttons.json'), 'r', encoding='utf-8') as f:
    button_data = json.load(f)

def main_menu(lang="en"):
    buttons = button_data["services"][lang]  # Use services buttons for main menu
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=buttons[0]), KeyboardButton(text=buttons[1])],  # Content plan, Generate images
            [KeyboardButton(text=buttons[2]), KeyboardButton(text=buttons[3])],  # Story+Reels+Post, Write stories
            [KeyboardButton(text=buttons[4]), KeyboardButton(text=buttons[5])],  # Write script, Write bio
            [KeyboardButton(text=buttons[6])]  # Back
        ],
        resize_keyboard=True
    )

def contact_keyboard(lang="en"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_data["acceptence"][lang][0], request_contact=True)]],  # Use "Accept" for sharing phone number
        resize_keyboard=True,
        one_time_keyboard=True
    )

def content_options(lang="en"):
    buttons = button_data["acceptence"][lang]  # Use "Accept" and "Cancel" for Save/Don't Save
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="save_content"),  # Save
            InlineKeyboardButton(text=buttons[1], callback_data="dont_save_content"),  # Don't Save
            InlineKeyboardButton(text=button_data["back"][lang][0].replace("🔙 ", ""), callback_data="edit_content")  # Edit (remove emoji for consistency)
        ]
    ])

def image_options(lang="en"):
    buttons = button_data["acceptence"][lang]  # Use "Accept" and "Cancel" for Save/Don't Save
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="save_image"),  # Save
            InlineKeyboardButton(text=buttons[1], callback_data="dont_save_image"),  # Don't Save
            InlineKeyboardButton(text=button_data["back"][lang][0].replace("🔙 ", ""), callback_data="edit_image")  # Edit (remove emoji for consistency)
        ]
    ])

def instagram_submenu(lang="en"):
    buttons = button_data["back"][lang] + button_data["acceptence"][lang]  # Back, Accept, Cancel
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="back_to_main"),  # Back
            InlineKeyboardButton(text=buttons[1].replace("✅ ", "🔍 "), callback_data="check_scheduled"),  # Check (replace emoji)
            InlineKeyboardButton(text=buttons[1].replace("✅ ", "📤 "), callback_data="upload_ig"),  # Upload (replace emoji)
            InlineKeyboardButton(text=buttons[2].replace("❌ ", "🚪 "), callback_data="log_out")  # Log out (replace emoji)
        ]
    ])

def upload_type(lang="en"):
    buttons = button_data["back"][lang]  # Back
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Reels", callback_data="reels"),  # Static for now; can be added to JSON if needed
            InlineKeyboardButton(text="Post", callback_data="post"),
            InlineKeyboardButton(text="Story", callback_data="story")
        ],
        [
            InlineKeyboardButton(text=buttons[0], callback_data="back_to_ig")  # Back
        ]
    ])

def yes_no(lang="en"):
    buttons = button_data["acceptence"][lang]  # Use "Accept" and "Cancel" for Yes/No
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="yes"),  # Yes
            InlineKeyboardButton(text=buttons[1], callback_data="no")  # No
        ]
    ])

def saved_contents_menu(lang="en"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Content", callback_data="view_content"),  # Static for now; can be added to JSON if needed
            InlineKeyboardButton(text="Images", callback_data="view_images")
        ]
    ])

def remove_keyboard():
    return ReplyKeyboardRemove()

def back_to_main_menu(lang="en"):
    buttons = button_data["back"][lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=buttons[0])]
        ],
        resize_keyboard=True
    )

def language_keyboard(lang="en"):
    buttons = button_data["lang"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons["uz"][0], callback_data="lang_uz"),
            InlineKeyboardButton(text=buttons["ru"][0], callback_data="lang_ru"),
            InlineKeyboardButton(text=buttons["en"][0], callback_data="lang_en"),
        ]
    ])
    return keyboard

def menu_keyboard(lang="en"):
    buttons = button_data["greetings"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="menu_settings"),
            InlineKeyboardButton(text=buttons[1], callback_data="menu_services"),
        ],
        [
            InlineKeyboardButton(text=buttons[2], callback_data="menu_subscription"),
            InlineKeyboardButton(text=buttons[3], callback_data="menu_tech_support"),
        ]
    ])
    return keyboard

def settings_keyboard(lang="en"):
    buttons = button_data["settings"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="settings_change_language"),
            InlineKeyboardButton(text=buttons[1], callback_data="settings_balance"),
        ],
        [
            InlineKeyboardButton(text=buttons[2], callback_data="settings_back"),
        ]
    ])
    return keyboard

def balance_keyboard(lang="en"):
    buttons = button_data["subscription"][lang]  # Using subscription buttons for Pay/Back
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="balance_pay"),
            InlineKeyboardButton(text=buttons[1], callback_data="balance_back"),
        ]
    ])
    return keyboard

def subscription_keyboard(lang="en"):
    buttons = button_data["subscription"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="subscription_pay"),
            InlineKeyboardButton(text=buttons[1], callback_data="subscription_back"),
        ]
    ])
    return keyboard

def feedback_keyboard(lang="en"):
    buttons = button_data["feedback"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=buttons[0], callback_data="feedback_like"),
            InlineKeyboardButton(text=buttons[1], callback_data="feedback_neutral"),
            InlineKeyboardButton(text=buttons[2], callback_data="feedback_dislike"),
        ]
    ])
    return keyboard