from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.models import Friend, Invite, Meal, Score, User
from app.schemas.schemas import DailySummary
from app.services.nutrition import seven_day_average, upsert_daily_score


def get_or_create_user(db: Session, telegram_id: int, full_name: str, username: str | None, inviter_telegram_id: int | None = None) -> User:
    user = db.query(User).filter_by(telegram_id=telegram_id).one_or_none()
    if user:
        return user

    inviter = None
    if inviter_telegram_id:
        inviter = db.query(User).filter_by(telegram_id=inviter_telegram_id).one_or_none()

    user = User(telegram_id=telegram_id, full_name=full_name, username=username, inviter_id=inviter.id if inviter else None)
    db.add(user)
    db.flush()

    if inviter:
        db.add(Invite(inviter_id=inviter.id, new_user_id=user.id))
        db.add(Friend(user_id=user.id, friend_id=inviter.id))
        db.add(Friend(user_id=inviter.id, friend_id=user.id))

    db.commit()
    return user


def add_meal(db: Session, user: User, description: str, calories: float, protein: float, carbs: float, fats: float):
    db.add(Meal(user_id=user.id, date=date.today(), food_description=description, calories=calories, protein=protein, carbs=carbs, fats=fats))
    db.commit()
    upsert_daily_score(db, user, date.today())


def delete_last_meal(db: Session, user: User) -> bool:
    meal = db.query(Meal).filter(Meal.user_id == user.id).order_by(desc(Meal.created_at)).first()
    if not meal:
        return False
    db.delete(meal)
    db.commit()
    upsert_daily_score(db, user, date.today())
    return True


def get_daily_summary(db: Session, user: User, day: date | None = None) -> DailySummary:
    day = day or date.today()
    totals = db.query(
        func.coalesce(func.sum(Meal.calories), 0.0),
        func.coalesce(func.sum(Meal.protein), 0.0),
        func.coalesce(func.sum(Meal.carbs), 0.0),
        func.coalesce(func.sum(Meal.fats), 0.0),
    ).filter(Meal.user_id == user.id, Meal.date == day).one()
    upsert_daily_score(db, user, day)
    score = db.query(Score).filter(Score.user_id == user.id, Score.date == day).one()

    return DailySummary(
        date=day,
        calories=round(totals[0], 1),
        protein=round(totals[1], 1),
        carbs=round(totals[2], 1),
        fats=round(totals[3], 1),
        calorie_target=user.calorie_target,
        protein_target=user.protein_target,
        carb_target=user.carb_target,
        fat_target=user.fat_target,
        remaining_calories=round(user.calorie_target - totals[0], 1),
        score=score.score,
    )


def friend_leaderboard(db: Session, user: User):
    friend_ids = [f.friend_id for f in db.query(Friend).filter(Friend.user_id == user.id).all()] + [user.id]
    users = db.query(User).filter(User.id.in_(friend_ids)).all()
    ranking = sorted([
        {'name': u.full_name, 'score': seven_day_average(db, u.id)} for u in users
    ], key=lambda x: x['score'], reverse=True)
    return ranking


def global_leaderboard(db: Session, limit: int = 50):
    users = db.query(User).all()
    ranking = sorted([
        {'name': u.full_name, 'score': seven_day_average(db, u.id)} for u in users
    ], key=lambda x: x['score'], reverse=True)
    return ranking[:limit]


def weekly_calories(db: Session, user: User):
    rows = []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        cals = db.query(func.coalesce(func.sum(Meal.calories), 0.0)).filter(Meal.user_id == user.id, Meal.date == day).scalar()
        rows.append({'date': day.isoformat(), 'calories': round(float(cals or 0.0), 1)})
    return rows
