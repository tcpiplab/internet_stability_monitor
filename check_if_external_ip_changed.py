import argparse
import os
from datetime import datetime
from colorama import init, Fore, Style


def did_external_ip_change(current_external_ip):
    """
    Check if the external IP address has changed since the last run.
    If it has, print a message to the console.

    :param current_external_ip: The current external IP address

    :return: str: A message explaining if the IP address has changed and if so, what the new IP address is and what the old one was
    """

    # If this function was called directly as an import from another script,
    # the current external IP address must have been passed in as an argument
    # If this function was called with no arguments, return a message to the console and exit
    if not current_external_ip:

        no_input_error_message = (f"{Fore.RED}Can not check if the external IP address has changed because did_external_ip_change() "
              f"was called without providing the current external IP address as an input argument. "
              f"Exiting.{Style.RESET_ALL}")

        print(no_input_error_message)

        return no_input_error_message

    # Check if the file exists from the previous run and compare the IP address
    if os.path.exists('/tmp/ip_address.txt'):
        with open('/tmp/ip_address.txt', 'r') as file:

            # Read the previous timestamp and external IP address from the file
            previous_external_ip_and_timestamp = file.read().strip()

            previous_external_ip = previous_external_ip_and_timestamp.split(',')[1].strip()

            # Also check the timestamp saved with the IP address last time
            previous_external_ip_timestamp = previous_external_ip_and_timestamp.split(',')[0].strip()

        if current_external_ip != previous_external_ip:

            ip_did_change_message = (f"IP address has changed from {previous_external_ip} to {current_external_ip}. "
                                     f"The change occurred some time at or before {previous_external_ip_timestamp}.")

            save_current_external_ip(current_external_ip)

            print(ip_did_change_message)

            return ip_did_change_message


        else:

            ip_has_not_changed_message = (f"IP address has not changed. It is still {current_external_ip}. The last "
                                          f"change occurred at or before {previous_external_ip_timestamp}.")

            save_current_external_ip(current_external_ip)

            print(ip_has_not_changed_message)

            return ip_has_not_changed_message



def save_current_external_ip(current_external_ip):
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
