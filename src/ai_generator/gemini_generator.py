# AI Generator Module - Gemini AI integration for project generation
import google.generativeai as genai
from config import GEMINI_API_KEY
import json

genai.configure(api_key=GEMINI_API_KEY)

class ProjectGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_project(self, project_name: str, description: str) -> dict:
        """
        Generate a complete project structure based on description.
        Returns a dictionary with files and their contents.
        """
        prompt = f"""
You are an expert software architect. Generate a complete, production-ready project based on this description:

Project Name: {project_name}
Description: {description}

Create a comprehensive project with:
1. All necessary files and directories
2. Complete, working code
3. Configuration files
4. README documentation
5. Requirements or dependencies file

Return the response in this exact JSON format:
{{
    "project_name": "{project_name}",
    "structure": {{
        "file_path": "content",
        "directory/file_path": "content",
        ...
    }},
    "summary": "Brief summary of what was generated"
}}

Important:
- Include ALL files needed for the project to work
- Code should be complete and functional
- Include proper comments in code
- Make realistic, practical projects
- Use appropriate programming languages and frameworks
- Include setup/installation instructions in README
"""
        
        response = self.model.generate_content(prompt)
        
        try:
            # Extract JSON from response
            response_text = response.text
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response: {response.text}")
            return {
                "project_name": project_name,
                "structure": {
                    "README.md": f"# {project_name}\n\n{description}\n\nProject structure to be generated.",
                    ".gitignore": "*.pyc\n__pycache__/\n.env\n.venv/\n"
                },
                "summary": "Error in generation, basic structure created"
            }
    
    def generate_project_files(self, project_name: str, description: str) -> dict:
        """
        Wrapper method to generate project files.
        """
        return self.generate_project(project_name, description)

# Initialize generator
generator = ProjectGenerator()
