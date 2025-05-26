"""
OpenVPN Manager - Management Script
-----------------------------------
This script serves as a unified entry point for
both the API server and CLI commands.

Usage:
    ./manage.py runserver [--host HOST] [--port PORT]
    ./manage.py [CLI_COMMANDS...]
"""

import argparse
import sys
import os
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir))

try:
    import service
    from server import run_server
except ImportError as e:
    sys.exit(f"Error importing modules: {e}")


def create_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="OpenVPN Manager - Unified management interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s runserver                    Start API server
  %(prog)s runserver --host 0.0.0.0     Start API server on all interfaces
  %(prog)s list                         List all clients
  %(prog)s add client_name              Add new client
  %(prog)s revoke client_name           Revoke client certificate
        """
    )

    subparsers = parser.add_subparsers(dest='command',
                                       help='Available commands')

    # API Server subcommand
    server_parser = subparsers.add_parser('runserver',
                                          help='Start the API server')
    server_parser.add_argument('--host',
                               default=os.environ.get("OVPN_API_HOST",
                                                      "127.0.0.1"),
                               help='Host to bind the server '
                                    '(default: 127.0.0.1)')
    server_parser.add_argument('--port',
                               type=int,
                               default=int(os.environ.get("OVPN_API_PORT",
                                                          8000)),
                               help='Port to bind the server (default: 8000)')

    # If no subcommand is provided, treat remaining args as CLI commands
    parser.add_argument('cli_args',
                        nargs='*',
                        help='CLI commands and arguments')

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == 'runserver':
        # Set environment variables for the server
        os.environ["OVPN_API_HOST"] = args.host
        os.environ["OVPN_API_PORT"] = str(args.port)

        service.logger.info(f"Starting API server on {args.host}:{args.port}")
        run_server()

    elif args.cli_args or args.command is None:
        # Handle CLI commands
        if args.command is not None:
            # If a subcommand was provided but it's not 'runserver', 
            # treat it as a CLI command
            cli_args = [args.command] + (args.cli_args or [])
        else:
            cli_args = args.cli_args

        if not cli_args:
            parser.print_help()
            return

        # Temporarily modify sys.argv to pass arguments to the CLI
        original_argv = sys.argv[:]
        sys.argv = [sys.argv[0]] + cli_args

        try:
            service._cli()
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Always restore original argv
            sys.argv = original_argv
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
