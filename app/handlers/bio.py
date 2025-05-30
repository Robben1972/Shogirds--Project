from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendChatAction
from ..states.states import ContentCreation
from ..utils.db import get_session
from ..models.models import Content, User, Feedback
from ..keyboards.keyboards import main_menu, content_options, remove_keyboard, back_to_main_menu, menu_keyboard, feedback_keyboard
from openai import OpenAI
from config import Config
import json
import os

router = Router()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Load messages and buttons
with open(os.path.join('lang', 'messages.json'), 'r', encoding='utf-8') as f:
    messages_data = json.load(f)

with open(os.path.join('lang', 'buttons.json'), 'r', encoding='utf-8') as f:
    buttons_data = json.load(f)

@router.message(lambda message: message.text in [
    buttons_data["services"]["en"][5],  # Create a content plan
    buttons_data["services"]["uz"][5],
    buttons_data["services"]["ru"][5]
])
async def create_content(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    await message.answer(
        messages_data["content_theme_prompt"][user.lang],
        reply_markup=back_to_main_menu(lang=user.lang)
    )
    await state.set_state(ContentCreation.theme)

@router.message(ContentCreation.theme)
async def process_theme(message: Message, state: FSMContext):
    # Check if the user pressed "Back"
    back_buttons = [buttons_data["back"]["en"][0], buttons_data["back"]["uz"][0], buttons_data["back"]["ru"][0]]
    if message.text in back_buttons:
        session = get_session()
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        session.close()
        await message.answer(
            messages_data["back_to_menu"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
        return

    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    theme = message.text
    await message.answer(
        messages_data["generating_content"][user.lang],
        reply_markup=remove_keyboard()
    )
    # Add typing action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                     """You are a professional Social Media Marketing (SMM) assistant with expertise in content creation for Instagram. You help users create engaging bio.
                       You understand current trends, know how to write in a fun, relatable tone, and can adjust your writing style depending on the user's niche (e.g., travel, fashion, education, fitness, business, etc.).
                       Create content that is short, catchy, and optimized for high engagement. Focus on storytelling, hooks, emojis, and call-to-actions where appropriate.
                       Your goal is to save time, spark creativity, and help users grow their Instagram organically and authentically.
                       Format your responses using HTML tags for Telegram (like <b>bold</b>, <i>italic</i>, <u>underline</u>, <code>code</code>, etc.). Do NOT use Markdown symbols like #, *, -, or backticks.
                       Your answers should be friendly, structured, clear and return in the given questions language (uzbek, russian or english, otherwise you should return "I didn't understand you")."""
                )
            },
            {"role": "user", "content": f"{theme}"}
        ]
    )
    content = response.choices[0].message.content
    await message.answer(
        content,
        reply_markup=content_options(lang=user.lang),
        parse_mode="HTML"
    )
    await state.update_data(content=content)

@router.callback_query(F.data == "save_content")
async def save_content(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    content = Content(user_id=callback.from_user.id, content=data['content'])
    session.add(content)
    session.commit()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    # Ask for feedback
    await callback.message.answer(
        messages_data["content_saved"][user.lang],
        reply_markup=feedback_keyboard(lang=user.lang)
    )
    await state.update_data(content_id=content.id)

@router.callback_query(F.data == "dont_save_content")
async def dont_save_content(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["content_not_saved"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )
    await state.clear()

@router.callback_query(F.data == "edit_content")
async def edit_content(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["edit_content_prompt"][user.lang],
        reply_markup=back_to_main_menu(lang=user.lang)
    )
    await state.set_state(ContentCreation.edit)

@router.message(ContentCreation.edit)
async def process_edit(message: Message, state: FSMContext):
    # Check if the user pressed "Back"
    back_buttons = [buttons_data["back"]["en"][0], buttons_data["back"]["uz"][0], buttons_data["back"]["ru"][0]]
    if message.text in back_buttons:
        session = get_session()
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        session.close()
        await message.answer(
            messages_data["back_to_menu"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
        return

    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    data = await state.get_data()
    await message.answer(
        messages_data["generating_edited_content"][user.lang],
        reply_markup=remove_keyboard()
    )
    # Add typing action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    edit_info = message.text
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    """You are a professional Social Media Marketing (SMM) assistant with expertise in content creation for Instagram. You help users create engaging bio.
                       You understand current trends, know how to write in a fun, relatable tone, and can adjust your writing style depending on the user's niche (e.g., travel, fashion, education, fitness, business, etc.).
                       Create content that is short, catchy, and optimized for high engagement. Focus on storytelling, hooks, emojis, and call-to-actions where appropriate.
                       Your goal is to save time, spark creativity, and help users grow their Instagram organically and authentically.
                       Format your responses using HTML tags for Telegram (like <b>bold</b>, <i>italic</i>, <u>underline</u>, <code>code</code>, etc.). Do NOT use Markdown symbols like #, *, -, or backticks.
                       Your answers should be friendly, structured, clear and return in the given questions language (uzbek, russian or english, otherwise you should return "I didn't understand you")."""
                )
            },
            {"role": "user", "content": f"Edit this content with additional info: '{data['content']}' - {edit_info}"}
        ]
    )
    updated_content = response.choices[0].message.content
    await message.answer(
        updated_content,
        reply_markup=content_options(lang=user.lang),
        parse_mode="HTML"
    )
    await state.update_data(content=updated_content)

@router.callback_query(F.data.startswith("feedback_"))
async def process_feedback(callback: CallbackQuery, state: FSMContext):
    feedback_type = callback.data.split("_")[1]  # 'like', 'dislike', or 'neutral'
    data = await state.get_data()
    content_id = data.get('content_id') or data.get('image_id')  # Works for both content and image
    
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    feedback = Feedback(user_id=callback.from_user.id, feedback=feedback_type)
    session.add(feedback)
    session.commit()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["feedback_thanks"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )
    await state.clear()