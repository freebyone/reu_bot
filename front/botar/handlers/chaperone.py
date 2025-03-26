# handlers/chaperone.py
from math import ceil
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.context import FSMContext
from states.states import ChaperoneState
from services import api_client

router = Router()  # Router for chaperone-related handlers

PER_PAGE = 8  # Максимальное число проектов на одной странице

@router.callback_query(F.data == "role_chaperone")
async def start_chaperone(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли сопровождающего."""
    await callback.answer()
    data = await state.get_data()
    if data.get("teacher") and data.get("projects"):
        await state.set_state(ChaperoneState.main_menu)
        await show_chaperone_menu(callback.message, state)
    else:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await state.set_state(ChaperoneState.entering_login)
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await callback.message.answer("Введи свой логин, пожалуйста:", reply_markup=cancel_kb)

@router.message(ChaperoneState.entering_login)
async def receive_login(message: Message, state: FSMContext):
    """Сохраняет логин и запрашивает ввод пароля."""
    login = message.text.strip()
    if login.lower() == "отмена":
        await message.answer("Отменено. Запусти /start, чтобы начать снова.")
        await state.clear()
        return
    await state.update_data(login=login)
    await state.set_state(ChaperoneState.entering_password)
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Введи свой пароль:", reply_markup=cancel_kb)

@router.message(ChaperoneState.entering_password)
async def receive_password(message: Message, state: FSMContext):
    """Пытается аутентифицировать тебя по введённым логину и паролю."""
    password = message.text.strip()
    if password.lower() == "отмена":
        await message.answer("Вход отменён. Запусти /start, чтобы начать снова.")
        await state.clear()
        return
    data = await state.get_data()
    login = data.get("login")
    if not login:
        await message.answer("Логин утерян, начни заново /start.")
        await state.clear()
        return
    try:
        teacher_data = await api_client.auth_chaperone(login, password)
        print(teacher_data)
    except api_client.ApiError as e:
        err_text = str(e)
        await message.answer(f"❌ {err_text}")
        # Возвращаем тебя к вводу логина
        await state.set_state(ChaperoneState.entering_login)
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("Введи свой логин:", reply_markup=cancel_kb)
        return
    # teacher_data ожидается в формате:
    # {
    #   "projects": [ { "id": "...", "name": "..." }, ... ],
    #   "user": { "id": "...", "login": "...", "password": "...", "school_name": "№17" }
    # }
    teacher_user = teacher_data.get("user", teacher_data)
    projects = teacher_data.get("projects", [])
    await state.update_data(teacher=teacher_user, projects=projects, authorized_role="companion")
    await state.set_state(ChaperoneState.main_menu)
    await show_chaperone_menu(message, state)

async def show_chaperone_menu(message: Message, state: FSMContext):
    """Отображает главное меню для сопровождающего с inline-клавиатурой."""
    data = await state.get_data()
    teacher = data.get("teacher", {})
    school_name = teacher.get("school_name", "не указана")
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выступления 🎤", callback_data="companion_projects")],
        [InlineKeyboardButton(text="Мастер-классы 🎓", callback_data="show_workshops")]
    ])
    await message.answer(f"Привет, ты успешно вошёл! 📚 Школа: *{school_name}*", parse_mode="Markdown")
    await message.answer("Главное меню:", reply_markup=menu_kb)

# ----------------------------
# Обработка кнопки "Выступления 🎤" с пагинацией
@router.callback_query(F.data == "companion_projects")
async def companion_projects(callback: CallbackQuery, state: FSMContext):
    """Отображает список твоих выступлений с пагинацией (если их больше 8)."""
    print("DEBUG: companion_projects handler вызван")
    await callback.answer()
    data = await state.get_data()
    projects = data.get("projects")
    if not projects:
        await callback.message.answer("Список выступлений пуст. 😔")
        return
    sorted_projects = sorted(projects, key=lambda p: p.get("name", "").lower())
    if len(sorted_projects) <= PER_PAGE:
        buttons = []
        for proj in sorted_projects:
            proj_name = proj.get("name", "Без имени")
            proj_id = proj.get("id")
            buttons.append([InlineKeyboardButton(text=proj_name, callback_data=f"project_{proj_id}")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="companion_main_menu")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("Выбери выступление:", reply_markup=kb)
    else:
        await state.update_data(projects_sorted=sorted_projects)
        await display_projects_page(callback.message, state, page=0)

async def display_projects_page(message: Message, state: FSMContext, page: int):
    """Отображает страницу с проектами (пагинация)."""
    data = await state.get_data()
    projects_sorted = data.get("projects_sorted", [])
    if not projects_sorted:
        await message.answer("Список выступлений пуст. 😔")
        return
    total = len(projects_sorted)
    total_pages = ceil(total / PER_PAGE)
    start_index = page * PER_PAGE
    end_index = start_index + PER_PAGE
    current_projects = projects_sorted[start_index:end_index]
    buttons = []
    for proj in current_projects:
        proj_name = proj.get("name", "Без имени")
        proj_id = proj.get("id")
        buttons.append([InlineKeyboardButton(text=proj_name, callback_data=f"project_{proj_id}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="←", callback_data=f"projects_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="→", callback_data=f"projects_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="companion_main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери выступление:", reply_markup=kb)

@router.callback_query(F.data.startswith("projects_page_"))
async def projects_page_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает навигацию между страницами списка выступлений."""
    await callback.answer()
    try:
        page = int(callback.data.split("_")[-1])
    except Exception:
        page = 0
    await display_projects_page(callback.message, state, page)

@router.callback_query(F.data == "companion_main_menu")
async def companion_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возвращает тебя в главное меню для сопровождающего."""
    await callback.answer()
    await show_chaperone_menu(callback.message, state)

@router.callback_query(F.data.startswith("project_"))
async def show_project_details(callback: CallbackQuery, state: FSMContext):
    """Отображает подробную информацию о выбранном выступлении с кнопкой 'Назад' для возврата к списку выступлений."""
    await callback.answer()
    project_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    project_details = data.get(f"project_{project_id}")
    if not project_details:
        try:
            project_details = await api_client.get_speaker_details(project_id)
        except api_client.ApiError as e:
            await callback.message.answer(f"❌ Ошибка получения данных выступления: {e}")
            return
        await state.update_data({f"project_{project_id}": project_details})
    info_text = (
        f"**Детали выступления:**\n\n"
        f"👤 **Имя:** {project_details.get('name', 'не указано')}\n"
        f"📝 **Проект:** {project_details.get('project_name', 'не указан')}\n"
        f"🎤 **Формат:** {project_details.get('project_format', 'не указан')}\n"
        f"🔢 **Слот:** {project_details.get('project_slot', 'не указан')}\n"
        f"⏰ **Время:** {project_details.get('project_time', 'не указано')}\n"
        f"🏫 **Класс:** {project_details.get('school_class', 'не указан')}\n"
        f"📚 **Школа:** {project_details.get('school_name', 'не указана')}\n\n"
        f"Нажми кнопку ниже, чтобы вернуться к списку выступлений."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="companion_projects")]
    ])
    img_url = project_details.get("image_url")
    if img_url:
        try:
            await callback.message.answer_photo(photo=img_url, caption=info_text, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await callback.message.answer(info_text, parse_mode="Markdown", reply_markup=kb)
    else:
        await callback.message.answer(info_text, parse_mode="Markdown", reply_markup=kb)
