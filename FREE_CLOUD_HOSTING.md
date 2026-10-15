# 🚀 Як безкоштовно запустити бота в хмарі 24/7

Щоб бот працював автономно без увімкненого ПК, є 3 найкращі **безкоштовні** варіанти:

---

## Варіант 1: Render.com (Найпростіший, безкоштовний Background Worker)
1. Створіть акаунт на [Render.com](https://render.com) (через GitHub або Email).
2. Створіть новий приватний репозиторій на [GitHub](https://github.com) і завантажте туди всі файли з вашої папки `c:\Users\resur\Documents\antigravity\quirky-pasteur` (включаючи `userbot_session.session`, щоб не вводити код).
3. На Render натисніть **New +** ➡️ **Background Worker**.
4. Підключіть ваш GitHub репозиторій.
5. У налаштуваннях:
   - **Environment:** `Python 3` або `Docker`
   - **Start Command:** `python main.py`
   - **Plan:** `Free`
6. У розділі **Environment Variables** додайте значення з вашого файлу `.env` (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `BOT_TOKEN`, `GEMINI_API_KEY`, `ADMIN_TELEGRAM_ID`).
7. Натисніть **Deploy**. Все, бот працює в хмарі цілодобово!

---

## Варіант 2: Oracle Cloud Free Tier (Найпотужніший, безлімітний назавжди)
* Дає повноцінний Linux-сервер 24/7 **назавжди безкоштовно**.
* Потрібна банківська картка для верифікації (списує та повертає 1$).

---

## Варіант 3: Railway.app / Koyeb
* **Koyeb.com** або **Railway.app** дають безкоштовні кредити кожного місяця.
* Підтримують запуск з Dockerfile (я вже створив [`Dockerfile`](file:///c:/Users/resur/Documents/antigravity/quirky-pasteur/Dockerfile) у проєкті).
