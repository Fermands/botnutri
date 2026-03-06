from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import Base, engine, get_db
from app.models.models import User
from app.schemas.schemas import DashboardPayload, MealCreate
from app.services.app_logic import add_meal, friend_leaderboard, get_daily_summary, weekly_calories

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory='app/templates')
app.mount('/static', StaticFiles(directory='app/dashboard/static'), name='static')


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/api/users/{telegram_id}/meals')
def create_meal(telegram_id: int, meal: MealCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if not user:
        raise HTTPException(404, 'User not found')
    add_meal(db, user, meal.food_description, meal.calories, meal.protein, meal.carbs, meal.fats)
    return {'ok': True}


@app.get('/api/users/{telegram_id}/summary')
def summary(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if not user:
        raise HTTPException(404, 'User not found')
    return get_daily_summary(db, user, date.today())


@app.get('/api/users/{telegram_id}/dashboard-data', response_model=DashboardPayload)
def dashboard_data(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if not user:
        raise HTTPException(404, 'User not found')
    today = get_daily_summary(db, user, date.today())
    return {
        'today': today,
        'weekly_calories': weekly_calories(db, user),
        'macro_distribution': {
            'protein': today.protein,
            'carbs': today.carbs,
            'fats': today.fats,
        },
        'friend_leaderboard': friend_leaderboard(db, user),
    }


@app.get('/dashboard', response_class=HTMLResponse)
def dashboard_page(request: Request, user_id: int = Query(...)):
    return templates.TemplateResponse('dashboard.html', {'request': request, 'user_id': user_id, 'base_url': settings.base_url})
