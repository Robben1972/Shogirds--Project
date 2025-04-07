from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ..states.states import UserInfo
from ..utils.db import get_session
from ..models.models import User
from ..keyboards.keyboards import main_menu, contact_keyboard, remove_keyboard

router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    session = get_session()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if not user:
        await message.answer(
            "Hello! Welcome to the Content Creation Bot! Let's get started by gathering some information about you.",
            reply_markup=remove_keyboard()
        )
        await message.answer("What is your name?", reply_markup=remove_keyboard())
        await state.set_state(UserInfo.name)
    else:
        await message.answer("Welcome back!", reply_markup=main_menu())
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
    session = get_session()
    user = User(
        user_id=message.from_user.id,
        full_name=full_name,
        phone_number=phone_number
    )
    session.add(user)
    session.commit()
    session.close()
    await message.answer("Information saved! Here's the main menu:", reply_markup=main_menu())
    await state.clear()