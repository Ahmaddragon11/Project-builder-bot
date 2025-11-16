from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction
from src.database.crud import (
    get_all_users, get_all_projects, get_user_projects,
    get_user_by_id, delete_project, toggle_feature
)
from src.config import ADMIN_IDS

# Admin conversation states
ADMIN_MENU, VIEW_USERS, VIEW_PROJECTS, MANAGE_SETTINGS = range(4)

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show admin menu"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You don't have admin access.")
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("👥 View All Users", callback_data="admin_users")],
        [InlineKeyboardButton("📁 View All Projects", callback_data="admin_projects")],
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔐 <b>Admin Panel</b>\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return ADMIN_MENU

async def view_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display all users"""
    query = update.callback_query
    await query.answer()
    
    users = get_all_users()
    
    if not users:
        await query.edit_message_text("📭 No users found.")
        return VIEW_USERS
    
    message = "<b>👥 All Users:</b>\n\n"
    for user in users:
        message += f"• <b>{user.username}</b> (ID: <code>{user.telegram_id}</code>)\n"
        message += f"  Projects: {len(user.projects)}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return VIEW_USERS

async def view_all_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display all projects"""
    query = update.callback_query
    await query.answer()
    
    projects = get_all_projects()
    
    if not projects:
        await query.edit_message_text("📭 No projects found.")
        return VIEW_PROJECTS
    
    message = "<b>📁 All Projects:</b>\n\n"
    for project in projects:
        user = get_user_by_id(project.user_id)
        message += f"• <b>{project.name}</b>\n"
        message += f"  Owner: {user.username}\n"
        message += f"  Created: {project.created_at.strftime('%Y-%m-%d')}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return VIEW_PROJECTS

async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show bot settings"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Toggle Project Generation", callback_data="toggle_generation")],
        [InlineKeyboardButton("🔄 Toggle Project Viewing", callback_data="toggle_viewing")],
        [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "<b>⚙️ Bot Settings</b>\n\nToggle features on/off:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return MANAGE_SETTINGS

async def toggle_generation_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle project generation feature"""
    query = update.callback_query
    await query.answer()
    
    # Toggle the feature (this would be stored in database)
    toggle_feature("project_generation")
    await query.edit_message_text("✅ Project generation feature toggled!")
    
    return MANAGE_SETTINGS

async def toggle_viewing_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggle project viewing feature"""
    query = update.callback_query
    await query.answer()
    
    toggle_feature("project_viewing")
    await query.edit_message_text("✅ Project viewing feature toggled!")
    
    return MANAGE_SETTINGS

async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to admin menu"""
    return await admin_menu(update, context)
