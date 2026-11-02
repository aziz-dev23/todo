import asyncio
import logging
import sys
from os import getenv

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from models import Base, engine, User, Note

load_dotenv()

TOKEN = getenv("BOT_TOKEN")


dp = Dispatcher()
session = Session(bind=engine)


def buttons_menu():
    rkb = ReplyKeyboardBuilder()
    rkb.add = ([*
        KeyboardButton(text = "Add Note"),
        KeyboardButton(text = "My Notes"),
        KeyboardButton(text = "Last Note Delete")
    ])
    rkb.adjust(2,1)
    return rkb.as_markup(resize_keyboard=True)

class NoteForm(StatesGroup):
    note = State()



@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    query = select(User).where(User.id == message.from_user.id)
    data = session.execute(query).scalar()
    if not data:
        query = insert(User).values(id=message.from_user.id, first_name= message.from_user.first_name)
        session.execute(query)
        session.commit()
    btn = buttons_menu()
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!", reply_markup=btn)

@dp.message(F.text == "Add Note")
async def add_note_handler(message: Message, state : FSMContext) -> None:
    await state.set_state(NoteForm.note)
    await message.answer("Qo'shadigan eslatmani kiriting: ")


@dp.message(F.text, NoteForm.note)
async def add_note_handler(message: Message, state: FSMContext) -> None:
    note = message.text
    query = insert(Note).values(note=note, user_id = message.from_user.id)
    session.execute(query)
    session.commit()
    await state.clear()
    await state.set_state(NoteForm.note)
    btn = buttons_menu()
    await message.answer("Muofaqqiyatli qoshildi", reply_markup=btn)


@dp.message(F.text == "My Notes")
async def my_note_handler(message: Message, state: FSMContext) -> None:
    query = select(Note).where(Note.user_id == message.from_user.id)
    notes = list(session.execute(query).scalars())
    for note in notes:
        await message.answer(text = note.note)

@dp.message(F.text == "Last Note Delete")
async def my_note_handler(message: Message, state: FSMContext) -> None:
    query = select(Note).where(Note.user_id==message.from_user.id).order_by("id")
    notes = list(session.execute(query).scalars())[-1]
    session.delete(notes)
    await message.answer("Ohirgi Note ochirildi ")

async def main() -> None:
    Base.metadata.create_all(engine)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())