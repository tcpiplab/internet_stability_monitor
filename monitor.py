import os
import sys
import subprocess
import logging
from datetime import datetime

# Set up the logging directory under /tmp
log_directory = "/tmp/internet_stability_monitor_logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Generate a log file name with the current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file_path = os.path.join(log_directory, f"internet_stability_log_{timestamp}.txt")

# Configure logging
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Function to run each script and log output
def run_script(script_name):

    separator = "=" * 80

    try:
        result = subprocess.run(
            ["python3", script_name],
            capture_output=True,
            text=True,
            check=True,
        )

    #     logging.info(f"Output of {script_name}:\n{result.stdout}\n{separator}\n")
    # except subprocess.CalledProcessError as e:
    #     logging.error(f"Error running {script_name}:\n{e.stderr}\n{separator}\n")

        output = f"Output of {script_name}:\n{result.stdout}\n{separator}\n"
            
        # Log to file
        logging.info(output)
        
        # Print to STDOUT
        print(output, file=sys.stdout)

    except subprocess.CalledProcessError as e:
        error_output = f"Error running {script_name}:\n{e.stderr}\n{separator}\n"
        
        # Log error to file
        logging.error(error_output)
        
        # Print error to STDOUT
        print(error_output, file=sys.stderr)


def main():
    scripts = [
        "check_local_os.py",
        "check_unifi_api.py",
        "mac_speed_test.py",
        "resolver_check.py",
        "whois_check.py",
        "dns_check.py",
        "ntp_check.py",
        "web_check.py",
        "cloud_check.py",
        "imap_check.py",
        "smtp_check.py",
        "tls_ca_check.py",
        "cdn_check.py",
        # "bgp_ripe_ris_check.py", (removed because still too verbose)
        "ixp_check.py",
    ]

    print("Starting report on critical internet infrastructure...")
    print(f"Tests were started at {datetime.now().isoformat()}")

    for script in scripts:

        print(f"Running {script}...")
        run_script(script)
        print(f"{script} completed.")
        
        # Sleep 5 seconds between scripts to be polite        
        print("Sleeping for 5 seconds before next script...")
        subprocess.run(["sleep", "5"])

if __name__ == "__main__":
    main()