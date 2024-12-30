import os
import re

def get_installed_packages():
    with open('requirements.txt', 'r') as file:
        packages = [line.split('==')[0].split('~')[0].strip() for line in file]
    return [package.lower() for package in packages]

def find_imports_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    return re.findall(r'^\s*import (\S+)|^\s*from (\S+) import', content, re.MULTILINE)

def find_unused_packages():
    installed_packages = get_installed_packages()
    imported_packages = set()

    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = find_imports_in_file(file_path)
                for imp in imports:
                    imported_packages.update(filter(None, imp))

    unused_packages = set(installed_packages) - {pkg.lower() for pkg in imported_packages}
    return unused_packages

if __name__ == "__main__":
    unused_packages = find_unused_packages()
    if unused_packages:
        print("Unused packages found in requirements.txt:")
        for package in unused_packages:
            print(f"- {package}")
    else:
        print("No unused packages found.")
