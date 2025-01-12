import argparse
import os
from datetime import datetime
from colorama import init, Fore, Style


def did_external_ip_change(current_external_ip):
    """
    Check if the external IP address has changed since the last run.
    If it has, print a message to the console.

    :param current_external_ip: The current external IP address

    :return: None
    """

    # If this function was called directly as an import from another script,
    # the current external IP address must have been passed in as an argument
    # If this function was called with no arguments, return a message to the console and exit
    if not current_external_ip:

        print(f"{Fore.RED}Can not check if the external IP address has changed because did_external_ip_change() "
              f"was called without providing the current external IP address as an input argument. "
              f"Exiting.{Style.RESET_ALL}")
        return

    # Check if the file exists from the previous run and compare the IP address
    if os.path.exists('/tmp/ip_address.txt'):
        with open('/tmp/ip_address.txt', 'r') as file:
            previous_external_ip = file.read().split(',')[1].strip()

        if current_external_ip != previous_external_ip:
            print(f"IP address has changed from {previous_external_ip} to {current_external_ip}")

            # TODO check the timestamp saved with the IP address last time

        else:
            print("IP address has not changed.")

    # Save the current external IP address to a file with today's date and time, separated by a comma
    today_date_and_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    with open('/tmp/ip_address.txt', 'w') as file:
        file.write(f"{today_date_and_timestamp},{current_external_ip}")


if __name__ == "__main__":
    # Initialize colorama
    init(autoreset=True)

    # If this script is run directly, the current external IP address must have been passed in as an argument
    # Set the current external IP address to the value passed in as an argument
    argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument("current_external_ip", help="The current external IP address")
    args = parser.parse_args()

    # Check if the external IP address has changed
    did_external_ip_change(args.current_external_ip)
