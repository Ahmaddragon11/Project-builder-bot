# Callback Handlers - Handle all button clicks
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import SessionLocal
from database.crud import UserService, ProjectService
from handlers.project_view_handler import (
    view_user_projects, show_project_info, download_project, 
    delete_project_confirm, delete_project