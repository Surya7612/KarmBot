import os

# Define the project structure
project_name = "karmbot"
directories = [
    f"{project_name}/src",
    f"{project_name}/data/resumes",
    f"{project_name}/data/logs",
    f"{project_name}/config",
    f"{project_name}/tests"
]

files = {
    f"{project_name}/src/__init__.py": "",
    f"{project_name}/src/main.py": "# Entry point for KarmBot\n",
    f"{project_name}/src/job_scraper.py": "# Job scraping module\n",
    f"{project_name}/src/apply_bot.py": "# Application submission module\n",
    f"{project_name}/src/cover_letter.py": "# Cover letter generation module\n",
    f"{project_name}/src/notifier.py": "# Notification system module\n",
    f"{project_name}/config/config.py": "# Configuration file (API keys, settings)\n",
    f"{project_name}/tests/test_scraper.py": "# Unit tests for job scraper\n",
    f"{project_name}/tests/test_apply_bot.py": "# Unit tests for application bot\n",
    f"{project_name}/README.md": "# KarmBot\n\nKarmBot is an automated job application bot...\n",
    f"{project_name}/.gitignore": "# Ignore virtual environment\nkarm/\n\n# Python cache files\n__pycache__/\n*.py[cod]\n\n# Environment files\n.env\n",
    f"{project_name}/LICENSE": ""
}

def create_directories():
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def create_files():
    for file_path, content in files.items():
        # Create directories for the files if they don't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Created file: {file_path}")

if __name__ == "__main__":
    print(f"Setting up the project structure for '{project_name}'...")
    create_directories()
    create_files()
    print(f"Project structure for '{project_name}' has been set up successfully.")
