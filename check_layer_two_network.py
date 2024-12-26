import psutil
import re

def guess_link_type(ifname: str) -> str:
    """
    Guess the local OSI Layer 2 link type based on the interface name.

    Args: str ifname: The name of the network interface.

    Returns: str: The guessed link type. E.g. "Wi-Fi", "Ethernet", "Loopback", "Unknown"
    """

    # This is just a rudimentary guesser based on interface name.
    # It may not hold true for all systems, but it often suffices.

    pattern_wifi = r"(wi-?fi|wlan|wlp|airport)"
    pattern_eth  = r"(eth|en|ethernet)"
    pattern_lo   = r"^(lo)$"

    if re.search(pattern_wifi, ifname, re.IGNORECASE):
        return "Wi-Fi"
    elif re.search(pattern_eth, ifname, re.IGNORECASE):
        return "Ethernet"
    elif re.search(pattern_lo, ifname, re.IGNORECASE):
        return "Loopback"
    else:
        return "Unknown"


def report_link_status_and_type():
    """Report on the OSI Layer 2 network link status.
    This function will print whether the network interfaces are up or down,
    and if they are up, it will also print the link type and speed.

    Returns: str: The link type guess for the last interface.
    """

    link_type_guess = ""

    stats = psutil.net_if_stats()

    for ifname, ifinfo in stats.items():
        # if ifinfo.isup:
        if ifinfo.isup and ifinfo.speed > 0:
            link_type = guess_link_type(ifname)

            link_type_guess = f"Interface {ifname} is up. Link type: {link_type}, Speed: {ifinfo.speed} Mbps"
            print(link_type_guess)

        # else:
        #
        #     link_type_guess = f"Interface {ifname} is down."
        #     print(link_type_guess)

    if link_type_guess == "":
        print("No network interfaces are up.")

    return link_type_guess


if __name__ == "__main__":

    report_link_status_and_type()