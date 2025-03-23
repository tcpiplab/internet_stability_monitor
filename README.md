# Internet Stability Monitor

A comprehensive tool for monitoring internet stability and connectivity, including DNS, email, WHOIS, IXP, CDN, cloud services, and more.

## Features

- Monitor DNS resolution and root server availability
- Check email service availability (SMTP/IMAP)
- Verify WHOIS server accessibility
- Monitor Internet Exchange Points (IXPs)
- Check Content Delivery Network (CDN) availability
- Monitor cloud provider status pages
- Verify Certificate Authority (CA) endpoint status
- Check major website availability
- Network diagnostics and speed testing
- NTP server monitoring
- System service status (e.g., Ollama)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Ollama (for AI-powered features)
- ipinfo.io API key (for location information)

### Environment Variables

The following environment variables are required:

- `IPINFOIO_API_KEY`: Your ipinfo.io API key for location information. You can get a free API key at https://ipinfo.io/

### Installing the Package

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/internet_stability_monitor.git
   cd internet_stability_monitor
   ```

2. Install the package:
   ```bash
   pip install .
   ```

Or install directly from PyPI (when available):
```bash
pip install internet-stability-monitor
```

## Usage

The tool provides three modes of operation:

### Interactive Mode

Run the interactive chatbot interface:
```bash
instability interactive
```

The chatbot supports both command-based and natural language interactions:

Commands (prefixed with `/`):
- `/check [services]` - Check specified services (or all if none specified)
- `/status` - Show current system status
- `/format [type]` - Change output format (text/json/table)
- `/save [file]` - Save current output to file
- `/help` - Show available commands
- `/exit` - Exit the program

Natural Language Queries:
You can also ask questions in natural language about your system and network. For example:
- "Are we using NAT between the LAN and the internet?"
- "What's the current network latency?"
- "Is my DNS resolution working correctly?"
- "What's the status of my email services?"

The chatbot will analyze your question, determine which tools to run, and provide a natural language response based on the results.

Service types:
- dns, email, whois, ixp, cdn, cloud, ca, web, ntp, system, network, location

### Batch Mode

Run continuous monitoring:
```bash
instability batch [options]
```

Options:
- `--format [text|json|table]` - Output format (default: text)
- `--no-color` - Disable color output
- `--no-timestamps` - Hide timestamps
- `--no-response-times` - Hide response times
- `--no-errors` - Hide error messages
- `--services [service1 service2]` - Check specific services
- `--interval SECONDS` - Interval between checks
- `--count NUMBER` - Number of checks to perform
- `--output FILE` - Save output to file

Example:
```bash
instability batch --interval 300 --count 12 --output monitor.log
```

### Test Mode

Run quick verification of core functionality:
```bash
instability test
```

## Output Formats

### Text Format (Default)
```
System Information:
  OS: macOS 13.0
  Python: 3.11.0
  ...

Network Information:
  IP: 192.168.1.100
  ISP: Example ISP
  ...

DNS Resolvers:
  ✓ Google DNS (0.123s)
  ✗ Cloudflare DNS: Connection timeout
  ...
```

### JSON Format
```json
{
  "timestamp": "2024-03-14T12:00:00",
  "system_info": "...",
  "network_info": "...",
  "services": {
    "dns_resolvers": [
      {
        "name": "Google DNS",
        "is_reachable": true,
        "response_time": 0.123,
        ...
      }
    ]
  }
}
```

### Table Format
```
+--------+------------+--------------+------------------+
| Status | Name       | Response Time| Last Checked    |
+========+============+==============+==================+
| ✓      | Google DNS | 123ms        | 2024-03-14 12:00|
| ✗      | Cloudflare | -            | 2024-03-14 12:00|
+--------+------------+--------------+------------------+
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
