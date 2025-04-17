from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..states.states import UserInfo, TechSupport
from ..utils.db import get_session
from ..models.models import User
from ..keyboards.keyboards import main_menu, contact_keyboard, remove_keyboard, language_keyboard, menu_keyboard, settings_keyboard, balance_keyboard, subscription_keyboard
import os

# Load admin ID from environment
ADMIN_ID = int(os.getenv("ADMIN"))

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    
    if not user:
        await message.answer(
            "Hello! Please choose your language:",
            reply_markup=language_keyboard()
        )
        await state.set_state(UserInfo.language)
    else:
        await message.answer(f"Welcome back, {user.full_name}!", reply_markup=menu_keyboard(lang=user.lang))
    session.close()

@router.callback_query(F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    current_state = await state.get_state()
    
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    
    if current_state == UserInfo.language.state:
        # New user: Proceed to gather info
        await state.update_data(lang=lang)
        await callback.message.edit_text("Language selected! Let's get started by gathering some information about you.")
        await callback.message.answer("What is your name?", reply_markup=remove_keyboard())
        await state.set_state(UserInfo.name)
    else:
        # Existing user: Update language and return to settings
        if user:
            user.lang = lang
            session.commit()
            await callback.message.edit_text("Language updated!", reply_markup=settings_keyboard(lang=lang))
        else:
            await callback.message.edit_text("User not found. Please restart the bot with /start.")
    
    session.close()

@router.message(UserInfo.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("What is your surname?", reply_markup=remove_keyboard())
    await state.set_state(UserInfo.surname)

@router.message(UserInfo.surname)
async def process_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer("Please share your phone number by pressing the button below:", reply_markup=contact_keyboard())
    await state.set_state(UserInfo.phone)

@router.message(UserInfo.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = f"{data['name']} {data['surname']}"
    phone_number = message.contact.phone_number
    lang = data.get("lang", "en")
    
    session = get_session()
    user = User(
        user_id=message.from_user.id,
        full_name=full_name,
        phone_number=phone_number,
        lang=lang,
        balance=0.0
    )
    session.add(user)
    session.commit()
    session.close()
    
    await message.answer("Information saved! Here's the menu:", reply_markup=menu_keyboard(lang=lang))
    await state.clear()

@router.callback_query(F.data == "menu_services")
async def show_services(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.answer("Here are the services:", reply_markup=main_menu())
    await callback.message.delete()

@router.callback_query(F.data == "menu_settings")
async def show_settings(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text("Settings:", reply_markup=settings_keyboard(lang=user.lang))

@router.callback_query(F.data == "menu_subscription")
async def show_subscription(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    messages = {
        "en": "Subscription Plans:\n1 Month: $5\n3 Months: $12",
        "uz": "Obuna Rejalari:\n1 Oy: $5\n3 Oy: $12",
        "ru": "Планы подписки:\n1 месяц: $5\n3 месяца: $12",
    }
    await callback.message.edit_text(messages[user.lang], reply_markup=subscription_keyboard(lang=user.lang))

@router.callback_query(F.data == "subscription_back")
async def subscription_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(f"Welcome back, {user.full_name}!", reply_markup=menu_keyboard(lang=user.lang))

@router.callback_query(F.data == "menu_tech_support")
async def show_tech_support(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    messages = {
        "en": "Please write your message for tech support:",
        "uz": "Iltimos, texnik yordam uchun xabaringizni yozing:",
        "ru": "Пожалуйста, напишите ваше сообщение для техподдержки:",
    }
    await callback.message.edit_text(messages[user.lang])
    await state.set_state(TechSupport.message)
    await state.update_data(user_id=callback.from_user.id, user_lang=user.lang)

@router.message(TechSupport.message)
async def process_tech_support_message(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    
    # Forward the message to the admin
    admin_message = f"Support request from {user.full_name} (ID: {user.user_id}):\n{message.text}"
    forwarded_message = await message.forward(ADMIN_ID)
    await message.bot.send_message(
        ADMIN_ID,
        "Reply to this message to respond to the user.",
        reply_to_message_id=forwarded_message.message_id
    )
    
    messages = {
        "en": "Your message has been sent to tech support. We'll get back to you soon!",
        "uz": "Xabaringiz texnik yordamga yuborildi. Tez orada sizga javob beramiz!",
        "ru": "Ваше сообщение отправлено в техподдержку. Мы скоро с вами свяжемся!",
    }
    await message.answer(messages[user.lang], reply_markup=menu_keyboard(lang=user.lang))
    await state.clear()

@router.message(F.reply_to_message, F.from_user.id == ADMIN_ID)
async def handle_admin_reply(message: Message):
    # Check if the replied message is a forwarded support request
    if message.reply_to_message.forward_from:
        user_id = message.reply_to_message.forward_from.id
        session = get_session()
        user = session.query(User).filter_by(user_id=user_id).first()
        session.close()
        
        if user:
            messages = {
                "en": "Tech Support Reply:\n",
                "uz": "Texnik Yordam Javobi:\n",
                "ru": "Ответ техподдержки:\n",
            }
            await message.bot.send_message(
                user_id,
                f"{messages[user.lang]}{message.text}",
                reply_markup=menu_keyboard(lang=user.lang)
            )
            await message.reply("Reply sent to the user.")

@router.callback_query(F.data == "settings_change_language")
async def change_language(callback: CallbackQuery):
    await callback.message.edit_text("Please choose your language:", reply_markup=language_keyboard())

@router.callback_query(F.data == "settings_balance")
async def show_balance(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(f"Your balance: {user.balance}", reply_markup=balance_keyboard(lang=user.lang))

@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(f"Welcome back, {user.full_name}!", reply_markup=menu_keyboard(lang=user.lang))

@router.callback_query(F.data == "balance_back")
async def balance_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text("Settings:", reply_markup=settings_keyboard(lang=user.lang))