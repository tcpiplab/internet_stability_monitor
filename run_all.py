import subprocess
import sys


def run_script(script_name, args=None):
    try:
        subprocess.run([sys.executable, script_name] + args, check=True)
        return True
    except subprocess.CalledProcessError as e:

        print(f"An error occurred while running {script_name}: {e}")
        return False
        # sys.exit(1)


def main(silent, polite):
    script_args = []
    if silent:
        script_args.append('--silent')
    if polite:
        script_args.append('--polite')

    # Check if Ollama is running and reachable
    if not run_script("check_ollama_status.py", script_args):
        print("Ollama is not running or not reachable. Exiting.")
        sys.exit(1)

    print("Starting monitor.py with options:", script_args)
    run_script("monitor.py", script_args)

    print("monitor.py completed. Starting process_logs.py with options:", script_args)
    run_script("process_logs.py", script_args)

    print("All scripts completed successfully.")


if __name__ == "__main__":
    silent_mode = '--silent' in sys.argv
    polite_mode = '--polite' in sys.argv
    main(silent_mode, polite_mode)
