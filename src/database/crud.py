# Database Operations - CRUD operations for database models
from sqlalchemy.orm import Session
from database.models import User, Project, AdminSettings
from datetime import datetime

class UserService:
    @staticmethod
    def create_or_get_user(db: Session, telegram_id: int, first_name: str, last_name: str = None, username: str = None):
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int):
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    
    @staticmethod
    def get_all_users(db: Session):
        return db.query(User).all()
    
    @staticmethod
    def ban_user(db: Session, telegram_id: int):
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.is_banned = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def unban_user(db: Session, telegram_id: int):
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.is_banned = False
            db.commit()
            return True
        return False

class ProjectService:
    @staticmethod
    def create_project(db: Session, user_id: int, name: str, description: str, file_path: str):
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            file_path=file_path
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def get_user_projects(db: Session, user_id: int):
        return db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()
    
    @staticmethod
    def get_project(db: Session, project_id: int):
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def update_project_zip(db: Session, project_id: int, zip_path: str):
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.zip_path = zip_path
            project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(project)
        return project
    
    @staticmethod
    def get_all_projects(db: Session):
        return db.query(Project).all()
    
    @staticmethod
    def delete_project(db: Session, project_id: int):
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.delete(project)
            db.commit()
            return True
        return False

class SettingsService:
    @staticmethod
    def get_setting(db: Session, key: str):
        setting = db.query(AdminSettings).filter(AdminSettings.key == key).first()
        return setting.value if setting else None
    
    @staticmethod
    def set_setting(db: Session, key: str, value: str):
        setting = db.query(AdminSettings).filter(AdminSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = AdminSettings(key=key, value=value)
            db.add(setting)
        db.commit()
        return setting
    
    @staticmethod
    def get_all_settings(db: Session):
        return db.query(AdminSettings).all()
