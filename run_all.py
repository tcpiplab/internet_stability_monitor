import subprocess
import sys


def run_script(script_name):
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running {script_name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Starting monitor.py...")
    run_script("monitor.py")

    print("monitor.py completed. Starting process_logs.py...")
    run_script("process_logs.py")

    print("All scripts completed successfully.")
