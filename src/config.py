# Config Module - Environment and Settings Management
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Gemini AI API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Admin User IDs
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv('ADMIN_IDS', '').split(',') if admin_id.strip()]

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///project_bot.db')

# Storage
PROJECTS_STORAGE_DIR = os.getenv('PROJECTS_STORAGE_DIR', './projects_storage')

# Validate required configurations
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS not found in environment variables")

# Create storage directory if not exists
os.makedirs(PROJECTS_STORAGE_DIR, exist_ok=True)
