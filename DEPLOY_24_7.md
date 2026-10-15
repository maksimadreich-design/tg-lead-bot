# Як розгорнути сервіс у хмарі (щоб працював 24/7 при вимкненому ПК)

Найпростіший і найнадійніший спосіб — запустити на недорогому віртуальному сервері (VPS) на базі Linux (Ubuntu), наприклад на **Hetzner** (~4 євро/міс) або **DigitalOcean / Railway**.

### Кроки для запуску на сервері:

1. **Скопіювати файли проєкту на сервер:**
   * Всі файли з поточної папки, включаючи `.env` та створений файл сесії `userbot_session.session`.
   * Завдяки тому, що сесія вже авторизована, вводити SMS-код на сервері **не потрібно**!

2. **Встановити залежності на сервері:**
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Налаштувати фонову службу 24/7 (systemd):**
   Створити файл `/etc/systemd/system/leadbot.service`:
   ```ini
   [Unit]
   Description=Telegram Lead Bot 24/7
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/quirky-pasteur
   ExecStart=/root/quirky-pasteur/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Активувати та запустити:**
   ```bash
   systemctl daemon-reload
   systemctl enable leadbot
   systemctl start leadbot
   ```
   *Тепер бот працює цілодобово, автоматично перезавантажується при збоях чи перезапуску сервера.*
