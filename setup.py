"""Setup configuration for internet stability monitor."""

from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="internet-stability-monitor",
    version="0.1.0",
    author="Luke Sheppard",
    author_email="luke.sheppard@example.com",
    description="A comprehensive tool for monitoring internet stability and connectivity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/internet_stability_monitor",
    packages=find_namespace_packages(include=["internet_stability_monitor", "internet_stability_monitor.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "dnspython>=2.4.2",
        "python-whois>=0.8.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "langchain-ollama>=0.1.5",
        "psutil>=5.9.0",
        "ntplib>=0.4.0",
        "urllib3>=2.0.0",
        "websocket-client>=1.6.0",
        "PyYAML>=6.0.0",
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0"
    ],
    entry_points={
        "console_scripts": [
            "instability=internet_stability_monitor.main:main",
        ],
    },
) 