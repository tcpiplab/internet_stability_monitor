import subprocess
import sys
import argparse
from service_check_summarizer import summarize_service_check_output
from summary_utils import add_to_combined_summaries


def parse_network_quality_output(output):
    lines = output.splitlines()
    summary = {}

    for line in lines:
        if "Uplink capacity" in line:
            summary['uplink_capacity'] = line.split(': ')[1]
        elif "Downlink capacity" in line:
            summary['downlink_capacity'] = line.split(': ')[1]
        elif "Uplink Responsiveness" in line:
            summary['uplink_responsiveness'] = line.split(': ')[1]
        elif "Downlink Responsiveness" in line:
            summary['downlink_responsiveness'] = line.split(': ')[1]
        elif "Idle Latency" in line:
            summary['idle_latency'] = line.split(': ')[1]

    return summary


def generate_summary_text_manually(summary):

    uplink_mbps = float(summary['uplink_capacity'].split(' ')[0])
    downlink_mbps = float(summary['downlink_capacity'].split(' ')[0])

    uplink_comparison = compare_speed_to_telecom(uplink_mbps)
    downlink_comparison = compare_speed_to_telecom(downlink_mbps)


    return (
        f"Your current uplink speed is {summary['uplink_capacity']}, {uplink_comparison}."
        f"Your downlink speed is {summary['downlink_capacity']}, {downlink_comparison}. "
        f"Uplink responsiveness is measured at {summary['uplink_responsiveness']}. "
        f"Downlink responsiveness is {summary['downlink_responsiveness']}. "
        f"The idle latency of the connection is {summary['idle_latency']}."
    )


def run_network_quality_test(silent):
    try:
        # Check if running on macOS
        if sys.platform != "darwin":
            print("This script only works on macOS")
            sys.exit(1)

        # Run the networkQuality command
        if not silent:
            subprocess.run(["say", f"Please wait while the network speed and quality test is running."])
        process = subprocess.run(
            ["networkQuality", "-p", "-s"],
            capture_output=True,
            text=True
        )

        # Parse the output and generate summary
        if process.stdout:
            network_quality_report = parse_network_quality_output(process.stdout)
            network_quality_report_manual_summary = generate_summary_text_manually(network_quality_report)

            # Replace "RPM" with "roundtrips completed per minute" in the summary_text string.
            network_quality_report_manual_summary = network_quality_report_manual_summary.replace("RPM", "roundtrips completed per minute")  # type: ignore

            # print(network_quality_report_manual_summary)
            # # Speak the summary_text
            # if not silent:
            #     subprocess.run(["say", network_quality_report_manual_summary])

        try:
            network_quality_ai_summary = summarize_service_check_output(network_quality_report_manual_summary)
            print(f"Received AI network quality summary: {network_quality_ai_summary}")

            # Add the summary to the combined summaries
            add_to_combined_summaries(network_quality_ai_summary)

            if not args.silent:
                subprocess.run(["say", network_quality_ai_summary])
        except Exception as e:
            print("Failed to summarize service check output.")
            print(f"{e}")


        # Print any errors
        if process.stderr:
            print("Errors:")
            print(f"{process.stderr}")

    except FileNotFoundError:
        print("Error: networkQuality command not found. This script requires macOS 12 (Monterey) or later.")
    except subprocess.SubprocessError as e:
        print(f"Error running networkQuality command: {e}")


def compare_speed_to_telecom(speed_mbps: float) -> str:
    """
    Generates a sentence fragment comparing a given Mbps speed to telecom circuit speeds.

    Parameters:
        speed_mbps (float): The upload or download speed in Mbps.

    Returns:
        str: A sentence fragment comparing the speed to the nearest telecom circuit speed.
    """
    telecom_speeds = [
        (0.064, "an ISDN line (single channel)"),
        (0.128, "a dual-channel ISDN line"),
        (0.384, "basic DSL at 384 kbps"),
        (1.0, "roughly one Mbps"),
        (1.544, "a single T-1 line"),
        (0.772, "half a T-1 line"),
        (2.0, "DSL2 at 2 Mbps"),
        (3.0, "typical DSL speeds"),
        (5.0, "a basic cable internet connection or ADSL"),
        (10.0, "ten T-1 bonded lines, or old school Ethernet"),
        (22.368, "about 15 bonded T-1 lines"),
        (45.0, "a DS-3 line or T-3 line"),
        (22.5, "half a T-3 line"),
        (100.0, "Fast Ethernet"),
        (155.0, "an OC-3 circuit"),
        (310.0, "two OC-3 circuits"),
        (622.0, "an OC-12 circuit"),
        (1244.0, "two OC-12 circuits"),
        (2488.0, "an OC-48 circuit"),
        (4976.0, "two OC-48 circuits"),
        (10000.0, "10 Gigabit Ethernet"),
        (40000.0, "40 Gigabit Ethernet"),
        (100000.0, "100 Gigabit Ethernet"),
    ]

    # Find the closest telecom speed
    closest_speed = min(telecom_speeds, key=lambda x: abs(speed_mbps - x[0]))

    # Generate the sentence fragment
    return f"this speed is similar to {closest_speed[1]}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run network quality test.")
    parser.add_argument("--silent", action="store_true", help="Run without audio feedback.")
    args = parser.parse_args()
    run_network_quality_test(args.silent)
