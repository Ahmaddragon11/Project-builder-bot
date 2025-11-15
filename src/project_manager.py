import os
import zipfile
import shutil
import logging

logger = logging.getLogger(__name__)

class ProjectManager:
    def __init__(self, base_dir='.'):
        self.base_dir = base_dir
        self.projects_root = os.path.join(self.base_dir, 'projects')
        os.makedirs(self.projects_root, exist_ok=True)

    async def create_project_files(self, project_name: str, project_details: dict) -> str:
        """Function to create files and directories based on AI output."""
        project_root = os.path.join(self.projects_root, project_name)
        os.makedirs(project_root, exist_ok=True)
        logger.info(f"Creating project files in: {project_root}")

        for file_path, content in project_details['files'].items():
            full_path = os.path.join(project_root, file_path)
            dir_name = os.path.dirname(full_path)
            os.makedirs(dir_name, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        return project_root

    async def zip_project(self, project_path: str) -> str:
        """Function to zip the created project."""
        output_file_name = f"{os.path.basename(project_path)}.zip"
        output_file_path = os.path.join(self.base_dir, output_file_name)
        logger.info(f"Zipping project from {project_path} to {output_file_path}")

        with zipfile.ZipFile(output_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(project_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    # Calculate relative path inside the zip file
                    arcname = os.path.relpath(file_full_path, os.path.dirname(project_path))
                    zipf.write(file_full_path, arcname)
        return output_file_path

    def clean_up_project_files(self, project_path: str, zip_file_path: str):
        """Clean up temporary project files and zip archive."""
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
            logger.info(f"Removed zip file: {zip_file_path}")
