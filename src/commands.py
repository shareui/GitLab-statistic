from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def startCommand(message: types.Message):
    text = "This is a gitlab.com language statistics bot created by coder @shareui."
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Source code",
                url="https://gitlab.com/shareui/gitstats"
            )
        ],
        [
            InlineKeyboardButton(
                text="Instruction",
                url="https://gitlab.com/shareui/gitstats/-/blob/main/README.md"
            )
        ]
    ])
    await message.answer(text=text, reply_markup=keyboard)
# idk why it doesn't work
def registerCommands(dispatcher: Dispatcher):
    dispatcher.message.register(startCommand, Command(commands=["start"]))