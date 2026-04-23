from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
from datetime import datetime, timedelta
import csv

BOT_TOKEN = "8636208292:AAFbikyusM5qo9WVFKjE6rf8-Vv2YldO4_I"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === СТАТИСТИКА (мини CRM аналитика) ===
stats = {
    "events_opened": 0,
    "b2b_opened": 0,
    "b2b_submitted": 0
}

# === FSM ===
class B2BForm(StatesGroup):
    name = State()
    company = State()
    phone = State()

# === CSV CRM ===
def save_lead(name, company, phone):
    with open("b2b_leads.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            name,
            company,
            phone
        ])

# === МЕНЮ ===
main_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🎪 Мероприятия выставки")],
        [types.KeyboardButton(text="🤝 B2B встречи")],
        [types.KeyboardButton(text="📦 Каталог продукции")]
    ],
    resize_keyboard=True
)

# === START ===
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать на выставку GEFEST 🔥\n\nВыберите раздел:",
        reply_markup=main_keyboard
    )

# =========================
# 📦 КАТАЛОГ ПРОДУКЦИИ
# =========================
@dp.message(F.text == "📦 Каталог продукции")
async def catalog(message: types.Message):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Плиты", callback_data="cat_stoves")],
        [InlineKeyboardButton(text="🏠 Встраиваемая техника", callback_data="cat_built")],
        [InlineKeyboardButton(text="💨 Воздухоочистители", callback_data="cat_hoods")]
    ])

    await message.answer(
        "📖 Каталог продукции\n\nВыберите категорию:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "cat_stoves")
async def stoves(callback: types.CallbackQuery):
    file = FSInputFile("Плиты.pdf")
    await callback.message.answer_document(file, caption="🔥 Каталог: Плиты GEFEST")


@dp.callback_query(F.data == "cat_built")
async def built(callback: types.CallbackQuery):
    file = FSInputFile("Встраиваемая техника.pdf")
    await callback.message.answer_document(file, caption="🏠 Каталог: Встраиваемая техника GEFEST")


@dp.callback_query(F.data == "cat_hoods")
async def hoods(callback: types.CallbackQuery):
    file = FSInputFile("Воздухоочистители.pdf")
    await callback.message.answer_document(file, caption="💨 Каталог: Воздухоочистители GEFEST")

# === EVENTS ===
@dp.message(F.text == "🎪 Мероприятия выставки")
async def events(message: types.Message):
    stats["events_opened"] += 1

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Открытие (10:00)", callback_data="event_open")],
        [InlineKeyboardButton(text="📢 Презентация техники (11:30)", callback_data="event_presentation")],
        [InlineKeyboardButton(text="🍳 Кулинарное шоу (13:00)", callback_data="event_cook")],
        [InlineKeyboardButton(text="🏆 Розыгрыш призов (17:00)", callback_data="event_prize")]
    ])

    await message.answer("🎪 Выберите мероприятие:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("event_"))
async def choose_event(callback: types.CallbackQuery):

    event_map = {
        "event_open": "🔥 Открытие выставки в 10:00\n\nТоржественное открытие стенда и обзор экспозиции.",
        "event_presentation": "📢 Презентация техники в 11:30\n\nСпециалисты GEFEST подробно расскажут о кухонных плитах и их преимуществах.",
        "event_cook": "🍳 Кулинарное шоу в 13:00\n\nШеф-повар приготовит блюда на плитах GEFEST с демонстрацией возможностей техники.",
        "event_prize": "🏆 Розыгрыш призов в 17:00\n\nИнтерактив с посетителями и розыгрыш сувениров."
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Напомнить за 1 час", callback_data=f"remind_{callback.data}")]
    ])

    await callback.message.answer(
        f"{event_map.get(callback.data)}\n\nХотите напоминание?",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("remind_"))
async def set_reminder(callback: types.CallbackQuery):

    await callback.message.answer("✅ Напоминание установлено!")

    user_id = callback.from_user.id

    event_times = {
        "remind_event_open": datetime(2026, 9, 30, 10, 0),
        "remind_event_presentation": datetime(2026, 9, 30, 11, 30),
        "remind_event_cook": datetime(2026, 9, 30, 13, 0),
        "remind_event_prize": datetime(2026, 9, 30, 17, 0)
    }

    event_time = event_times.get(callback.data)
    if not event_time:
        return

    remind_time = event_time - timedelta(hours=1)
    wait_seconds = (remind_time - datetime.now()).total_seconds()

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

        await bot.send_message(
            user_id,
            "⏰ Напоминание!\nЧерез 1 час начнётся мероприятие GEFEST 🔥"
        )

# === B2B ===
@dp.message(F.text == "🤝 B2B встречи")
async def b2b_start(message: types.Message, state: FSMContext):
    stats["b2b_opened"] += 1
    await message.answer("👤 Введите ваше имя:")
    await state.set_state(B2BForm.name)

@dp.message(B2BForm.name)
async def b2b_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🏢 Введите компанию:")
    await state.set_state(B2BForm.company)

@dp.message(B2BForm.company)
async def b2b_company(message: types.Message, state: FSMContext):
    await state.update_data(company=message.text)
    await message.answer("📞 Введите телефон:")
    await state.set_state(B2BForm.phone)

@dp.message(B2BForm.phone)
async def b2b_phone(message: types.Message, state: FSMContext):

    data = await state.get_data()

    name = data["name"]
    company = data["company"]
    phone = message.text

    save_lead(name, company, phone)

    stats["b2b_submitted"] += 1

    await message.answer(
        f"✅ Заявка отправлена!\n\n👤 {name}\n🏢 {company}\n📞 {phone}"
    )

    await state.clear()

# === STATS ===
@dp.message(Command("stats"))
async def stats_cmd(message: types.Message):

    await message.answer(
        "📊 СТАТИСТИКА:\n\n"
        f"🎪 Мероприятия: {stats['events_opened']}\n"
        f"🤝 B2B: {stats['b2b_opened']}\n"
        f"📩 Заявки: {stats['b2b_submitted']}"
    )

# === RUN ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())