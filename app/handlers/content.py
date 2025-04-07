from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from ..states.states import ContentCreation
from ..utils.db import get_session
from ..models.models import Content
from ..keyboards.keyboards import main_menu, content_options, remove_keyboard, back_to_main_menu
from openai import OpenAI
from config import Config

router = Router()
client = OpenAI(api_key=Config.OPENAI_API_KEY)

@router.message(F.text == "Create Content")
async def create_content(message: Message, state: FSMContext):
    await message.answer("In which theme would you like to make content?", reply_markup=back_to_main_menu())
    await state.set_state(ContentCreation.theme)

@router.message(ContentCreation.theme)
async def process_theme(message: Message, state: FSMContext):
    if message.text == "Back":
        await message.answer("Returning to the main menu.", reply_markup=main_menu())
        await state.clear()
        return
    theme = message.text
    await message.answer("Generating content, please wait...", reply_markup=remove_keyboard())
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
                {
        "role": "system",
        "content": (
            "You are an advanced AI content creator for social media platforms like Instagram, Telegram, YouTube, and LinkedIn. "
            "You generate creative, emotionally compelling, and visually clear content based on the user’s theme or request.\n\n"

            "You understand and deliver different content types, based on what the user asks:\n"
            "• If the user wants a **caption/post**, write 3–5 concise, scroll-stopping sentences with a hook and call to action.\n"
            "• If the user asks for a **Reels/video idea**, deliver a short, bold title + hook, then outline key scenes or script beats.\n"
            "• If they request a **carousel idea**, provide slide-by-slide text with a clear flow.\n"
            "• If they mention a **story sequence**, generate Instagram Story with each story having: a bolded title, short narrative, and an interactive element like a poll or question.\n"
            "• If the theme is abstract or brand-based (e.g., 'elegance', 'confidence'), turn it into an emotional campaign idea or narrative.\n\n"

            "📝 **Formatting Rules (important!):**\n"
            "- Use HTML formatting: bold, italic, emojis, and line breaks.\n"
            "- Do **not** use hashtags or symbols like '---' or '•' as separators.\n"
            "- Add enough line spacing to make content readable on Telegram.\n"
            "- Only return the formatted content. Do not explain or introduce anything.\n\n"
            "- Add stickers to attract attention.\n"
            "- Use a friendly and inviting tone.\n"

            "Your tone must be creative, human, emotionally intelligent, and aligned with the needs of fashion, beauty, wellness, personal brands, or modern online businesses."
        )
        },
            {"role": "user", "content": f"{theme}"}
        ]
    )
    content = response.choices[0].message.content
    await message.answer(content, reply_markup=content_options(), parse_mode="HTML")
    await state.update_data(content=content)

@router.callback_query(F.data == "save_content")
async def save_content(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_session()
    content = Content(user_id=callback.from_user.id, content=data['content'])
    session.add(content)
    session.commit()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Content saved successfully! Returning to the main menu.", reply_markup=main_menu())
    await state.clear()

@router.callback_query(F.data == "dont_save_content")
async def dont_save_content(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Content not saved. Returning to the main menu.", reply_markup=main_menu())
    await state.clear()

@router.callback_query(F.data == "edit_content")
async def edit_content(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Please provide extra information to edit the content:", reply_markup=back_to_main_menu())
    await state.set_state(ContentCreation.edit)

@router.message(ContentCreation.edit)
async def process_edit(message: Message, state: FSMContext):
    if message.text == "Back":
        await message.answer("Returning to the main menu.", reply_markup=main_menu())
        await state.clear()
        return
    data = await state.get_data()
    await message.answer("Generating edited content, please wait...", reply_markup=remove_keyboard())
    edit_info = message.text
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{
        "role": "system",
        "content": (
            "You are an advanced AI content creator for social media platforms like Instagram, Telegram, YouTube, and LinkedIn. "
            "You generate creative, emotionally compelling, and visually clear content based on the user’s theme or request.\n\n"

            "You understand and deliver different content types, based on what the user asks:\n"
            "• If the user wants a **caption/post**, write 3–5 concise, scroll-stopping sentences with a hook and call to action.\n"
            "• If the user asks for a **Reels/video idea**, deliver a short, bold title + hook, then outline key scenes or script beats.\n"
            "• If they request a **carousel idea**, provide slide-by-slide text with a clear flow.\n"
            "• If they mention a **story sequence**, generate Instagram Story with each story having: a bolded title, short narrative, and an interactive element like a poll or question.\n"
            "• If the theme is abstract or brand-based (e.g., 'elegance', 'confidence'), turn it into an emotional campaign idea or narrative.\n\n"

            "📝 **Formatting Rules (important!):**\n"
            "- Use HTML formatting: bold, italic, emojis, and line breaks.\n"
            "- Do **not** use hashtags or symbols like '---' or '•' as separators.\n"
            "- Add enough line spacing to make content readable on Telegram.\n"
            "- Only return the formatted content. Do not explain or introduce anything.\n\n"
            "- Add stickers to attract attention.\n"
            "- Use a friendly and inviting tone.\n"

            "Your tone must be creative, human, emotionally intelligent, and aligned with the needs of fashion, beauty, wellness, personal brands, or modern online businesses."
        )
        },
        {"role": "user", "content": f"Edit this content with additional info: '{data['content']}' - {edit_info}"}]
    )
    updated_content = response.choices[0].message.content
    await message.answer(updated_content, reply_markup=content_options(), parse_mode="HTML")
    await state.update_data(content=updated_content)