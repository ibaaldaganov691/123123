import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
DB_PATH = 'tracker.db'

# Для PostgreSQL (если