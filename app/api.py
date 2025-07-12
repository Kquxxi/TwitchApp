import os
import subprocess

def update_streamers():
    # wywołujemy oryginalny main.py z katalogu wyżej
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
    result = subprocess.run(
        ['python', script],
        capture_output=True, text=True, check=True
    )
    return result.stdout

def generate_report():
    result = subprocess.run(
        ['python', 'app/generate_report.py'],
        capture_output=True, text=True, check=True
    )
    return result.stdout
