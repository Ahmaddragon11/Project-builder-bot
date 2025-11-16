# Start and Main Menu Handlers
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import SessionLocal
from database.crud import UserService
from datetime import datetime

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Welcome message and main menu."""
    user = update.effective_user
    
    # Get or create user in database
    db = SessionLocal()
    db_user = UserService.create_or_get_user(
        db,
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )
    db.close()
    
    # Check if user is banned
    if db_user.is_banned:
        await update.message.reply_text(
            "❌ Sorry, your account has been banned. Please contact support."
        )
        return
    
    welcome_text = f"""
👋 Welcome, {user.first_name}!

I'm an AI-powered project generator bot. I can help you create complete projects based on your descriptions!

With me, you can:
✨ Create new projects with AI
📁 View and manage your projects
📥 Download project files as ZIP

Let's get started! What would you like to do?
"""
    
    keyboard = [
        [InlineKeyboardButton("➕ Create Project", callback_data="create_project")],
        [InlineKeyboardButton("📂 View My Projects", callback_data="view_projects")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
🤖 *Project Builder Bot - Help Guide*

*Available Commands:*
/start - Start the bot and show main menu
/help - Show this help message
/myprojects - View your projects
/settings - User settings

*Features:*

1️⃣ *Create Project*
   - Click "Create Project" button
   - Enter project name and description
   - AI generates complete project structure
   - Download as ZIP file

2️⃣ *View Projects*
   - Click "View My Projects"
   - See all your created projects
   - Download any project as ZIP

3️⃣ *Project Storage*
   - All projects are stored securely
   - Only you can access your projects
   - Download anytime

*Questions?*
Contact support or use /help anytime!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu."""
    keyboard = [
        [InlineKeyboardButton("➕ Create Project", callback_data="create_project")],
        [InlineKeyboardButton("📂 View My Projects", callback_data="view_projects")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📋 *Main Menu*\n\nWhat would you like to do?"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
