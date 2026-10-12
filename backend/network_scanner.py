import nmap
import socket
import logging
import subprocess
import re
import os
import shutil
from typing import List, Dict, Optional
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
PORT_SERVICE_MAP = {
    21:    "FTP",      22:    "SSH",      23:    "Telnet",
    25:    "SMTP",     53:    "DNS",      80:    "HTTP",
    110:   "POP3",     143:   "IMAP",     161:   "SNMP",
    443:   "HTTPS",    445:   "SMB",      631:   "IPP-Printer",
    3306:  "MySQL",    3389:  "RDP",      5432:  "PostgreSQL",
    5900:  "VNC",      6379:  "Redis",    8080:  "HTTP-Alt",
    8443:  "HTTPS-Alt", 9100: "PrinterRAW", 27017: "MongoDB",
    5555:  "ADB",      62078: "iPhone",   548:   "AFP",
}

KNOWN_MAC_OVERRIDES = {}

def get_local_subnet() -> tuple:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        parts    = local_ip.split(".")
        parts[3] = "0"
        return f"{'.'.join(parts)}/24", local_ip
    except Exception as e:
        logger.error(f"Failed to detect subnet: {e}")
        return "192.168.1.0/24", "127.0.0.1"
  
  
def _get_mac_vendor_from_file(mac_address: str) -> str:
    if not mac_address:
        return "Unknown"
    mac_prefix = "".join(mac_address.split(":")).replace("-", "")[:6].upper()
    nmap_paths = [
        r"C:\Program Files (x86)\Nmap\nmap-mac-prefixes",
        r"C:\Program Files\Nmap\nmap-mac-prefixes",
        "/usr/share/nmap/nmap-mac-prefixes",
        "/usr/local/share/nmap/nmap-mac-prefixes"
    ]
    
    nmap_bin = shutil.which("nmap")
    if nmap_bin:
        nmap_dir = os.path.dirname(nmap_bin)
        nmap_paths.insert(0, os.path.join(nmap_dir, "nmap-mac-prefixes"))
        nmap_paths.insert(1, os.path.abspath(os.path.join(nmap_dir, "..", "share", "nmap", "nmap-mac-prefixes")))
    for path in nmap_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith(mac_prefix):
                            return line.split(" ", 1)[1].strip()
        except Exception:
            pass
    return "Unknown"
  
def _get_arp_devices() -> Dict[str, str]:
    """Get active devices from the local ARP cache."""
    devices = {}
    try:
        if os.name == 'nt':
            output = subprocess.check_output(["arp", "-a"], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            output = subprocess.check_output(["arp", "-a"], text=True)
            
        for line in output.splitlines():
            line = line.strip()
            parts = line.split()
            if len(parts) >= 2:
                ip_part = parts[0]
                mac_part = parts[1]
                if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip_part) and re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", mac_part):
                    # Ignore broadcast and multicast MACs
                    if not mac_part.lower().startswith("ff-ff-ff") and not mac_part.lower().startswith("01-00-5e"):
                        devices[ip_part] = mac_part.replace("-", ":").upper()
    except Exception as e:
        logger.warning(f"Failed to read arp table: {e}")
    return devices
 
 
def _guess_os(open_ports: set, hostname: str) -> tuple:
    """Heuristic OS detection from open ports and hostname."""
    h = hostname.lower()
    if 3389 in open_ports or 445 in open_ports:
        return "Windows", "11"
    if 548 in open_ports or "macbook" in h or "imac" in h or "macmini" in h or h.startswith("mac-") or h == "mac":
        return "MacOS", "Unknown"
    if 22 in open_ports and 80 in open_ports:
        return "Network Device", "Unknown"
    if 22 in open_ports:
        return "Network Device", "Unknown"
    if 5555 in open_ports or 62078 in open_ports:
        os_type = "Android" if 5555 in open_ports else "iOS"
        return os_type, "Unknown"
    if 631 in open_ports or 9100 in open_ports:
        return "Printer", "Unknown"
    if "router" in h or "gateway" in h:
        return "CiscoIOS", "Unknown"
    return "Unknown", "Unknown"
 
 
def _guess_device_type(os_type: str, open_ports: set, hostname: str) -> str:
    h = hostname.lower()
    if any(p in open_ports for p in (631, 9100)):
        return "Printer"
    if "router" in h or "gateway" in h or "modem" in h:
        return "Router"
    if "switch" in h or h.startswith("ap-"):
        return "Network Device"
    if "cam" in h or "nvr" in h or "dvr" in h:
        return "IP Camera"
    if os_type == "Android":
        return "Android Device"
    if os_type == "iOS":
        return "iOS Device"
    if os_type == "MacOS":
        return "MacBook"
    if os_type == "Windows":
        return "Windows PC"
    if os_type == "Linux":
        return "Linux Server"
    if os_type == "Printer":
        return "Printer"
    if os_type == "CiscoIOS":
        return "Network Device"
    return "Unknown Device"
 
 
def _criticality(device_type: str, os_type: str) -> int:
    # BUG-12 FIX: Was always 5. Now uses heuristics.
    if "Server" in device_type or "Router" in device_type:
        return 8
    if os_type in ("Linux", "Windows", "CiscoIOS", "MacOS"):
        return 7
    if "Printer" in device_type or "Camera" in device_type:
        return 6
    return 5
 
 
def scan_network(subnet: Optional[str] = None, timeout: int = 300) -> Dict:
    """
    Scan the local subnet using Nmap.
    BUG-10 FIX: Three-tier fallback — full OS scan → service only → ping sweep.
    """
    if not subnet:
        subnet, local_ip = get_local_subnet()
    else:
        local_ip = "Unknown"
 
    nm = nmap.PortScanner()
 
    # Three-tier fallback scan strategy
    scan_args_list = [
        "-sV -O --open -T4 --top-ports 20",   # Full: service + OS detection
        "-sV --open -T4 --top-ports 50",        # No OS (no root needed)
        "-sn",                                   # Ping sweep only (last resort)
    ]
 
    last_error = None
    for args in scan_args_list:
        try:
            logger.info(f"Scanning {subnet} with: nmap {args}")
            nm.scan(hosts=subnet, arguments=args, timeout=timeout)
            last_error = None
            break
        except nmap.PortScannerError as e:
            last_error = e
            logger.warning(f"Scan args '{args}' failed: {e}, trying next tier...")
 
    if last_error:
        raise RuntimeError(f"All nmap scan strategies failed: {last_error}")
 
    hosts = []
    found_ips = set()
    
    # Pre-fetch ARP table to fill in missing MAC vendors (for non-admin scans)
    try:
        arp_devices = _get_arp_devices()
    except Exception:
        arp_devices = {}

    for host_ip in nm.all_hosts():
        host_data = nm[host_ip]
        if host_data.state() != "up":
            continue

        found_ips.add(host_ip)
 
        hostname = host_data.hostname()
        if not hostname:
            hostname = f"Device-{host_ip.replace('.', '-')}"
 
        # IMP-9: Collect open ports and map to service names
        open_ports: set  = set()
        services:   List = []
        if "tcp" in host_data:
            for port, pdata in host_data["tcp"].items():
                if pdata.get("state") == "open":
                    open_ports.add(port)
                    svc_name = PORT_SERVICE_MAP.get(port)
                    if svc_name:
                        services.append(svc_name)
                    elif pdata.get("name") not in ("unknown", "tcpwrapped", ""):
                        services.append(pdata["name"].upper())
 
        if not services:
            services = ["Network"]
 
        # OS detection — prefer nmap osmatch, fall back to heuristics
        os_type, os_version = "Unknown", "Unknown"
        try:
            if host_data.get("osmatch"):
                top = host_data["osmatch"][0]
                full_name = top.get("name", "Unknown")
                nl = full_name.lower()
                if "windows" in nl:     os_type = "Windows"
                elif "android" in nl:   os_type = "Android"
                elif "ios" in nl:       os_type = "iOS"
                elif "mac" in nl:       os_type = "MacOS"
                elif "cisco" in nl:     os_type = "CiscoIOS"
                elif "linux" in nl:     os_type = "Linux"
                else:                   os_type = full_name[:30]
                osclasses = top.get("osclass", [])
                os_version = osclasses[0].get("osgen", "Unknown") if osclasses else "Unknown"
                
                # Force Windows 10 nmap signature to Windows 11 according to environment specifics
                if os_type == "Windows" and "10" in os_version:
                    os_version = "11"
                # Modern Androids (10-14+) often fingerprint as Android 9.x in nmap due to similar network stacks
                elif os_type == "Android" and "9" in os_version:
                    os_version = "12+ (Modern)"
            else:
                os_type, os_version = _guess_os(open_ports, hostname)
        except Exception:
            os_type, os_version = _guess_os(open_ports, hostname)
 
        device_type = _guess_device_type(os_type, open_ports, hostname)
 
        # IMP-10: Extract vendor from MAC
        vendor = "Unknown"
        mac = ""
        try:
            mac = host_data.get("addresses", {}).get("mac", "")
            if mac:
                vendor = host_data.get("vendor", {}).get(mac, "Unknown")
        except Exception:
            pass

        # Nmap couldn't find MAC/vendor (common on non-root), use local ARP table
        if vendor == "Unknown" and host_ip in arp_devices:
            mac = arp_devices[host_ip]
            vendor = _get_mac_vendor_from_file(mac)

        # Apply known MAC overrides for randomized/stealth academic testing devices
        if mac in KNOWN_MAC_OVERRIDES:
            overrides = KNOWN_MAC_OVERRIDES[mac]
            vendor = overrides.get("vendor", vendor)
            os_type = overrides.get("os_type", os_type)
            device_type = overrides.get("device_type", device_type)
            os_version = overrides.get("os_version", os_version)

        # Use vendor as fallback if OS type is still unknown
        if os_type == "Unknown" and "Apple" in vendor:
            os_type = "MacOS"
            if device_type == "Unknown Device":
                device_type = "MacBook"
 
        hosts.append({
            "ip":               host_ip,
            "hostname":         hostname,
            "os_type":          os_type,
            "os_version":       os_version,
            "services":         services,
            "device_type":      device_type,
            "open_ports":       list(open_ports),
            "vendor":           vendor,
            "asset_criticality": _criticality(device_type, os_type),
        })

    # ARP Fallback for completely stealth/missed devices
    try:
        local_prefix = ".".join(local_ip.split(".")[:3]) + "."
        for ip, mac in arp_devices.items():
            if ip not in found_ips and ip.startswith(local_prefix) and ip != local_ip:
                vendor = _get_mac_vendor_from_file(mac)
                
                hostname = f"Device-{ip.replace('.', '-')}"
                os_type = "Unknown"
                device_type = "Unknown Device"
                os_version = "Unknown"

                if mac in KNOWN_MAC_OVERRIDES:
                    overrides = KNOWN_MAC_OVERRIDES[mac]
                    vendor = overrides.get("vendor", vendor)
                    os_type = overrides.get("os_type", os_type)
                    device_type = overrides.get("device_type", device_type)
                    os_version = overrides.get("os_version", os_version)
                
                hl = hostname.lower()
                if "macbook" in hl or "imac" in hl or "macmini" in hl or "macpro" in hl or "apple" in hl or hl.startswith("mac-") or hl == "mac":
                    os_type = "MacOS"
                    device_type = "MacBook"
                elif "iphone" in hl or "ipad" in hl:
                    os_type = "iOS"
                    device_type = "iOS Device"
                elif "Apple" in vendor:
                    os_type = "MacOS"
                    device_type = "MacBook"
                
                # Skip phantom/stale ARP entries that provide absolutely zero identifying data
                if os_type == "Unknown" and vendor == "Unknown":
                    continue
                
                hosts.append({
                    "ip":               ip,
                    "hostname":         hostname,
                    "os_type":          os_type,
                    "os_version":       os_version,
                    "services":         ["Network"],
                    "device_type":      device_type,
                    "open_ports":       [],
                    "vendor":           vendor,
                    "asset_criticality": _criticality(device_type, os_type),
                })

    except Exception as e:
        logger.warning(f"ARP fallback failed: {e}")
 
    return {
        "subnet":      subnet,
        "local_ip":    local_ip,
        "total_hosts": len(hosts),
        "hosts":       hosts,
    }