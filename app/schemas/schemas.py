from datetime import date

from pydantic import BaseModel


class MealCreate(BaseModel):
    food_description: str
    calories: float
    protein: float
    carbs: float
    fats: float


class NutritionParseResult(BaseModel):
    food_name: str
    portion: str
    calories: float
    protein: float
    carbs: float
    fats: float


class DailySummary(BaseModel):
    date: date
    calories: float
    protein: float
    carbs: float
    fats: float
    calorie_target: int
    protein_target: int
    carb_target: int
    fat_target: int
    remaining_calories: float
    score: float


class DashboardPayload(BaseModel):
    today: DailySummary
    weekly_calories: list[dict]
    macro_distribution: dict
    friend_leaderboard: list[dict]
