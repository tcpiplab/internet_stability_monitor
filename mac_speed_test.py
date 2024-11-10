import subprocess
import sys

def run_network_quality_test():
    try:
        # Check if running on macOS
        if sys.platform != "darwin":
            print("This script only works on macOS")
            sys.exit(1)

        # Run the networkQuality command
        process = subprocess.run(
            ["networkQuality", "-p", "-s"],
            capture_output=True,
            text=True
        )

        # Print the output
        if process.stdout:
            print("Broadband speed test results from our current location:")
            print(process.stdout)

        # Print any errors
        # if process.stderr:
        #     print("Errors:")
        #     print(process.stderr)

        # Return the exit code
        # return process.returncode

    except FileNotFoundError:
        print("Error: networkQuality command not found. This script requires macOS 12 (Monterey) or later.")
        # return 1
    except subprocess.SubprocessError as e:
        print(f"Error running networkQuality command: {e}")
        # return 1

if __name__ == "__main__":
    run_network_quality_test()
    # exit_code = run_network_quality_test()
    # sys.exit(exit_code)
