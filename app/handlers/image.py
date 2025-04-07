import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from ..states.states import ImageGeneration
from ..utils.db import get_session
from ..models.models import Image
from ..keyboards.keyboards import main_menu, image_options, remove_keyboard, back_to_main_menu
from openai import OpenAI
from config import Config
import requests
import random
import string

router = Router()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

@router.message(F.text == "Generate Image")
async def generate_image(message: Message, state: FSMContext):
    await message.answer("What kind of image would you like to generate? Please describe the theme or idea.", reply_markup=back_to_main_menu())
    await state.set_state(ImageGeneration.description)

@router.message(ImageGeneration.description)
async def process_image_desc(message: Message, state: FSMContext):
    if message.text == "Back":
        await message.answer("Returning to the main menu.", reply_markup=main_menu())
        await state.clear()
        return
    desc = message.text
    await message.answer("Generating image, please wait...", reply_markup=remove_keyboard())
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
    sent_message = await message.answer_photo(FSInputFile(path=image_path), caption=f"Generated for: {desc}", reply_markup=image_options())
    await state.update_data(image_path=image_path, message_id=sent_message.message_id, description=desc)

@router.callback_query(F.data == "save_image")
async def save_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    image = Image(user_id=callback.from_user.id, image_id=data['image_path'])
    session.add(image)
    session.commit()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Image saved successfully! Returning to the main menu.", reply_markup=main_menu())
    await state.clear()

@router.callback_query(F.data == "dont_save_image")
async def dont_save_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if os.path.exists(data['image_path']):
        os.remove(data['image_path'])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Image not saved. Returning to the main menu.", reply_markup=main_menu())
    await state.clear()

@router.callback_query(F.data == "edit_image")
async def edit_image(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Please provide extra information to edit the image description:", reply_markup=back_to_main_menu())
    await state.set_state(ImageGeneration.edit)

@router.message(ImageGeneration.edit)
async def process_image_edit(message: Message, state: FSMContext):
    if message.text == "Back":
        await message.answer("Returning to the main menu.", reply_markup=main_menu())
        await state.clear()
        return
    data = await state.get_data()
    await message.answer("Generating updated image, please wait...", reply_markup=remove_keyboard())
    edit_info = message.text
    new_desc = f"additional prompt: {edit_info}"
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"First prompt: {data['description']}, " + new_desc,
        n=1,
        size="1024x1024"
    )
    image_url = response.data[0].url
    image_path = os.path.join(Config.MEDIA_DIR, f"{message.from_user.id}_{new_desc[:10]}.jpg")
    with open(image_path, 'wb') as f:
        f.write(requests.get(image_url).content)
    if os.path.exists(data['image_path']):
        os.remove(data['image_path'])
    sent_message = await message.answer_photo(FSInputFile(path=image_path), caption=f"Updated for: {new_desc}", reply_markup=image_options())
    await state.update_data(image_path=image_path, message_id=sent_message.message_id)