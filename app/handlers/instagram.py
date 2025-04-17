import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from ..states.states import InstagramAuth, InstagramUpload
from ..utils.db import get_session
from ..models.models import User, ScheduledPost
from ..keyboards.keyboards import main_menu, instagram_submenu, upload_type, yes_no, remove_keyboard, back_to_main_menu
from config import Config
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ClientError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

router = Router()

# Load messages and buttons
with open(os.path.join('lang', 'messages.json'), 'r', encoding='utf-8') as f:
    messages_data = json.load(f)

with open(os.path.join('lang', 'buttons.json'), 'r', encoding='utf-8') as f:
    buttons_data = json.load(f)

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)
challenge_clients = {}

@router.message(lambda message: message.text in [
    buttons_data["services"]["en"][2],  # Create Story + Reels + Post
    buttons_data["services"]["uz"][2],
    buttons_data["services"]["ru"][2]
])
async def instagram_menu(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    if not user.instagram_username:
        await message.answer(
            messages_data["ig_username_prompt"][user.lang],
            reply_markup=back_to_main_menu(lang=user.lang)
        )
        await state.set_state(InstagramAuth.username)
    else:
        await message.answer(
            messages_data["ig_account_linked"][user.lang],
            reply_markup=remove_keyboard()
        )
        await message.answer(
            messages_data["ig_options"][user.lang],
            reply_markup=instagram_submenu(lang=user.lang)
        )

@router.message(InstagramAuth.username)
async def process_username(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()
    
    # Check if the user pressed "Back"
    back_buttons = [buttons_data["back"]["en"][0], buttons_data["back"]["uz"][0], buttons_data["back"]["ru"][0]]
    if message.text in back_buttons:
        await message.answer(
            messages_data["back_to_menu"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
        return

    await state.update_data(username=message.text)
    await message.answer(
        messages_data["ig_password_prompt"][user.lang],
        reply_markup=back_to_main_menu(lang=user.lang)
    )
    await state.set_state(InstagramAuth.password)

def telegram_challenge_code_handler(username, choice):
    raise ChallengeRequired("Challenge code required via Telegram")

@router.message(InstagramAuth.password)
async def process_password(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    # Check if the user pressed "Back"
    back_buttons = [buttons_data["back"]["en"][0], buttons_data["back"]["uz"][0], buttons_data["back"]["ru"][0]]
    if message.text in back_buttons:
        await message.answer(
            messages_data["back_to_menu"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
        return

    data = await state.get_data()
    username = data['username']
    password = message.text
    cli = Client()

    cli.challenge_code_handler = telegram_challenge_code_handler

    try:
        await message.answer(
            messages_data["ig_logging_in"][user.lang],
            reply_markup=remove_keyboard()
        )
        cli.login(username, password)
        cli.dump_settings(os.path.join(SESSIONS_DIR, f"{username}_session.json"))
        session = get_session()
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        user.instagram_username = username
        user.instagram_password = password
        session.commit()
        session.close()

        await message.answer(
            messages_data["ig_credentials_saved"][user.lang],
            reply_markup=instagram_submenu(lang=user.lang)
        )
        await state.clear()

    except ChallengeRequired:
        challenge_clients[message.from_user.id] = (cli, username, password)
        await message.answer(
            messages_data["ig_verification_required"][user.lang]
        )
        await state.set_state(InstagramAuth.verification_code)
    except Exception as e:
        await message.answer(
            messages_data["ig_login_failed"][user.lang].format(error=e),
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()

@router.message(InstagramAuth.verification_code)
async def process_verification_code(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    if message.from_user.id not in challenge_clients:
        await message.answer(
            messages_data["ig_verification_not_found"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
        return

    cli, username, password = challenge_clients[message.from_user.id]
    code = message.text.strip()

    try:
        challenge_data = cli.last_json
        user_id = challenge_data['user_id']
        nonce_code = challenge_data['nonce_code']

        response = cli.private_request(
            f"challenge/{user_id}/{nonce_code}/",
            data={"security_code": code},
            with_signature=True
        )

        if 'logged_in_user' in response:
            cli.dump_settings(os.path.join(SESSIONS_DIR, f"{username}_session.json"))
            session = get_session()
            user = session.query(User).filter_by(user_id=message.from_user.id).first()
            user.instagram_username = username
            user.instagram_password = password
            session.commit()
            session.close()

            del challenge_clients[message.from_user.id]

            await message.answer(
                messages_data["ig_verification_success"][user.lang],
                reply_markup=instagram_submenu(lang=user.lang)
            )
            await state.clear()
            return

        cli.last_json = response
        cli.challenge_resolve(cli.last_json)
        cli.login(username, password)
        cli.dump_settings(os.path.join(SESSIONS_DIR, f"{username}_session.json"))
        session = get_session()
        user = session.query(User).filter_by(user_id=message.from_user.id).first()
        user.instagram_username = username
        user.instagram_password = password
        session.commit()
        session.close()

        del challenge_clients[message.from_user.id]

        await message.answer(
            messages_data["ig_verification_success"][user.lang],
            reply_markup=instagram_submenu(lang=user.lang)
        )
        await state.clear()

    except ClientError as e:
        await message.answer(
            messages_data["ig_invalid_verification_code"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )
        return
    except Exception as e:
        await message.answer(
            messages_data["ig_verification_failed"][user.lang],
            reply_markup=main_menu(lang=user.lang)
        )

@router.callback_query(F.data == "upload_ig")
async def upload_menu(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["ig_upload_type_prompt"][user.lang],
        reply_markup=upload_type(lang=user.lang)
    )

@router.callback_query(F.data == "back_to_ig")
async def back_to_instagram_menu(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["ig_options"][user.lang],
        reply_markup=instagram_submenu(lang=user.lang)
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["ig_main_menu"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )

def get_scheduled_pagination_keyboard(current_index, total_items, post_id, lang="en"):
    buttons = []
    if current_index > 0:
        buttons.append(InlineKeyboardButton(text=buttons_data["back"][lang][0].replace("🔙 ", "⬅️ "), callback_data=f"prev_scheduled_{current_index}_{post_id}"))
    if current_index < total_items - 1:
        buttons.append(InlineKeyboardButton(text=buttons_data["back"][lang][0].replace("🔙 ", "➡️ ").replace("Back", "Next").replace("Orqaga", "Keyingi").replace("Назад", "Далее"), callback_data=f"next_scheduled_{current_index}_{post_id}"))
    buttons.append(InlineKeyboardButton(text=buttons_data["acceptence"][lang][1].replace("❌ ", "🗑️ ").replace("Cancel", "Delete").replace("Bekor qilish", "O'chirish").replace("Отмена", "Удалить"), callback_data=f"delete_scheduled_{current_index}_{post_id}"))
    buttons.append(InlineKeyboardButton(text=buttons_data["back"][lang][0], callback_data="back_to_ig"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.callback_query(F.data == "check_scheduled")
async def check_scheduled(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    posts = session.query(ScheduledPost).filter_by(user_id=callback.from_user.id).order_by(ScheduledPost.time).all()
    session.close()

    await callback.message.edit_reply_markup(reply_markup=None)

    if not posts:
        await callback.message.answer(
            messages_data["ig_no_scheduled_posts"][user.lang],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=buttons_data["back"][user.lang][0], callback_data="back_to_ig")]
                ]
            )
        )
        return

    await state.update_data(scheduled_posts=[p.id for p in posts], scheduled_index=0)
    post = posts[0]

    if not os.path.exists(post.file_path):
        await callback.message.answer(
            messages_data["ig_file_not_found"][user.lang],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=buttons_data["back"][user.lang][0], callback_data="back_to_ig")]
                ]
            )
        )
        return

    keyboard = get_scheduled_pagination_keyboard(0, len(posts), post.id, lang=user.lang)

    if post.file_path.endswith('.jpg') or post.file_path.endswith('.jpeg') or post.file_path.endswith('.png'):
        await callback.message.answer_photo(
            photo=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )
    else:
        await callback.message.answer_video(
            video=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("next_scheduled_"))
async def next_scheduled(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    data = await state.get_data()
    current_index = int(callback.data.split("_")[2])
    scheduled_posts = data.get("scheduled_posts", [])
    new_index = current_index + 1

    if new_index >= len(scheduled_posts):
        await callback.message.answer(messages_data["ig_no_more_scheduled"][user.lang])
        return

    session = get_session()
    post = session.query(ScheduledPost).get(scheduled_posts[new_index])
    session.close()

    keyboard = get_scheduled_pagination_keyboard(new_index, len(scheduled_posts), post.id, lang=user.lang)

    await callback.message.delete()

    if post.file_path.endswith('.jpg') or post.file_path.endswith('.jpeg') or post.file_path.endswith('.png'):
        await callback.message.answer_photo(
            photo=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )
    else:
        await callback.message.answer_video(
            video=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )

    await state.update_data(scheduled_index=new_index)

@router.callback_query(F.data.startswith("prev_scheduled_"))
async def prev_scheduled(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    data = await state.get_data()
    current_index = int(callback.data.split("_")[2])
    scheduled_posts = data.get("scheduled_posts", [])
    new_index = current_index - 1

    if new_index < 0:
        await callback.message.answer(messages_data["ig_first_scheduled"][user.lang])
        return

    session = get_session()
    post = session.query(ScheduledPost).get(scheduled_posts[new_index])
    session.close()

    keyboard = get_scheduled_pagination_keyboard(new_index, len(scheduled_posts), post.id, lang=user.lang)

    await callback.message.delete()

    if post.file_path.endswith('.jpg') or post.file_path.endswith('.jpeg') or post.file_path.endswith('.png'):
        await callback.message.answer_photo(
            photo=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )
    else:
        await callback.message.answer_video(
            video=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )

    await state.update_data(scheduled_index=new_index)

@router.callback_query(F.data.startswith("delete_scheduled_"))
async def delete_scheduled(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    data = await state.get_data()
    current_index = int(callback.data.split("_")[2])
    scheduled_posts = data.get("scheduled_posts", [])

    session = get_session()
    post = session.query(ScheduledPost).get(scheduled_posts[current_index])
    if post:
        if os.path.exists(post.file_path):
            os.remove(post.file_path)
        session.delete(post)
        session.commit()
    session.close()

    scheduled_posts.pop(current_index)
    await state.update_data(scheduled_posts=scheduled_posts)

    await callback.message.delete()

    if not scheduled_posts:
        await callback.message.answer(
            messages_data["ig_no_scheduled_posts"][user.lang],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=buttons_data["back"][user.lang][0], callback_data="back_to_ig")]
                ]
            )
        )
        await state.clear()
        return

    new_index = max(0, current_index - 1)
    session = get_session()
    post = session.query(ScheduledPost).get(scheduled_posts[new_index])
    session.close()

    if not os.path.exists(post.file_path):
        await callback.message.answer(
            messages_data["ig_file_not_found"][user.lang],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=buttons_data["back"][user.lang][0], callback_data="back_to_ig")]
                ]
            )
        )
        return

    keyboard = get_scheduled_pagination_keyboard(new_index, len(scheduled_posts), post.id, lang=user.lang)

    if post.file_path.endswith('.jpg') or post.file_path.endswith('.jpeg') or post.file_path.endswith('.png'):
        await callback.message.answer_photo(
            photo=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )
    else:
        await callback.message.answer_video(
            video=FSInputFile(post.file_path),
            caption=messages_data["ig_scheduled_caption"][user.lang].format(
                caption=post.caption,
                time=post.time.strftime('%Y-%m-%d %H:%M')
            ),
            reply_markup=keyboard
        )

    await state.update_data(scheduled_index=new_index)

@router.callback_query(F.data.in_(["reels", "post", "story"]))
async def process_upload_type(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    await callback.message.edit_reply_markup(reply_markup=None)
    content_type = callback.data
    await state.update_data(content_type=content_type)
    await callback.message.answer(
        messages_data["ig_media_prompt"][user.lang].format(content_type=content_type.capitalize()),
        reply_markup=remove_keyboard()
    )
    await state.set_state(InstagramUpload.media)

@router.message(InstagramUpload.media)
async def process_media(message: Message, state: FSMContext, bot):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    data = await state.get_data()
    os.makedirs(Config.MEDIA_DIR, exist_ok=True)
    caption = message.caption or ""
    
    if message.video:
        file = await bot.get_file(message.video.file_id)
        file_path = os.path.join(Config.MEDIA_DIR, f"{message.from_user.id}_{file.file_id}.mp4")
        await bot.download_file(file.file_path, file_path)
    elif message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = os.path.join(Config.MEDIA_DIR, f"{message.from_user.id}_{file.file_id}.jpg")
        await bot.download_file(file.file_path, file_path)
    else:
        await message.answer(messages_data["ig_media_invalid"][user.lang])
        return
    
    await state.update_data(file_path=file_path, description=caption)
    
    if caption:
        await message.answer(
            messages_data["ig_schedule_prompt"][user.lang],
            reply_markup=remove_keyboard()
        )
        await state.set_state(InstagramUpload.schedule)
    else:
        await message.answer(
            messages_data["ig_description_choice"][user.lang],
            reply_markup=yes_no(lang=user.lang)
        )
        await state.set_state(InstagramUpload.description_choice)

@router.callback_query(F.data == "yes")
async def ask_description(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["ig_description_prompt"][user.lang],
        reply_markup=remove_keyboard()
    )
    await state.set_state(InstagramUpload.description)

@router.message(InstagramUpload.description)
async def process_description(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    if len(message.text) > 150:
        await message.answer(
            messages_data["ig_description_too_long"][user.lang],
            reply_markup=remove_keyboard()
        )
        return
    await state.update_data(description=message.text)
    await message.answer(
        messages_data["ig_schedule_prompt"][user.lang],
        reply_markup=remove_keyboard()
    )
    await state.set_state(InstagramUpload.schedule)

@router.callback_query(F.data == "no")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    session.close()

    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(description="")
    await callback.message.answer(
        messages_data["ig_schedule_prompt"][user.lang],
        reply_markup=remove_keyboard()
    )
    await state.set_state(InstagramUpload.schedule)

@router.callback_query(F.data == "log_out")
async def log_out(callback: CallbackQuery):
    session = get_session()
    user = session.query(User).filter_by(user_id=callback.from_user.id).first()
    
    if user:
        user.instagram_username = None
        user.instagram_password = None
        session.commit()
    
    session.close()
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        messages_data["ig_logout_success"][user.lang],
        reply_markup=main_menu(lang=user.lang)
    )

@router.message(InstagramUpload.schedule)
async def process_schedule(message: Message, state: FSMContext):
    from datetime import datetime
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    session.close()

    try:
        schedule_time = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        if schedule_time < datetime.now():
            await message.answer(
                messages_data["ig_schedule_past_error"][user.lang],
                reply_markup=remove_keyboard()
            )
            return
        data = await state.get_data()
        session = get_session()
        post = ScheduledPost(
            user_id=message.from_user.id,
            file_path=data['file_path'],
            time=schedule_time,
            caption=data.get('description', ''),
            content_type=data['content_type']
        )
        session.add(post)
        session.commit()
        session.close()
        await message.answer(
            messages_data["ig_schedule_success"][user.lang].format(
                content_type=data['content_type'].capitalize(),
                time=message.text
            ),
            reply_markup=main_menu(lang=user.lang)
        )
        await state.clear()
    except ValueError:
        await message.answer(
            messages_data["ig_schedule_format_error"][user.lang],
            reply_markup=remove_keyboard()
        )