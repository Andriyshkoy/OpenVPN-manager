from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

# Configure logging
logger = logging.getLogger("ovpn-service")
logger.setLevel(logging.INFO)
# Console handler
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)
# File handler (optional)
log_dir = Path("/var/log/ovpn-service")
log_dir.mkdir(exist_ok=True, parents=True)
fh = logging.FileHandler(log_dir / "ovpn-service.log")
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

# Enable debug logging if DEBUG environment variable is set
if os.environ.get("DEBUG"):
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

# ======== PATHS ================
BASE_DIR = Path("/etc/openvpn/server")
EASYRSA_PATH = BASE_DIR / "easy-rsa"
EASYRSA_BIN = EASYRSA_PATH / "easyrsa"
OUTPUT_DIR = BASE_DIR / "clients"
BASE_OVPN_TEMPLATE = BASE_DIR / "client-common.txt"
TLS_KEY = BASE_DIR / "tc.key"
BLOCKLIST_PATH = BASE_DIR / "blocked_clients.txt"
CRL_PATH = BASE_DIR / "crl.pem"

TLS_TAG = "tls-crypt" if TLS_KEY.name.startswith("tc") else "tls-auth"
ADD_KEY_DIRECTION = TLS_TAG == "tls-auth"

# ============================================================================


def _run_easy_rsa(args: List[str]) -> None:
    """Run Easy‑RSA with *args* and raise on failure."""
    cmd = [str(EASYRSA_BIN)] + args
    logger.debug(f"Executing command: {' '.join(cmd)}")
    logger.debug(f"Working directory: {EASYRSA_PATH}")

    # Add EASYRSA_BATCH=1 environment variable to avoid prompts in most cases
    env = os.environ.copy()
    env["EASYRSA_BATCH"] = "1"

    try:
        # For commands that might still require confirmation
        if "build-client-full" in args or "revoke" in args:
            # Use Popen to be able to write to stdin
            process = subprocess.Popen(
                cmd,
                cwd=EASYRSA_PATH,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )

            stdout, stderr = process.communicate(input="yes\n")

            if process.returncode != 0:
                logger.error(f"Command failed with exit code "
                             f"{process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, cmd)

            logger.debug(stdout)
            if stderr:
                logger.debug(f"STDERR: {stderr}")
        else:
            result = subprocess.run(
                cmd,
                cwd=EASYRSA_PATH,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )
            logger.debug(result.stdout)
            if result.stderr:
                logger.debug(f"STDERR: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        if hasattr(e, 'stdout') and e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        raise


def _refresh_crl() -> None:
    """Copy freshly generated CRL from Easy‑RSA pki to server directory."""
    src = EASYRSA_PATH / "pki" / "crl.pem"
    if not src.exists():
        raise RuntimeError("crl.pem not found after gen-crl")
    shutil.copy2(src, CRL_PATH)


def generate_client(name: str, password: bool = False) -> Path:
    """Create cert/key for *name* and build inline .ovpn. Return file path."""
    build = ["build-client-full", name]
    if not password:
        build.append("nopass")
    _run_easy_rsa(build)

    pki = EASYRSA_PATH / "pki"
    certs = {
        "ca": pki / "ca.crt",
        "cert": pki / "issued" / f"{name}.crt",
        "key": pki / "private" / f"{name}.key",
        "tls": TLS_KEY,
    }

    template = BASE_OVPN_TEMPLATE.read_text().rstrip() + "\n"

    def embed(tag: str, path: Path) -> str:
        return f"<{tag}>\n{path.read_text().strip()}\n</{tag}>\n"

    cfg = template
    cfg += embed("ca", certs["ca"])
    cfg += embed("cert", certs["cert"])
    cfg += embed("key", certs["key"])
    cfg += embed(TLS_TAG, certs["tls"])
    if ADD_KEY_DIRECTION:
        cfg += "key-direction 1\n"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{name}.ovpn"
    out.write_text(cfg)
    logger.info(f"Generated client configuration for {name}: {out}")
    return out


def revoke_client(name: str) -> None:
    """Revoke cert, regenerate CRL, copy it to server dir, unsuspend user."""
    _run_easy_rsa(["revoke", name])
    _run_easy_rsa(["gen-crl"])
    _refresh_crl()

    # Remove client artefacts
    pki = EASYRSA_PATH / "pki"
    for sub in ("issued", "private", "reqs"):
        (pki / sub / f"{name}.crt").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{name}.ovpn").unlink(missing_ok=True)
    unsuspend_client(name)
    logger.info(f"Revoked {name} and updated CRL")

# ---- suspend logic ---------------------------------------------------------


def suspend_client(name: str) -> int:
    BLOCKLIST_PATH.touch(exist_ok=True)
    lines = BLOCKLIST_PATH.read_text().splitlines()
    if name in lines:
        logger.info(f"Client {name} already suspended")
    BLOCKLIST_PATH.write_text("\n".join(lines + [name]) + "\n")
    logger.info(f"Client {name} suspended (added to block-list)")


def unsuspend_client(name: str) -> None:
    if not BLOCKLIST_PATH.exists():
        return
    lines = [line for line in BLOCKLIST_PATH.read_text().splitlines()
             if line != name]
    BLOCKLIST_PATH.write_text("\n".join(lines) + ("\n" if lines else ""))
    logger.info(f"Client {name} unsuspended")


def list_blocked() -> None:
    if not BLOCKLIST_PATH.exists() or not BLOCKLIST_PATH.read_text().strip():
        logger.info("No suspended clients")
        return
    blocked_clients = BLOCKLIST_PATH.read_text().splitlines()
    logger.info(f"Suspended clients: {', '.join(blocked_clients)}")
    # For CLI display, still print to stdout
    print("Suspended clients:")
    for cn in blocked_clients:
        print(f"  • {cn}")

# ---- CLI -------------------------------------------------------------------


def _cli() -> None:
    p = argparse.ArgumentParser(description="OpenVPN client manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="Generate client & inline config")
    g.add_argument("name")
    g.add_argument("--pass", dest="use_pass", action="store_true",
                   help="Protect private key with passphrase")

    r = sub.add_parser("revoke", help="Revoke client and update CRL")
    r.add_argument("name")

    s = sub.add_parser("suspend",
                       help="Temporarily block client via tls-verify")
    s.add_argument("name")

    u = sub.add_parser("unsuspend", help="Remove client from block‑list")
    u.add_argument("name")

    sub.add_parser("blocked", help="List suspended clients")

    args = p.parse_args()
    try:
        match args.cmd:
            case "gen":
                generate_client(args.name, password=args.use_pass)
            case "revoke":
                revoke_client(args.name)
            case "suspend":
                suspend_client(args.name)
            case "unsuspend":
                unsuspend_client(args.name)
            case "blocked":
                list_blocked()
    except subprocess.CalledProcessError as e:
        logger.error(f"Easy‑RSA error: {e.stderr.decode() if e.stderr else e}")
        sys.exit(f"Easy‑RSA error: {e.stderr.decode() if e.stderr else e}")


if __name__ == "__main__":
    _cli()
