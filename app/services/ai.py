from __future__ import annotations

import json

from openai import OpenAI

from app.core.config import settings
from app.schemas.schemas import NutritionParseResult

client = OpenAI(api_key=settings.openai_api_key)

NUTRITION_PROMPT = """
You are a clinical nutrition assistant for Uzbekistan users.
Convert user meal text into strict JSON with keys:
food_name, portion, calories, protein, carbs, fats.
Estimate realistic macros for Uzbek and common foods (plov, lagman, samsa, shashlik, manty, non).
Rules:
- output ONLY valid JSON
- calories/protein/carbs/fats must be numbers
- if uncertain, provide best estimate and keep portion explicit
""".strip()


def parse_food_text(text: str) -> NutritionParseResult:
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': NUTRITION_PROMPT},
            {'role': 'user', 'content': text},
        ],
        temperature=0.2,
    )
    data = json.loads(response.choices[0].message.content)
    return NutritionParseResult(**data)


def transcribe_voice(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        res = client.audio.transcriptions.create(model='whisper-1', file=f)
    return res.text


def analyze_food_image(file_path: str) -> NutritionParseResult:
    with open(file_path, 'rb') as image:
        uploaded = client.files.create(file=image, purpose='vision')

    response = client.chat.completions.create(
        model='gpt-4.1-mini',
        response_format={'type': 'json_object'},
        messages=[
            {'role': 'system', 'content': NUTRITION_PROMPT},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'Estimate food and macros from this image.'},
                    {'type': 'image_file', 'image_file': {'file_id': uploaded.id}},
                ],
            },
        ],
    )
    return NutritionParseResult(**json.loads(response.choices[0].message.content))
