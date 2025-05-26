#!/bin/bash

# setup_cron.sh - Script to add OpenVPN Manager server to cron scheduler
# This script sets up automatic startup of the OpenVPN Manager API server

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="${PYTHON_EXEC:-python3}"
SERVER_SCRIPT="$SCRIPT_DIR/server.py"
LOG_FILE="$SCRIPT_DIR/cron_server.log"
CRON_COMMENT="# OpenVPN Manager API Server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. The cron job will be installed for root user."
        return 0
    else
        print_status "Running as regular user: $(whoami)"
        return 0
    fi
}

# Check if Python and required files exist
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v "$PYTHON_EXEC" &> /dev/null; then
        print_error "Python3 not found. Please install Python3 or set PYTHON_EXEC environment variable."
        exit 1
    fi
    
    if [[ ! -f "$SERVER_SCRIPT" ]]; then
        print_error "Server script not found at: $SERVER_SCRIPT"
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_DIR/requirements.txt" ]]; then
        print_warning "requirements.txt not found. Make sure dependencies are installed."
    fi
    
    print_status "Dependencies check passed"
}

# Create a wrapper script for cron
create_wrapper_script() {
    local wrapper_script="$SCRIPT_DIR/run_server_cron.sh"
    
    print_status "Creating wrapper script at: $wrapper_script"
    
    cat > "$wrapper_script" << EOF
#!/bin/bash
# Auto-generated wrapper script for OpenVPN Manager cron job

# Set environment variables
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export PYTHONPATH="$SCRIPT_DIR:\$PYTHONPATH"

# Change to script directory
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
fi

# Run the server with logging
exec $PYTHON_EXEC "$SERVER_SCRIPT" >> "$LOG_FILE" 2>&1
EOF

    chmod +x "$wrapper_script"
    print_status "Wrapper script created and made executable"
    echo "$wrapper_script"
}

# Function to add cron job
add_cron_job() {
    local wrapper_script="$1"
    local cron_schedule="${CRON_SCHEDULE:-@reboot}"
    
    print_status "Adding cron job with schedule: $cron_schedule"
    
    # Create temporary cron file
    local temp_cron=$(mktemp)
    
    # Get current crontab (ignore errors if no crontab exists)
    crontab -l 2>/dev/null > "$temp_cron" || true
    
    # Check if our job already exists
    if grep -q "$CRON_COMMENT" "$temp_cron"; then
        print_warning "OpenVPN Manager cron job already exists. Removing old entry..."
        # Remove old entries
        grep -v "$CRON_COMMENT" "$temp_cron" > "${temp_cron}.new" || true
        grep -v "$wrapper_script" "${temp_cron}.new" > "$temp_cron" || true
        rm -f "${temp_cron}.new"
    fi
    
    # Add new cron job
    echo "$CRON_COMMENT" >> "$temp_cron"
    echo "$cron_schedule $wrapper_script" >> "$temp_cron"
    
    # Install new crontab
    crontab "$temp_cron"
    rm "$temp_cron"
    
    print_status "Cron job added successfully"
}

# Function to remove cron job
remove_cron_job() {
    print_status "Removing OpenVPN Manager cron job..."
    
    local temp_cron=$(mktemp)
    
    # Get current crontab
    if ! crontab -l 2>/dev/null > "$temp_cron"; then
        print_warning "No crontab found for current user"
        rm "$temp_cron"
        return 0
    fi
    
    # Remove our entries
    if grep -q "$CRON_COMMENT" "$temp_cron"; then
        grep -v "$CRON_COMMENT" "$temp_cron" > "${temp_cron}.new"
        grep -v "run_server_cron.sh" "${temp_cron}.new" > "$temp_cron"
        rm "${temp_cron}.new"
        
        # Install cleaned crontab
        crontab "$temp_cron"
        print_status "Cron job removed successfully"
    else
        print_warning "No OpenVPN Manager cron job found"
    fi
    
    rm "$temp_cron"
}

# Function to show current cron jobs
show_cron_jobs() {
    print_status "Current cron jobs for user $(whoami):"
    crontab -l 2>/dev/null || print_warning "No crontab found for current user"
}

# Function to test the setup
test_setup() {
    local wrapper_script="$SCRIPT_DIR/run_server_cron.sh"
    
    print_status "Testing the setup..."
    
    if [[ ! -f "$wrapper_script" ]]; then
        print_error "Wrapper script not found. Run 'install' first."
        exit 1
    fi
    
    print_status "Testing wrapper script execution..."
    echo "Test run at $(date)" >> "$LOG_FILE"
    
    # Test run in background for 5 seconds
    timeout 5s "$wrapper_script" &
    local pid=$!
    
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        kill $pid 2>/dev/null
        print_status "Test successful - server starts correctly"
    else
        print_error "Test failed - check $LOG_FILE for errors"
        exit 1
    fi
}

# Main function
main() {
    case "${1:-install}" in
        "install")
            check_root
            check_dependencies
            wrapper_script=$(create_wrapper_script)
            add_cron_job "$wrapper_script"
            print_status "Installation completed!"
            print_status "Log file: $LOG_FILE"
            print_status "Use '$0 test' to test the setup"
            print_status "Use '$0 status' to check cron jobs"
            ;;
        "remove"|"uninstall")
            remove_cron_job
            rm -f "$SCRIPT_DIR/run_server_cron.sh"
            print_status "Uninstallation completed!"
            ;;
        "status"|"show")
            show_cron_jobs
            ;;
        "test")
            test_setup
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  install     Install OpenVPN Manager to cron (default)"
            echo "  remove      Remove from cron and cleanup"
            echo "  status      Show current cron jobs"
            echo "  test        Test the setup"
            echo "  help        Show this help"
            echo ""
            echo "Environment variables:"
            echo "  CRON_SCHEDULE    Cron schedule (default: @reboot)"
            echo "  PYTHON_EXEC      Python executable (default: python3)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Install with @reboot schedule"
            echo "  CRON_SCHEDULE='0 2 * * *' $0  # Install with daily 2 AM schedule"
            echo "  $0 test                      # Test the installation"
            echo "  $0 remove                    # Remove from cron"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
