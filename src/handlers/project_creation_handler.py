# Project Creation Handlers
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database.models import SessionLocal
from database.crud import UserService, ProjectService
from ai_generator.gemini_generator import generator
from utils.storage import StorageManager
import os

# Conversation states
ASK_PROJECT_NAME, ASK_PROJECT_DESCRIPTION, GENERATING_PROJECT, PROJECT_CREATED = range(4)

async def start_project_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start project creation - Ask for project name."""
    if update.callback_query:
        await update.callback_query.answer()
        chat_id = update.callback_query.message.chat_id
        message_method = update.callback_query.edit_message_text
        
        text = "📝 What would you like to name your project?"
        await message_method(text)
    else:
        chat_id = update.message.chat_id
        text = "📝 What would you like to name your project?"
        await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    
    return ASK_PROJECT_NAME

async def ask_project_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store project name and ask for description."""
    project_name = update.message.text.strip()
    
    if not project_name or len(project_name) < 2:
        await update.message.reply_text("❌ Project name too short. Please enter at least 2 characters.")
        return ASK_PROJECT_NAME
    
    if len(project_name) > 50:
        await update.message.reply_text("❌ Project name too long. Please keep it under 50 characters.")
        return ASK_PROJECT_NAME
    
    context.user_data['project_name'] = project_name
    
    text = f"✅ Great! You named it *{project_name}*\n\n📋 Now, please describe your project in detail. Include:\n• What it does\n• Main features\n• Technology stack (optional)\n• Any special requirements"
    await update.message.reply_text(text, parse_mode='Markdown')
    
    return ASK_PROJECT_DESCRIPTION

async def start_generating_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store description and start generating project."""
    description = update.message.text.strip()
    
    if not description or len(description) < 10:
        await update.message.reply_text("❌ Description too short. Please provide at least 10 characters describing your project.")
        return ASK_PROJECT_DESCRIPTION
    
    context.user_data['project_description'] = description
    
    # Show generating message
    generating_msg = await update.message.reply_text(
        "🚀 *Generating your project...*\n\n⏳ This may take up to 2-3 minutes depending on project complexity.",
        parse_mode='Markdown'
    )
    
    context.user_data['generating_msg_id'] = generating_msg.message_id
    
    # Get user info
    db = SessionLocal()
    user = UserService.get_user_by_telegram_id(db, update.effective_user.id)
    
    project_name = context.user_data['project_name']
    project_description = context.user_data['project_description']
    
    try:
        # Generate project using AI
        project_files = await _generate_project_async(project_name, project_description)
        
        if not project_files or not project_files.get('structure'):
            await update.message.reply_text(
                "❌ Error generating project. Please try again with a different description."
            )
            db.close()
            return ConversationHandler.END
        
        # Save project to database
        project_dir = StorageManager.create_project_directory(user.id, len(user.projects) + 1, project_name)
        
        # Save files
        if not StorageManager.save_project_files(project_dir, project_files['structure']):
            await update.message.reply_text("❌ Error saving project files. Please try again.")
            db.close()
            return ConversationHandler.END
        
        # Create project record in database
        db_project = ProjectService.create_project(
            db,
            user_id=user.id,
            name=project_name,
            description=project_description,
            file_path=project_dir
        )
        
        # Compress project
        zip_path = StorageManager.compress_project(project_dir)
        if zip_path:
            ProjectService.update_project_zip(db, db_project.id, zip_path)
        
        db.commit()
        db.close()
        
        # Edit generating message
        summary = project_files.get('summary', 'Project generated successfully!')
        success_text = f"""
✅ *Project Generated Successfully!*

📦 *Project:* {project_name}
📝 *Summary:* {summary}

Your project is ready to download!
"""
        
        keyboard = [
            [InlineKeyboardButton("📥 Download Project", callback_data=f"download_project_{db_project.id}")],
            [InlineKeyboardButton("📂 View My Projects", callback_data="view_projects")],
            [InlineKeyboardButton("➕ Create Another", callback_data="create_project")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await generating_msg.edit_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        return ConversationHandler.END
        
    except Exception as e:
        print(f"Error in project generation: {e}")
        await update.message.reply_text(
            f"❌ An error occurred while generating the project: {str(e)}\n\nPlease try again."
        )
        db.close()
        return ConversationHandler.END

async def _generate_project_async(project_name: str, description: str) -> dict:
    """Generate project asynchronously."""
    return generator.generate_project_files(project_name, description)

async def cancel_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel project creation."""
    await update.message.reply_text("❌ Project creation cancelled.")
    return ConversationHandler.END

def get_creation_conversation_handler():
    """Get the conversation handler for project creation."""
    from telegram.ext import MessageHandler, filters, CommandHandler
    
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Create Project$"), start_project_creation),
        ],
        states={
            ASK_PROJECT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_project_description)
            ],
            ASK_PROJECT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, start_generating_project)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_creation),
        ],
        allow_reentry=True,
    )
