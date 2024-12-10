import platform


def get_os_type():
    os_type = platform.system()
    if os_type == "Darwin":
        return "macOS"
    elif os_type == "Windows":
        return "Windows"
    elif os_type == "Linux":
        return "Linux"
    else:
        return "Unknown"


# Set a variable for the OS type at the module level.
# It must be set outside any function or class and outside of main()
# so that the variable can be imported by other scripts
OS_TYPE = get_os_type()


if __name__ == "__main__":

    get_os_type()
