import subprocess
import sys


def run_script(script_name, args=None):
    try:
        subprocess.run([sys.executable, script_name] + args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running {script_name}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    silent_mode = '--silent' in sys.argv
    script_args = ['--silent'] if silent_mode else []

    print("Starting monitor.py...")
    run_script("monitor.py", script_args)

    print("monitor.py completed. Starting process_logs.py...")
    run_script("process_logs.py", script_args)

    print("All scripts completed successfully.")
