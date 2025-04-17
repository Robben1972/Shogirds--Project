from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from ..utils.db import get_session
from ..models.models import Content, Image
from ..keyboards.keyboards import main_menu, saved_contents_menu, remove_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
from ..models.models import User

router = Router()

# Load messages and buttons
with open(os.path.join('lang', 'messages.json'), 'r', encoding='utf-8') as f:
    messages_data = json.load(f)

with open(os.path.join('lang', 'buttons.json'), 'r', encoding='utf-8') as f:
    buttons_data = json.load(f)

class PaginationState:
    CONTENT = "content"
    IMAGES = "images"

def get_pagination_keyboard(item_type, current_index, total_items, item_id, lang="en"):
    buttons = []
    if current_index > 0:
        buttons.append(InlineKeyboardButton(
            text=buttons_data["back"][lang][0].replace("🔙 ", "⬅️ ").replace("Back", "Previous").replace("Orqaga", "Oldingi").replace("Назад", "Предыдущий"),
            callback_data=f"prev_{item_type}_{current_index}_{item_id}"
        ))
    if current_index < total_items - 1:
        buttons.append(InlineKeyboardButton(
            text=buttons_data["back"][lang][0].replace("🔙 ", "➡️ ").replace("Back", "Next").replace("Orqaga", "Keyingi").replace("Назад", "Далее"),
            callback_data=f"next_{item_type}_{current_index}_{item_id}"
        ))
    buttons.append(InlineKeyboardButton(
        text=buttons_data["acceptence"][lang][1].replace("❌ ", "🗑️ ").replace("Cancel", "Delete").replace("Bekor qilish", "O'chirish").replace("Отмена", "Удалить"),
        callback_data=f"delete_{item_type}_{current_index}_{item_id}"
    ))
    buttons.append(InlineKeyboardButton(
        text=buttons_data["acceptence"][lang][1],
        callback_data="cancel"
    ))
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.message(lambda message: message.text in [
    buttons_data["menu"]["en"][1],  # Saved Contents
    buttons_data["menu"]["uz"][1],
    buttons_data["menu"]["ru"][1]
])
async def saved_contents(message: Message):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    
    await message.answer(
        messages_data["saved_view_prompt"][user.lang],
        reply_markup=remove_keyboard()
    )
    await message.answer(
        messages_data["saved_choose_view"][user.lang],
        reply_markup=saved_contents_menu(lang=user.lang)
    )

@router.callback_query(F.data == "view_content")
async def view_content(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    contents = session.query(Content).filter_by(user_id=callback.from_user.id).order_by(Content.id).all()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if not contents:
        await callback.message.answer(
            messages_data["saved_no_content"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        return
    
    await state.update_data(content_list=[c.id for c in contents], content_index=0)
    content = contents[0]
    keyboard = get_pagination_keyboard(PaginationState.CONTENT, 0, len(contents), content.id, lang=user.lang)
    sent_message = await callback.message.answer(
        messages_data["saved_content_caption"][user.lang].format(
            current=1,
            total=len(contents),
            content=content.content
        ),
        reply_markup=keyboard
    )
    await state.update_data(last_message_id=sent_message.message_id)

@router.callback_query(F.data == "view_images")
async def view_images(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    images = session.query(Image).filter_by(user_id=callback.from_user.id).order_by(Image.id).all()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if not images:
        await callback.message.answer(
            messages_data["saved_no_images"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        return
    
    await state.update_data(image_list=[i.id for i in images], image_index=0)
    image = images[0]
    keyboard = get_pagination_keyboard(PaginationState.IMAGES, 0, len(images), image.id, lang=user.lang)
    sent_message = await callback.message.answer_photo(
        FSInputFile(path=image.image_id),
        reply_markup=keyboard
    )
    await state.update_data(last_message_id=sent_message.message_id)

@router.callback_query(F.data.startswith("next_"))
async def next_item(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    item_type, current_index, item_id = callback.data.split("_")[1], int(callback.data.split("_")[2]), int(callback.data.split("_")[3])
    
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message_id)
    
    if item_type == PaginationState.CONTENT:
        content_list = data.get("content_list", [])
        new_index = current_index + 1
        if new_index >= len(content_list):
            await callback.message.answer(
                messages_data["saved_no_more_content"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
            return
        session = get_session()
        content = session.query(Content).get(content_list[new_index])
        session.close()
        keyboard = get_pagination_keyboard(item_type, new_index, len(content_list), content.id, lang=user.lang)
        sent_message = await callback.message.answer(
            messages_data["saved_content_caption"][user.lang].format(
                current=new_index + 1,
                total=len(content_list),
                content=content.content
            ),
            reply_markup=keyboard
        )
        await state.update_data(content_index=new_index, last_message_id=sent_message.message_id)
    
    elif item_type == PaginationState.IMAGES:
        image_list = data.get("image_list", [])
        new_index = current_index + 1
        if new_index >= len(image_list):
            await callback.message.answer(
                messages_data["saved_no_more_images"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
            return
        session = get_session()
        image = session.query(Image).get(image_list[new_index])
        session.close()
        keyboard = get_pagination_keyboard(item_type, new_index, len(image_list), image.id, lang=user.lang)
        sent_message = await callback.message.answer_photo(
            FSInputFile(path=image.image_id),
            reply_markup=keyboard
        )
        await state.update_data(image_index=new_index, last_message_id=sent_message.message_id)

@router.callback_query(F.data.startswith("prev_"))
async def prev_item(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    item_type, current_index, item_id = callback.data.split("_")[1], int(callback.data.split("_")[2]), int(callback.data.split("_")[3])
    
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message_id)
    
    if item_type == PaginationState.CONTENT:
        content_list = data.get("content_list", [])
        new_index = current_index - 1
        if new_index < 0:
            await callback.message.answer(
                messages_data["saved_first_content"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
            return
        session = get_session()
        content = session.query(Content).get(content_list[new_index])
        session.close()
        keyboard = get_pagination_keyboard(item_type, new_index, len(content_list), content.id, lang=user.lang)
        sent_message = await callback.message.answer(
            messages_data["saved_content_caption"][user.lang].format(
                current=new_index + 1,
                total=len(content_list),
                content=content.content
            ),
            reply_markup=keyboard
        )
        await state.update_data(content_index=new_index, last_message_id=sent_message.message_id)
    
    elif item_type == PaginationState.IMAGES:
        image_list = data.get("image_list", [])
        new_index = current_index - 1
        if new_index < 0:
            await callback.message.answer(
                messages_data["saved_first_image"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
            return
        session = get_session()
        image = session.query(Image).get(image_list[new_index])
        session.close()
        keyboard = get_pagination_keyboard(item_type, new_index, len(image_list), image.id, lang=user.lang)
        sent_message = await callback.message.answer_photo(
            FSInputFile(path=image.image_id),
            reply_markup=keyboard
        )
        await state.update_data(image_index=new_index, last_message_id=sent_message.message_id)

@router.callback_query(F.data.startswith("delete_"))
async def delete_item(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    item_type, current_index, item_id = callback.data.split("_")[1], int(callback.data.split("_")[2]), int(callback.data.split("_")[3])
    
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message_id)
    
    session = get_session()
    if item_type == PaginationState.CONTENT:
        content = session.query(Content).get(item_id)
        if content:
            session.delete(content)
            session.commit()
        content_list = data.get("content_list", [])
        content_list.pop(current_index)
        await state.update_data(content_list=content_list, content_index=max(0, current_index - 1))
        new_index = max(0, current_index - 1)
        if content_list:
            new_content = session.query(Content).get(content_list[new_index])
            keyboard = get_pagination_keyboard(item_type, new_index, len(content_list), new_content.id, lang=user.lang)
            sent_message = await callback.message.answer(
                messages_data["saved_content_deleted"][user.lang].format(
                    current=new_index + 1,
                    total=len(content_list),
                    content=new_content.content
                ),
                reply_markup=keyboard
            )
            await state.update_data(last_message_id=sent_message.message_id)
        else:
            await callback.message.answer(
                messages_data["saved_no_content_left"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
    
    elif item_type == PaginationState.IMAGES:
        image = session.query(Image).get(item_id)
        if image:
            if os.path.exists(image.image_id):
                os.remove(image.image_id)
            session.delete(image)
            session.commit()
        image_list = data.get("image_list", [])
        image_list.pop(current_index)
        await state.update_data(image_list=image_list, image_index=max(0, current_index - 1))
        new_index = max(0, current_index - 1)
        if image_list:
            new_image = session.query(Image).get(image_list[new_index])
            keyboard = get_pagination_keyboard(item_type, new_index, len(image_list), new_image.id, lang=user.lang)
            sent_message = await callback.message.answer_photo(
                FSInputFile(path=new_image.image_id),
                reply_markup=keyboard
            )
            await state.update_data(last_message_id=sent_message.message_id)
        else:
            await callback.message.answer(
                messages_data["saved_no_images_left"][user.lang],
                reply_markup=main_menu(lang=user.lang)
            )
            await state.clear()
    
    session.close()

@router.callback_query(F.data == "cancel")
async def cancel_pagination(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)  
    data = await state.get_data()
    last_message_id = data.get("last_message_id")
    if last_message_id:
        await callback.message.bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message_id)
    await callback.message.answer(
        messages_data["saved_return_to_main"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )
    await state.clear()