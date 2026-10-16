import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import config

logger = logging.getLogger(__name__)

class LeadAnalysis(BaseModel):
    is_client_request: bool = Field(
        description="True if the message is from a CLIENT/CUSTOMER looking to hire, buy, or get a service done. False if it's a candidate looking for a job, spam, announcement, advertisement of services, or off-topic chat."
    )
    relevance_score: int = Field(
        description="Score from 0 to 100 based on how closely the request matches our services."
    )
    summary: str = Field(
        description="Short 1-2 sentence Ukrainian summary of what the client actually needs."
    )
    suggested_pitch: str = Field(
        description="Professional, friendly, and persuasive 2-4 sentence direct pitch in Ukrainian responding directly to the client's problem, explaining why we can solve it quickly and suggesting a brief chat."
    )

class AIAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = "gemini-3.5-flash-lite"

    def analyze_message(self, text: str) -> LeadAnalysis:
        # Швидкий пре-фільтр на сміття / короткі повідомлення
        if not text or len(text.strip()) < 15:
            return LeadAnalysis(
                is_client_request=False,
                relevance_score=0,
                summary="Занадто коротке повідомлення",
                suggested_pitch=""
            )

        prompt = f"""
Ти — експертний ШІ-аналітик лідогенерації для IT/Digital-агенції.
Наші послуги:
{config.OUR_SERVICES_DESCRIPTION}

Твоє завдання — проаналізувати повідомлення з публічного Telegram-чату:
1. Визначити чи це РЕАЛЬНЕ ТЕХНІЧНЕ/IT ЗАМОВЛЕННЯ (хтось шукає розробника, замовити Telegram-бота, написати сайт, скрипт, парсер, веб-сервіс, автоматизацію).
2. СУВОРО ВІДСІЯТИ:
   - Розмиті запитання без конкретики ("хто допоможе", "у кого є тема", "напишіть в лс", "є питання").
   - Арбітраж, схеми заробітку, темки, крипту, залив трафіку, пошук дропів/карток.
   - Кандидатів, які шукають роботу ("шукаю роботу", "#резюме", "я розробник", "junior python").
   - Спам, рекламу каналів/курсів, пропозиції послуг від інших розробників.
   - Звичайний флуд та обговорення.
3. Оцінити релевантність від 0 до 100%. Якщо немає чіткого наміру розробити щось технічне — став релевантність менше 50%.
4. Якщо це РЕАЛЬНИЙ клієнт із конкретним завданням — написати лаконічний підсумок (summary) та професійний, дружній pitch українською мовою.

Текст повідомлення:
\"\"\"{text}\"\"\"
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LeadAnalysis,
                    temperature=0.2,
                )
            )
            data = json.loads(response.text)
            return LeadAnalysis(**data)
        except Exception as e:
            logger.error(f"Помилка аналізу через Gemini: {e}")
            return LeadAnalysis(
                is_client_request=False,
                relevance_score=0,
                summary=f"Помилка аналізу: {e}",
                suggested_pitch=""
            )
