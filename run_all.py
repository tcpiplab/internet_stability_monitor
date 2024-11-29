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
    polite_mode = '--polite' in sys.argv
    script_args = []
    if silent_mode:
        script_args.append('--silent')
    if polite_mode:
        script_args.append('--polite')

    print("Starting monitor.py with options:", script_args)
    run_script("monitor.py", script_args)

    print("monitor.py completed. Starting process_logs.py with options:", script_args)
    run_script("process_logs.py", script_args)

    print("All scripts completed successfully.")
