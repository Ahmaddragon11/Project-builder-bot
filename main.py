import logging
import os
import asyncio
import json # Added for parsing AI response
import shutil # Added for project cleanup

from telegram import Update, ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.config import TELEGRAM_BOT_TOKEN
from src.ai_service import AIService
from src.project_manager import ProjectManager

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Store user project data temporarily
user_projects = {}

# Initialize services globally or pass them around
ai_service = AIService()
project_manager = ProjectManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('مرحباً بك في بوت إنشاء المشاريع بالذكاء الاصطناعي! أرسل لي /newproject لبدء مشروع جديد.')

async def new_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initiate a new project creation flow."""
    chat_id = update.message.chat_id
    user_projects[chat_id] = {'state': 'awaiting_name'}
    await update.message.reply_text('أهلاً بك! ما هو اسم مشروعك؟')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "أهلاً بك في بوت إنشاء المشاريع بالذكاء الاصطناعي!\n\n"
        "يمكنني مساعدتك في إنشاء مشاريع برمجية متنوعة بناءً على وصفك.\n\n"
        "الأوامر المتاحة:\n"
        "/start - لبدء التفاعل مع البوت.\n"
        "/newproject - لبدء عملية إنشاء مشروع جديد.\n"
        "/help - لعرض هذه الرسالة المساعدة.\n\n"
        "لبدء مشروع جديد، أرسل /newproject وسأطلب منك اسم المشروع ووصفه. "
        "سأقوم بعد ذلك بإنشاء المشروع وإرساله إليك كملف مضغوط."
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages for project creation."""
    chat_id = update.message.chat_id
    text = update.message.text

    if chat_id in user_projects:
        if user_projects[chat_id]['state'] == 'awaiting_name':
            user_projects[chat_id]['project_name'] = text
            user_projects[chat_id]['state'] = 'awaiting_description'
            await update.message.reply_text(f'تم تعيين اسم المشروع: "{text}". الآن، يرجى إرسال وصف مفصل للمشروع الذي تريده.')
        elif user_projects[chat_id]['state'] == 'awaiting_description':
            user_projects[chat_id]['project_description'] = text
            user_projects[chat_id]['state'] = 'processing'
            await update.message.reply_text(f'شكراً لك! مشروعك "{user_projects[chat_id]["project_name"]}" قيد الإنشاء الآن. قد يستغرق هذا بعض الوقت...')
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # --- AI Integration and Project Creation Logic ---
            project_name = user_projects[chat_id]['project_name']
            project_description = user_projects[chat_id]['project_description']
            project_path = None
            zip_file_path = None

            try:
                project_details = await ai_service.generate_project_content(project_name, project_description)
                project_path = await project_manager.create_project_files(project_name, project_details)
                zip_file_path = await project_manager.zip_project(project_path)

                # Send the zipped project and details to the user
                with open(zip_file_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        caption=f'مشروعك "{project_name}" جاهز!\n\nالوصف:\n{project_description}\n\nتفاصيل إضافية:\n{project_details.get("additional_info", "لا توجد تفاصيل إضافية.")}'
                    )

                await update.message.reply_text('تم إرسال مشروعك بنجاح!')

            except Exception as e:
                logger.error("Error during project creation: %s", e)
                await update.message.reply_text('عذراً، حدث خطأ أثناء إنشاء مشروعك. يرجى المحاولة مرة أخرى لاحقاً.')
            finally:
                # Clear user state
                if chat_id in user_projects:
                    del user_projects[chat_id]
                # Clean up project files if they were created
                if project_path and zip_file_path:
                    project_manager.clean_up_project_files(project_path, zip_file_path)
                elif project_path: # If zipping failed but files were created
                    shutil.rmtree(project_path)
                    logger.info(f"Removed project directory: {project_path}")
    else:
        await update.message.reply_text('أنا هنا لإنشاء المشاريع! أرسل /newproject لبدء مشروع جديد.')

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newproject", new_project))
    application.add_handler(CommandHandler("help", help_command))

    # On non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
