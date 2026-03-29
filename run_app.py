import subprocess
import sys
import os

def run_streamlit_app():
    project_dir = os.path.dirname(os.path.abspath(__file__))

    python_exe = os.path.join(project_dir, ".venv", "Scripts", "python.exe")
    streamlit_cmd = [
        python_exe,
        "-m",
        "streamlit",
        "run",
        "main.py"
    ]

    subprocess.run(streamlit_cmd, cwd=project_dir)

if __name__ == "__main__":
    run_streamlit_app()
