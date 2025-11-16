# Project Viewing and Management Handlers
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from database.models import SessionLocal
from database.crud import UserService, ProjectService
from utils.storage import StorageManager
from datetime import datetime
import os

async def view_user_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display user's projects."""
    if update.callback_query:
        await update.callback_query.answer()
        user_id = update.effective_user.id
        chat_id = update.callback_query.message.chat_id
    else:
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
    
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, user_id)
    
    if not user:
        await update.callback_query.edit_message_text("❌ User not found.")
        db.close()
        return
    
    projects = ProjectService.get_user_projects(db, user.id)
    
    if not projects:
        text = "📂 *Your Projects*\n\nYou haven't created any projects yet.\n\nClick below to create your first project!"
        keyboard = [
            [InlineKeyboardButton("➕ Create Project", callback_data="create_project")],
            [InlineKeyboardButton("◀️ Back", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        db.close()
        return
    
    # Build projects list
    text = "📂 *Your Projects*\n\n"
    keyboard = []
    
    for idx, project in enumerate(projects, 1):
        created_date = project.created_at.strftime("%d/%m/%Y")
        text += f"{idx}. *{project.name}*\n   📅 Created: {created_date}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(f"📥 {project.name}", callback_data=f"download_project_{project.id}"),
            InlineKeyboardButton("ℹ️", callback_data=f"project_info_{project.id}"),
        ])
    
    storage_size = StorageManager.get_user_projects_size(user.id)
    text += f"\n📊 *Total Storage:* {storage_size}"
    
    keyboard.append([InlineKeyboardButton("➕ Create New Project", callback_data="create_project")])
    keyboard.append([InlineKeyboardButton("◀️ Back", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    db.close()

async def show_project_info(update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: int) -> None:
    """Show project information."""
    if update.callback_query:
        await update.callback_query.answer()
    
    db = SessionLocal()
    project = ProjectService.get_project(db, project_id)
    
    if not project:
        await update.callback_query.edit_message_text("❌ Project not found.")
        db.close()
        return
    
    created_date = project.created_at.strftime("%d/%m/%Y %H:%M")
    
    # Calculate project size
    if os.path.exists(project.file_path):
        size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(project.file_path)
            for filename in filenames
        )
        size_mb = size / (1024 * 1024)
        size_text = f"{size_mb:.2f} MB"
    else:
        size_text = "Unknown"
    
    text = f"""
📋 *Project Information*

*Name:* {project.name}
📅 *Created:* {created_date}
💾 *Size:* {size_text}

*Description:*
{project.description}
"""
    
    keyboard = [
        [InlineKeyboardButton("📥 Download", callback_data=f"download_project_{project.id}")],
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_project_{project.id}")],
        [InlineKeyboardButton("◀️ Back", callback_data="view_projects")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    db.close()

async def download_project(update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: int) -> None:
    """Download project as ZIP file."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    
    db = SessionLocal()
    project = ProjectService.get_project(db, project_id)
    
    if not project:
        await update.callback_query.edit_message_text("❌ Project not found.")
        db.close()
        return
    
    # Check if ZIP exists
    if not project.zip_path or not os.path.exists(project.zip_path):
        # Try to create ZIP
        zip_path = StorageManager.compress_project(project.file_path)
        if zip_path:
            ProjectService.update_project_zip(db, project.id, zip_path)
            db.commit()
            project.zip_path = zip_path
        else:
            await update.callback_query.edit_message_text("❌ Error preparing project for download.")
            db.close()
            return
    
    try:
        # Send file
        file = FSInputFile(project.zip_path)
        await update.callback_query.message.chat.send_document(
            file,
            caption=f"📦 {project.name}.zip",
        )
        
        # Edit message
        keyboard = [
            [InlineKeyboardButton("📂 View My Projects", callback_data="view_projects")],
            [InlineKeyboardButton("➕ Create Another", callback_data="create_project")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"✅ *Download Successful!*\n\nProject *{project.name}* has been sent as a ZIP file.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error sending file: {e}")
        await update.callback_query.edit_message_text(f"❌ Error sending file: {str(e)}")
    
    db.close()

async def delete_project_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: int) -> None:
    """Confirm project deletion."""
    if update.callback_query:
        await update.callback_query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{project_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"project_info_{project_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "⚠️ *Are you sure you want to delete this project?*\n\nThis action cannot be undone!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE, project_id: int) -> None:
    """Delete project."""
    if update.callback_query:
        await update.callback_query.answer()
    
    db = SessionLocal()
    project = ProjectService.get_project(db, project_id)
    
    if not project:
        await update.callback_query.edit_message_text("❌ Project not found.")
        db.close()
        return
    
    # Delete files
    StorageManager.delete_project_directory(project.file_path)
    
    # Delete from database
    ProjectService.delete_project(db, project_id)
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("📂 View Projects", callback_data="view_projects")],
        [InlineKeyboardButton("➕ Create Project", callback_data="create_project")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "✅ *Project Deleted*\n\nThe project has been permanently deleted.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
