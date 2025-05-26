# OpenVPN Client Manager

A utility for managing OpenVPN clients with both CLI and API interfaces, tailored for servers using Nyr's openvpn-install.sh layout.

## Features

- **Generate client configurations** - Create client certificates and keys, producing ready-to-use .ovpn files
- **Revoke clients** - Permanently revoke client access and update CRL
- **Suspend/Unsuspend clients** - Temporarily block and unblock clients without revoking their certificates
- **List blocked clients** - View all currently suspended clients
- **REST API** - Manage clients programmatically via HTTP API

## Prerequisites

1. A working OpenVPN server set up with [Nyr's openvpn-install.sh](https://github.com/Nyr/openvpn-install)
2. Server configuration located in `/etc/openvpn/server/`
3. Python 3.10+ installed on the server

## Installation

1. Clone this repository:

   ``` bash
   git clone https://github.com/yourusername/ovpn-service.git
   cd ovpn-service
   ```

2. Install dependencies:

   ``` bash
   pip install -r requirements.txt
   ```

3. Make the scripts executable:

   ``` bash
   chmod +x service.py vpn_manager.py api.py
   ```

4. Create the scripts directory and install the TLS verification script:

   ``` bash
   sudo mkdir -p /etc/openvpn/server/scripts/
   sudo cp check_client.sh /etc/openvpn/server/scripts/
   sudo chmod +x /etc/openvpn/server/scripts/check_client.sh
   ```

5. Add the following lines to your OpenVPN server configuration (`/etc/openvpn/server/server.conf`):

   ``` bash
   script-security 2
   tls-verify "/etc/openvpn/server/scripts/check_client.sh"
   ```

6. Restart the OpenVPN service:

   ``` bash
   sudo systemctl restart openvpn-server@server.service
   ```

## Automatic Startup with Cron

The project includes a convenient script for setting up automatic startup of the API server using cron scheduler.

### Setup automatic startup

To automatically start the API server on system reboot:

``` bash
./setup_cron.sh install
```

### Custom scheduling

You can specify custom cron schedule using environment variables:

``` bash
# Start daily at 2 AM
CRON_SCHEDULE='0 2 * * *' ./setup_cron.sh install

# Start every 30 minutes
CRON_SCHEDULE='*/30 * * * *' ./setup_cron.sh install
```

### Management commands

``` bash
# Remove from cron
./setup_cron.sh remove

# Check current cron jobs
./setup_cron.sh status

# Test the setup
./setup_cron.sh test

# Show help
./setup_cron.sh help
```

### Features

- **Smart dependency checking** - Verifies Python and project files
- **Virtual environment support** - Automatically activates venv or .venv if present
- **Logging** - All output is logged to `cron_server.log`
- **Safe installation** - Prevents duplicate entries and handles cleanup
- **Flexible scheduling** - Supports any valid cron expression

## CLI Usage

### Generate a client configuration

Create a new client certificate and configuration file:

``` bash
sudo ./vpn_manager.py gen client_name
```

Use a password to protect the private key:

``` bash
sudo ./vpn_manager.py gen client_name --pass
```

The generated .ovpn file will be stored in `/etc/openvpn/server/clients/`.

### Temporarily suspend a client

Block a client without revoking their certificate:

``` bash
sudo ./vpn_manager.py suspend client_name
```

### Unsuspend a client

Remove a client from the blocklist:

``` bash
sudo ./vpn_manager.py unsuspend client_name
```

### List all suspended clients

View all clients currently in the blocklist:

``` bash
sudo ./vpn_manager.py blocked
```

### Permanently revoke a client

Revoke a client's certificate and update the CRL:

``` bash
sudo ./vpn_manager.py revoke client_name
```

## API Usage

### Generate a client configuration

Create a new client certificate and configuration file via API:

``` bash
curl -X POST "http://your-server-ip:5000/generate" -H "Content-Type: application/json" -d '{"client_name": "client_name"}'
```

### Temporarily suspend a client

Block a client without revoking their certificate via API:

``` bash
curl -X POST "http://your-server-ip:5000/suspend" -H "Content-Type: application/json" -d '{"client_name": "client_name"}'
```

### Unsuspend a client

Remove a client from the blocklist via API:

``` bash
curl -X POST "http://your-server-ip:5000/unsuspend" -H "Content-Type: application/json" -d '{"client_name": "client_name"}'
```

### List all suspended clients

View all clients currently in the blocklist via API:

``` bash
curl -X GET "http://your-server-ip:5000/blocked"
```

### Permanently revoke a client

Revoke a client's certificate and update the CRL via API:

``` bash
curl -X POST "http://your-server-ip:5000/revoke" -H "Content-Type: application/json" -d '{"client_name": "client_name"}'
```

## Directory Structure

This utility works with the following directory structure:

- Easy-RSA path: `/etc/openvpn/server/easy-rsa`
- TLS-Crypt key: `/etc/openvpn/server/tc.key`
- Client template: `/etc/openvpn/server/client-common.txt`
- Output .ovpn files: `/etc/openvpn/server/clients/`
- Blocklist for suspended clients: `/etc/openvpn/server/blocked_clients.txt`

## TLS Verification

The TLS verification script checks incoming connections against the blocklist. When a client is suspended, their connections will be rejected even though their certificate is still valid.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Nyr's openvpn-install.sh](https://github.com/Nyr/openvpn-install) for the excellent OpenVPN server setup script
