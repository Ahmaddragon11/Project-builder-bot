# Storage and Compression Utilities
import os
import zipfile
import shutil
from pathlib import Path
from config import PROJECTS_STORAGE_DIR
from datetime import datetime

class StorageManager:
    @staticmethod
    def create_project_directory(user_id: int, project_id: int, project_name: str) -> str:
        """Create a directory for storing project files."""
        sanitized_name = "".join(c for c in project_name if c.isalnum() or c in ('-', '_')).rstrip()
        project_dir = os.path.join(PROJECTS_STORAGE_DIR, f"user_{user_id}", f"project_{project_id}_{sanitized_name}")
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
    
    @staticmethod
    def save_project_files(project_dir: str, files_structure: dict) -> bool:
        """
        Save project files to the project directory.
        files_structure: dict with file_path as key and content as value
        """
        try:
            for file_path, content in files_structure.items():
                full_path = os.path.join(project_dir, file_path)
                
                # Create parent directories
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return True
        except Exception as e:
            print(f"Error saving project files: {e}")
            return False
    
    @staticmethod
    def compress_project(project_dir: str) -> str:
        """Compress project directory into a ZIP file."""
        try:
            # Create zip filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = os.path.basename(project_dir)
            zip_path = os.path.join(os.path.dirname(project_dir), f"{project_name}_{timestamp}.zip")
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(project_dir))
                        zipf.write(file_path, arcname)
            
            return zip_path
        except Exception as e:
            print(f"Error compressing project: {e}")
            return None
    
    @staticmethod
    def get_user_projects_size(user_id: int) -> str:
        """Get total size of user's projects."""
        user_dir = os.path.join(PROJECTS_STORAGE_DIR, f"user_{user_id}")
        if not os.path.exists(user_dir):
            return "0 MB"
        
        total_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(user_dir)
            for filename in filenames
        )
        
        # Convert to MB
        size_mb = total_size / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    
    @staticmethod
    def delete_project_directory(project_dir: str) -> bool:
        """Delete project directory and all files."""
        try:
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            return True
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
