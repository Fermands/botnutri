from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Meal, Score, User

ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

GOAL_MULTIPLIERS = {
    'lose': 0.8,
    'maintain': 1.0,
    'bulk': 1.15,
}


def calculate_targets(weight: float, height: float, age: int, gender: str, activity_level: str, goal: str):
    s = 5 if gender.lower() == 'male' else -161
    bmr = (10 * weight) + (6.25 * height) - (5 * age) + s
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    calories = round(tdee * GOAL_MULTIPLIERS.get(goal, 1.0))

    protein_g = round((calories * 0.3) / 4)
    fats_g = round((calories * 0.25) / 9)
    carbs_g = round((calories - protein_g * 4 - fats_g * 9) / 4)
    return calories, protein_g, carbs_g, fats_g


def upsert_daily_score(db: Session, user: User, day: date):
    totals = db.query(
        func.coalesce(func.sum(Meal.calories), 0.0),
        func.coalesce(func.sum(Meal.protein), 0.0),
        func.coalesce(func.sum(Meal.carbs), 0.0),
        func.coalesce(func.sum(Meal.fats), 0.0),
    ).filter(Meal.user_id == user.id, Meal.date == day).one()

    cal_progress = min(100.0, (totals[0] / max(user.calorie_target, 1)) * 100)
    protein_progress = min(100.0, (totals[1] / max(user.protein_target, 1)) * 100)
    carb_progress = min(100.0, (totals[2] / max(user.carb_target, 1)) * 100)
    fat_progress = min(100.0, (totals[3] / max(user.fat_target, 1)) * 100)
    score = round((cal_progress + protein_progress + carb_progress + fat_progress) / 4, 1)

    existing = db.query(Score).filter(Score.user_id == user.id, Score.date == day).one_or_none()
    if existing:
        existing.score = score
        existing.calorie_progress = cal_progress
        existing.protein_progress = protein_progress
        existing.carb_progress = carb_progress
        existing.fat_progress = fat_progress
    else:
        db.add(Score(
            user_id=user.id,
            date=day,
            score=score,
            calorie_progress=cal_progress,
            protein_progress=protein_progress,
            carb_progress=carb_progress,
            fat_progress=fat_progress,
        ))
    db.commit()


def seven_day_average(db: Session, user_id: int) -> float:
    start = date.today() - timedelta(days=6)
    value = db.query(func.coalesce(func.avg(Score.score), 0.0)).filter(
        Score.user_id == user_id,
        Score.date >= start,
    ).scalar()
    return round(float(value or 0.0), 1)
