"""Main entry point for internet stability monitor.

This module provides the command-line interface for the internet stability monitor,
supporting interactive, batch, and test modes.
"""

import argparse
import sys
from typing import Optional
from datetime import datetime
import json
import os
from pathlib import Path

from colorama import Fore, Style, init
from tabulate import tabulate

from internet_stability_monitor.context import MonitorContext
from internet_stability_monitor.chatbot.chatbot import Chatbot
from internet_stability_monitor.service import MonitorService
from internet_stability_monitor.presentation import MonitorPresenter, DisplayOptions

# Initialize colorama
init(autoreset=True)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Internet Stability Monitor - Monitor various aspects of internet connectivity and stability."
    )
    
    # Mode selection
    parser.add_argument(
        "mode",
        choices=["interactive", "batch", "test"],
        help="Operation mode: interactive (chatbot), batch (single run), or test"
    )
    
    # Output options
    parser.add_argument(
        "--format",
        choices=["text", "json", "table"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output"
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Hide timestamps in output"
    )
    parser.add_argument(
        "--no-response-times",
        action="store_true",
        help="Hide response times in output"
    )
    parser.add_argument(
        "--no-errors",
        action="store_true",
        help="Hide error messages in output"
    )
    
    # Output file
    parser.add_argument(
        "--output",
        type=str,
        help="Save output to file (supports .txt, .json, .log extensions)"
    )
    
    # Cache file
    parser.add_argument(
        "--cache-file",
        type=str,
        default="~/.instability_cache.json",
        help="Path to cache file (default: ~/.instability_cache.json)"
    )
    
    # Service selection
    parser.add_argument(
        "--services",
        nargs="+",
        choices=[
            "dns", "email", "whois", "ixp", "cdn", "cloud",
            "ca", "web", "ntp", "system", "network", "location"
        ],
        help="Specific services to check (default: all)"
    )
    
    # Batch mode options
    parser.add_argument(
        "--interval",
        type=int,
        help="Interval between checks in seconds (batch mode only)"
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Number of checks to perform (batch mode only)"
    )
    
    return parser.parse_args()

def save_output(output: str, output_file: str) -> None:
    """Save output to file.
    
    Args:
        output: Output string to save
        output_file: Path to output file
    """
    try:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"{Fore.GREEN}Output saved to {output_file}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error saving output: {e}{Style.RESET_ALL}")

def get_display_options(args: argparse.Namespace) -> DisplayOptions:
    """Get display options from command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        DisplayOptions instance
    """
    return DisplayOptions(
        use_color=not args.no_color,
        show_timestamps=not args.no_timestamps,
        show_response_times=not args.no_response_times,
        show_errors=not args.no_errors,
        format=args.format
    )

def run_batch_mode(
    interval: int,
    count: Optional[int],
    output_file: Optional[str],
    services: Optional[list],
    display_options: DisplayOptions
) -> None:
    """Run the batch monitoring mode.
    
    Args:
        interval: Interval between checks in seconds
        count: Optional number of checks to perform
        output_file: Optional file to save results to
        services: Optional list of services to check
        display_options: Display options for output formatting
    """
    context = MonitorContext()
    service = MonitorService(context)
    presenter = MonitorPresenter(context, display_options)
    
    checks = 0
    while True:
        if count and checks >= count:
            break
            
        try:
            results = service.check_all_services()
            if services:
                results = {k: v for k, v in results.items() if k in services}
                
            output = presenter.format_results(results)
            print(output)
            
            if output_file:
                with open(output_file, 'a') as f:
                    f.write(f"\n{datetime.now()}\n{output}\n")
                    
            checks += 1
            if count and checks < count:
                print(f"\nWaiting {interval} seconds before next check...")
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping batch mode...")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            if count and checks >= count:
                break

def run_interactive_mode(cache_file: Optional[str] = None) -> None:
    """Run the interactive chatbot mode.
    
    Args:
        cache_file: Optional path to the cache file
    """
    context = MonitorContext(cache_file)
    chatbot = Chatbot(context)
    
    print(f"{Fore.GREEN}Internet Stability Monitor - Interactive Mode{Style.RESET_ALL}")
    print("Type 'help' for available commands, 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("instability> ").strip()
            if not user_input:
                continue
                
            response = chatbot.process_input(user_input)
            print(response)
            
            if user_input.lower() == 'exit' or user_input == '/exit':
                break
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

def run_test_mode() -> None:
    """Run the test mode to verify core functionality."""
    context = MonitorContext()
    service = MonitorService(context)
    
    print(f"{Fore.YELLOW}Running in test mode...{Style.RESET_ALL}")
    
    # Test basic connectivity
    results = service.check_all_services()
    
    # Check DNS resolvers
    dns_status = results.get('dns_resolvers', [])
    working_dns = [s for s in dns_status if s.is_reachable]
    print(f"\nDNS Resolvers: {len(working_dns)}/{len(dns_status)} working")
    
    # Check network connectivity
    is_connected, network_info = context.get_network_status()
    print(f"\nNetwork Status: {'Connected' if is_connected else 'Not Connected'}")
    if is_connected:
        print(f"Network Info: {network_info}")
    
    # Check system health
    is_healthy, health_status = context.get_system_health()
    print(f"\nSystem Health: {'Healthy' if is_healthy else 'Issues Detected'}")
    print(f"Health Status: {health_status}")

def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Run in appropriate mode
        if args.mode == "interactive":
            run_interactive_mode(args.cache_file)
        elif args.mode == "batch":
            run_batch_mode(
                args.interval,
                args.count,
                args.output,
                args.services,
                get_display_options(args)
            )
        else:  # test mode
            run_test_mode()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        return 0
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 