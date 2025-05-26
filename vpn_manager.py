#!/usr/bin/env python3
"""
OpenVPN client manager wrapper script
------------------------------------
This script serves as the main entry point for the OpenVPN client manager
that works with Nyr's openvpn-install.sh layout.

Installation:
1. Place this file in an accessible location
2. Make it executable: chmod +x vpn_manager.py
3. Ensure service.py is in the same directory
4. Copy check_client.sh to /etc/openvpn/server/scripts/ and make it executable
5. Add required lines to server.conf as mentioned in service.py documentation

For usage examples, run: ./vpn_manager.py --help
"""

import importlib.util
import sys
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).parent.absolute()

# Import service.py from the same directory
service_path = script_dir / "service.py"
if not service_path.exists():
    sys.exit(f"Error: {service_path} not found. "
             f"Please ensure it's in the same directory.")

# Dynamically import service.py
spec = importlib.util.spec_from_file_location("service", service_path)
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)

if __name__ == "__main__":
    # Call the CLI function from service.py
    service._cli()
