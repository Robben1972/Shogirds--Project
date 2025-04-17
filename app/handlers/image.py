import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendChatAction
from ..states.states import ImageGeneration
from ..utils.db import get_session
from ..models.models import Image, Feedback
from ..keyboards.keyboards import main_menu, image_options, remove_keyboard, back_to_main_menu, feedback_keyboard
from openai import OpenAI
from config import Config
from ..models.models import User
import requests
import random
import string
import json

router = Router()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# Load messages and buttons
with open(os.path.join('lang', 'messages.json'), 'r', encoding='utf-8') as f:
    messages_data = json.load(f)

with open(os.path.join('lang', 'buttons.json'), 'r', encoding='utf-8') as f:
    buttons_data = json.load(f)

@router.message(lambda message: message.text in [
    buttons_data["services"]["en"][1],  # Generate images
    buttons_data["services"]["uz"][1],
    buttons_data["services"]["ru"][1]
])
async def generate_image(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    await message.answer(
        messages_data["image_theme_prompt"][user.lang],
        reply_markup=back_to_main_menu(lang=user.lang)
    )
    await state.set_state(ImageGeneration.description)

@router.message(ImageGeneration.description)
async def process_image_desc(message: Message, state: FSMContext):
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

    desc = message.text
    await message.answer(
        messages_data["generating_image"][user.lang],
        reply_markup=remove_keyboard()
    )
    # Add sending photo action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    response = client.images.generate(
        model="dall-e-3",
        prompt=desc,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    characters = string.ascii_letters + string.digits
    randomize = ''.join(random.choice(characters) for _ in range(10))
    image_path = os.path.join(Config.MEDIA_DIR, f"{message.from_user.id}_{randomize}.jpg")
    os.makedirs(Config.MEDIA_DIR, exist_ok=True)
    with open(image_path, 'wb') as f:
        f.write(requests.get(image_url).content)
    sent_message = await message.answer_photo(
        FSInputFile(path=image_path),
        caption=messages_data["image_caption"][user.lang].format(desc=desc),
        reply_markup=image_options(lang=user.lang)
    )
    await state.update_data(image_path=image_path, message_id=sent_message.message_id, description=desc)

@router.callback_query(F.data == "save_image")
async def save_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    image = Image(user_id=callback.from_user.id, image_id=data['image_path'])
    session.add(image)
    session.commit()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    # Ask for feedback
    await callback.message.answer(
        messages_data["image_saved"][user.lang],
        reply_markup=feedback_keyboard(lang=user.lang)
    )
    await state.update_data(image_id=image.id)

@router.callback_query(F.data == "dont_save_image")
async def dont_save_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    if os.path.exists(data['image_path']):
        os.remove(data['image_path'])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["image_not_saved"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )
    await state.clear()

@router.callback_query(F.data == "edit_image")
async def edit_image(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["edit_image_prompt"][user.lang],
        reply_markup=back_to_main_menu(lang=user.lang)
    )
    await state.set_state(ImageGeneration.edit)

@router.message(ImageGeneration.edit)
async def process_image_edit(message: Message, state: FSMContext):
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
        messages_data["generating_edited_image"][user.lang],
        reply_markup=remove_keyboard()
    )
    # Add sending photo action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    edit_info = message.text
    new_desc = f"additional prompt: {edit_info}"
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"First prompt: {data['description']}, " + new_desc,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    characters = string.ascii_letters + string.digits
    randomize = ''.join(random.choice(characters) for _ in range(10))
    image_path = os.path.join(Config.MEDIA_DIR, f"{message.from_user.id}_{randomize}.jpg")
    with open(image_path, 'wb') as f:
        f.write(requests.get(image_url).content)
    if os.path.exists(data['image_path']):
        os.remove(data['image_path'])
    sent_message = await message.answer_photo(
        FSInputFile(path=image_path),
        caption=messages_data["edit_image_caption"][user.lang].format(desc=new_desc),
        reply_markup=image_options(lang=user.lang)
    )
    await state.update_data(image_path=image_path, message_id=sent_message.message_id, description=new_desc)