from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import date

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import User
from app.services.ai import analyze_food_image, parse_food_text, transcribe_voice
from app.services.app_logic import (
    add_meal,
    delete_last_meal,
    friend_leaderboard,
    get_daily_summary,
    get_or_create_user,
    global_leaderboard,
)
from app.services.nutrition import calculate_targets


class Onboarding(StatesGroup):
    weight = State()
    height = State()
    age = State()
    gender = State()
    activity = State()
    goal = State()


dp = Dispatcher()


def _find_user(db, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).one_or_none()


@dp.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    start_args = None
    if message.text and len(message.text.split()) > 1:
        start_args = message.text.split()[1]

    with SessionLocal() as db:
        inviter_tid = int(start_args) if start_args and start_args.isdigit() else None
        user = get_or_create_user(
            db,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            inviter_telegram_id=inviter_tid,
        )

        if not user.weight:
            await state.set_state(Onboarding.weight)
            await message.answer("Assalomu alaykum! Vazningizni kiriting (kg):")
        else:
            await message.answer("Xush kelibsiz! /add, /summary, /leaderboard buyruqlaridan foydalaning.")


@dp.message(Onboarding.weight)
async def set_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await state.set_state(Onboarding.height)
    await message.answer('Bo\'yingizni kiriting (cm):')


@dp.message(Onboarding.height)
async def set_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await state.set_state(Onboarding.age)
    await message.answer('Yoshingiz:')


@dp.message(Onboarding.age)
async def set_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await state.set_state(Onboarding.gender)
    await message.answer("Jinsingizni kiriting (male/female):")


@dp.message(Onboarding.gender)
async def set_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text.strip().lower())
    await state.set_state(Onboarding.activity)
    await message.answer('Faollik darajasi: sedentary/light/moderate/active/very_active')


@dp.message(Onboarding.activity)
async def set_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text.strip().lower())
    await state.set_state(Onboarding.goal)
    await message.answer('Maqsad: lose / maintain / bulk')


@dp.message(Onboarding.goal)
async def set_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    goal = message.text.strip().lower()
    cals, protein, carbs, fats = calculate_targets(
        weight=data['weight'],
        height=data['height'],
        age=data['age'],
        gender=data['gender'],
        activity_level=data['activity'],
        goal=goal,
    )
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        user.weight = data['weight']
        user.height = data['height']
        user.age = data['age']
        user.gender = data['gender']
        user.activity_level = data['activity']
        user.goal = goal
        user.calorie_target = cals
        user.protein_target = protein
        user.carb_target = carbs
        user.fat_target = fats
        db.commit()
    await state.clear()
    await message.answer(f"Profil saqlandi ✅\nKaloriya: {cals}\nP: {protein} C: {carbs} F: {fats}")


@dp.message(Command('add'))
async def cmd_add(message: Message):
    await message.answer('Ovqatni matn, ovoz yoki rasm ko\'rinishida yuboring.')


@dp.message(F.voice)
async def handle_voice(message: Message):
    bot = message.bot
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp:
        await bot.download(message.voice, destination=tmp)
        tmp_path = tmp.name
    try:
        text = parse_food_text(transcribe_voice(tmp_path))
        with SessionLocal() as db:
            user = _find_user(db, message.from_user.id)
            add_meal(db, user, text.food_name, text.calories, text.protein, text.carbs, text.fats)
        await message.answer(f"Qo'shildi: {text.food_name} ({text.calories} kcal)")
    finally:
        os.remove(tmp_path)


@dp.message(F.photo)
async def handle_photo(message: Message):
    bot = message.bot
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        await bot.download(message.photo[-1], destination=tmp)
        tmp_path = tmp.name
    try:
        parsed = analyze_food_image(tmp_path)
        with SessionLocal() as db:
            user = _find_user(db, message.from_user.id)
            add_meal(db, user, parsed.food_name, parsed.calories, parsed.protein, parsed.carbs, parsed.fats)
        await message.answer(f"Rasm tahlili bo'yicha qo'shildi: {parsed.food_name} — {parsed.calories} kcal")
    finally:
        os.remove(tmp_path)


@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text_food(message: Message):
    parsed = parse_food_text(message.text)
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        if not user:
            await message.answer('Avval /start bosing.')
            return
        add_meal(db, user, parsed.food_name, parsed.calories, parsed.protein, parsed.carbs, parsed.fats)
    await message.answer(f"✅ Saqlandi: {parsed.food_name}\n{parsed.calories} kcal | P{parsed.protein} C{parsed.carbs} F{parsed.fats}")


@dp.message(Command('summary'))
async def cmd_summary(message: Message):
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        if not user:
            await message.answer('Avval /start qiling.')
            return
        s = get_daily_summary(db, user, date.today())
    await message.answer(
        f"🔥 Bugungi natija\n\n"
        f"Kaloriya: {s.calories} / {s.calorie_target} kcal\n"
        f"Protein: {s.protein}g / {s.protein_target}g\n"
        f"Uglevod: {s.carbs}g / {s.carb_target}g\n"
        f"Yog‘: {s.fats}g / {s.fat_target}g\n\n"
        f"Qolgan kaloriya: {s.remaining_calories} kcal\n"
        f"🔥 Bugungi progress: {s.score}%"
    )


@dp.message(Command('profile'))
async def cmd_profile(message: Message):
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        if not user:
            await message.answer('Avval /start qiling.')
            return
    await message.answer(
        f"Profil:\n{user.weight}kg, {user.height}cm, {user.age} yosh\n"
        f"Maqsad: {user.goal}\nTarget: {user.calorie_target} kcal"
    )


@dp.message(Command('delete_last'))
async def cmd_delete_last(message: Message):
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        result = delete_last_meal(db, user) if user else False
    await message.answer('Oxirgi ovqat o‘chirildi.' if result else 'O‘chiradigan ovqat topilmadi.')


@dp.message(Command('invite'))
async def cmd_invite(message: Message):
    link = f"https://t.me/YourBot?start={message.from_user.id}"
    await message.answer(f"Do‘stlaringizni taklif qiling!\n\nSizning havolangiz:\n{link}")


@dp.message(Command('leaderboard'))
async def cmd_leaderboard(message: Message):
    with SessionLocal() as db:
        user = _find_user(db, message.from_user.id)
        if not user:
            await message.answer('Avval /start qiling.')
            return
        friends = friend_leaderboard(db, user)
        global_top = global_leaderboard(db)

    f_text = '\n'.join([f"{i+1}️⃣ {row['name']} — {row['score']}%" for i, row in enumerate(friends)])
    g_text = '\n'.join([f"{i+1}️⃣ {row['name']} — {row['score']}%" for i, row in enumerate(global_top[:10])])
    await message.answer(f"🏆 Do‘stlar reytingi\n\n{f_text}\n\n🌍 Global reyting\n\n{g_text}")


@dp.message(Command('dashboard'))
async def cmd_dashboard(message: Message):
    await message.answer(f"Dashboard: {settings.base_url}/dashboard?user_id={message.from_user.id}")


async def main():
    bot = Bot(token=settings.bot_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
