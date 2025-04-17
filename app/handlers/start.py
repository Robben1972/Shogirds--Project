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
import json

# Load admin ID from environment
ADMIN_ID = int(os.getenv("ADMIN"))

# Load messages from messages.json
with open(os.path.join('lang', 'messages.json'), 'r', encoding='utf-8') as f:
    messages_data = json.load(f)

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    
    if not user:
        await message.answer(
            messages_data["start"]["en"],
            reply_markup=language_keyboard(lang="en")
        )
        await state.set_state(UserInfo.language)
    else:
        await message.answer(
            messages_data["welcome_back"][user.lang].format(name=user.full_name),
            reply_markup=menu_keyboard(lang=user.lang)
        )
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
        await callback.message.edit_text(messages_data["language_selected"][lang])
        await callback.message.answer(
            messages_data["what_is_your_name"][lang],
            reply_markup=remove_keyboard()
        )
        await state.set_state(UserInfo.name)
    else:
        if user:
            user.lang = lang
            session.commit()
            await callback.message.edit_text(
                messages_data["language_updated"][lang],
                reply_markup=settings_keyboard(lang=lang)
            )
        else:
            await callback.message.edit_text(messages_data["user_not_found"][lang])
    
    session.close()

@router.message(UserInfo.name)
async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(name=message.text)
    await message.answer(
        messages_data["what_is_your_surname"][lang],
        reply_markup=remove_keyboard()
    )
    await state.set_state(UserInfo.surname)

@router.message(UserInfo.surname)
async def process_surname(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(surname=message.text)
    await message.answer(
        messages_data["share_phone_number"][lang],
        reply_markup=contact_keyboard(lang=lang)
    )
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
    
    await message.answer(
        messages_data["info_saved"][lang],
        reply_markup=menu_keyboard(lang=lang)
    )
    await state.clear()

@router.callback_query(F.data == "menu_services")
async def show_services(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.answer(
        messages_data["services"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )
    await callback.message.delete()

@router.callback_query(F.data == "menu_settings")
async def show_settings(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["settings"][user.lang],
        reply_markup=settings_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "menu_subscription")
async def show_subscription(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["subscription"][user.lang],
        reply_markup=subscription_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "subscription_back")
async def subscription_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["welcome_back"][user.lang].format(name=user.full_name),
        reply_markup=menu_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "menu_tech_support")
async def show_tech_support(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(messages_data["tech_support_prompt"][user.lang])
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
    
    await message.answer(
        messages_data["tech_support_sent"][user.lang],
        reply_markup=menu_keyboard(lang=user.lang)
    )
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
            await message.bot.send_message(
                user_id,
                f"{messages_data['tech_support_reply'][user.lang]}{message.text}",
                reply_markup=menu_keyboard(lang=user.lang)
            )
            await message.reply(messages_data["admin_reply_sent"][user.lang])

@router.callback_query(F.data == "settings_change_language")
async def change_language(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["start"][user.lang],  # Reuse the "choose language" message
        reply_markup=language_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "settings_balance")
async def show_balance(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["balance"][user.lang].format(balance=user.balance),
        reply_markup=balance_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["welcome_back"][user.lang].format(name=user.full_name),
        reply_markup=menu_keyboard(lang=user.lang)
    )

@router.callback_query(F.data == "balance_back")
async def balance_back(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_text(
        messages_data["settings"][user.lang],
        reply_markup=settings_keyboard(lang=user.lang)
    )