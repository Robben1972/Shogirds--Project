# from aiogram import Router, F
# from aiogram.types import CallbackQuery
# from ..utils.db import get_session
# from ..models.models import User
# from ..keyboards.keyboards import main_menu, settings_keyboard, menu_keyboard, balance_keyboard, language_keyboard


# router = Router()


# @router.callback_query(F.data == "menu_services")
# async def show_services(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.answer("Here are the services:", reply_markup=main_menu())
    
#     await callback.message.delete()


# @router.callback_query(F.data == "menu_settings")
# async def show_settings(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text("Settings:", reply_markup=settings_keyboard(lang=user.lang))

# @router.callback_query(F.data == "menu_subscription")
# async def show_subscription(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text("Subscription options will be available soon!", reply_markup=menu_keyboard(lang=user.lang))

# @router.callback_query(F.data == "menu_tech_support")
# async def show_tech_support(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text("Contact tech support at support@example.com", reply_markup=menu_keyboard(lang=user.lang))

# @router.callback_query(F.data == "settings_change_language")
# async def change_language(callback: CallbackQuery):
#     await callback.message.edit_text("Please choose your language:", reply_markup=language_keyboard())

# @router.callback_query(F.data == "settings_balance")
# async def show_balance(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text(f"Your balance: {user.balance}", reply_markup=balance_keyboard(lang=user.lang))

# @router.callback_query(F.data == "settings_back")
# async def settings_back(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text(f"Welcome back, {user.full_name}!", reply_markup=menu_keyboard(lang=user.lang))

# @router.callback_query(F.data == "balance_back")
# async def balance_back(callback: CallbackQuery):
#     session = get_session()
#     user = session.query(User).filter_by(user_id=callback.from_user.id).first()
#     session.close()
    
#     await callback.message.edit_text("Settings:", reply_markup=settings_keyboard(lang=user.lang))