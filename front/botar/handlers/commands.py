# handlers/commands.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("speaker"))
async def speaker_command(message: Message, state: FSMContext):
    print('Speaker')
    data = await state.get_data()
    print(data)
    if data.get("speaker"):
        await message.answer("Вы уже авторизованы как спикер. Перехожу в меню спикера...")
        from handlers.speaker import show_speaker_menu
        await show_speaker_menu(message, state)
    else:
        await message.answer("Вы не авторизованы как спикер. Пожалуйста, нажмите /start и выберите роль 'Спикер 🎤' для авторизации.")

@router.message(Command("companion"))
async def companion_command(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("teacher") and data.get("projects"):
        from handlers.chaperone import show_chaperone_menu
        await show_chaperone_menu(message, state)
    else:
        await message.answer("Вы не авторизованы как сопровождающий. Пожалуйста, нажмите /start и выберите роль 'Сопровождающий 🧑‍🏫' для авторизации.")

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Для того чтобы связаться с администратором позвоните по номеру +7 (777) 777 77-77 доб 7777")

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Начало работы бота. Пожалуйста, выберите роль.")
