from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import os
from vulnerability_api import search_vulnerabilities


# ── CVE Knowledge Base (IMP-3: expanded from 16 to 27 entries) ──────────
cve_kb = [
    # General Linux/Server
    {"cve": "CVE-2023-1001", "desc": "Remote Code Execution in outdated SSH versions",
     "base_score": 9.8, "tags": ["ssh", "remote", "critical", "linux", "server"],
     "remediation": "Update OpenSSH to latest version immediately."},
    {"cve": "CVE-2023-1002", "desc": "SQL Injection in default web server config",
     "base_score": 7.5, "tags": ["web", "sql", "high", "server", "apache", "nginx", "http"],
     "remediation": "Sanitize inputs and update web server config."},
    {"cve": "CVE-2023-1003", "desc": "Weak password policy enforcement",
     "base_score": 4.3, "tags": ["auth", "password", "medium", "windows", "linux"],
     "remediation": "Enforce strong password policies via GPO or PAM."},
    {"cve": "CVE-2023-1004", "desc": "Unpatched Kernel vulnerability leading to privilege escalation",
     "base_score": 8.8, "tags": ["kernel", "privilege", "linux", "android"],
     "remediation": "Apply latest kernel patches and reboot."},
    {"cve": "CVE-2023-1005", "desc": "Open SMB share with guest access",
     "base_score": 6.5, "tags": ["smb", "windows", "network", "file-sharing"],
     "remediation": "Disable guest access on SMB shares."},
    # IMP-3: New entries below
    {"cve": "CVE-2023-1006", "desc": "FTP server allows anonymous login exposing sensitive data",
     "base_score": 6.8, "tags": ["ftp", "linux", "server", "network", "anonymous"],
     "remediation": "Disable anonymous FTP; replace with SFTP or FTPS."},
    {"cve": "CVE-2023-1007", "desc": "Telnet service running in cleartext over the network",
     "base_score": 7.0, "tags": ["telnet", "network", "cleartext", "linux", "server"],
     "remediation": "Disable Telnet; use SSH for all remote access."},
    {"cve": "CVE-2023-1008", "desc": "SNMP community string set to default public or private",
     "base_score": 5.5, "tags": ["snmp", "network", "default", "router", "switch"],
     "remediation": "Change SNMP community strings; upgrade to SNMPv3."},
    # Windows & RDP
    {"cve": "CVE-2023-2001", "desc": "BlueKeep RDP Remote Code Execution in Windows 7 Server 2008",
     "base_score": 9.8, "tags": ["windows", "rdp", "remote", "critical"],
     "remediation": "Apply Microsoft security update MS19-0708 immediately."},
    {"cve": "CVE-2023-2002", "desc": "Windows Print Spooler Privilege Escalation PrintNightmare",
     "base_score": 8.8, "tags": ["windows", "printer", "high", "privilege"],
     "remediation": "Disable Print Spooler service or apply latest patches."},
    {"cve": "CVE-2023-2003", "desc": "Microsoft Exchange Server ProxyLogon RCE",
     "base_score": 9.8, "tags": ["windows", "exchange", "email", "critical"],
     "remediation": "Install Exchange Cumulative Updates immediately."},
    {"cve": "CVE-2023-2004", "desc": "Windows SMBv1 EternalBlue vulnerability allowing worm propagation",
     "base_score": 9.3, "tags": ["windows", "smb", "network", "critical", "worm"],
     "remediation": "Disable SMBv1 and apply MS17-010 patch."},
    # Android & Mobile
    {"cve": "CVE-2023-3001", "desc": "Android Media Framework Arbitrary Code Execution",
     "base_score": 8.8, "tags": ["android", "mobile", "media", "high"],
     "remediation": "Update Android OS to the latest security patch level."},
    {"cve": "CVE-2023-3002", "desc": "Unsecured ADB Debugging Bridge exposed to network",
     "base_score": 7.2, "tags": ["android", "adb", "debug", "medium", "network"],
     "remediation": "Disable USB debugging; require authentication for ADB."},
    {"cve": "CVE-2023-3003", "desc": "Malicious App Installed via Sideloading on Android",
     "base_score": 6.5, "tags": ["android", "app", "mobile", "medium"],
     "remediation": "Disable Unknown Sources and enable Google Play Protect."},
    # Printers & IoT
    {"cve": "CVE-2023-4001", "desc": "Default Admin Credentials on Network Printer",
     "base_score": 9.0, "tags": ["printer", "iot", "auth", "critical", "canon", "hp", "ipp"],
     "remediation": "Change default admin password for the printer web interface."},
    {"cve": "CVE-2023-4002", "desc": "Printer exposed to public internet IPP Port 631",
     "base_score": 7.5, "tags": ["printer", "network", "exposure", "high", "ipp"],
     "remediation": "Place printer behind a firewall and disable UPnP."},
    {"cve": "CVE-2023-4003", "desc": "Outdated Firmware on Wireless Projector or IoT device",
     "base_score": 6.0, "tags": ["iot", "projector", "firmware", "school", "network"],
     "remediation": "Update device firmware from the manufacturer website."},
    {"cve": "CVE-2023-4004", "desc": "IP camera accessible without authentication over the network",
     "base_score": 8.5, "tags": ["camera", "iot", "auth", "network", "high"],
     "remediation": "Enable authentication on camera; isolate to VLAN."},
    # Networking & Wi-Fi
    {"cve": "CVE-2023-5001", "desc": "Weak WEP or WPA Encryption on Local Wi-Fi",
     "base_score": 7.5, "tags": ["wifi", "network", "encryption", "high"],
     "remediation": "Migrate to WPA2-Enterprise or WPA3."},
    {"cve": "CVE-2023-5002", "desc": "Captive Portal Bypass in Guest Network",
     "base_score": 5.4, "tags": ["wifi", "network", "auth", "medium"],
     "remediation": "Patch captive portal software or restrict guest ACLs."},
    {"cve": "CVE-2023-5003", "desc": "Router using default admin credentials admin admin",
     "base_score": 9.0, "tags": ["router", "auth", "critical", "network", "default"],
     "remediation": "Change router admin password; disable remote management."},
    # Databases
    {"cve": "CVE-2023-6001", "desc": "MySQL server accessible without auth from the network",
     "base_score": 9.4, "tags": ["mysql", "database", "network", "critical", "linux", "server"],
     "remediation": "Bind MySQL to localhost; enforce strong credentials."},
    {"cve": "CVE-2023-6002", "desc": "PostgreSQL running with default superuser without password",
     "base_score": 8.5, "tags": ["postgresql", "database", "auth", "high", "linux"],
     "remediation": "Set a strong password for the postgres superuser."},
    {"cve": "CVE-2023-6003", "desc": "MongoDB instance exposed to the internet without authentication",
     "base_score": 9.8, "tags": ["mongodb", "database", "network", "critical"],
     "remediation": "Enable MongoDB auth; bind to localhost."},
    {"cve": "CVE-2023-6004", "desc": "Redis server accessible over the network without a password",
     "base_score": 9.0, "tags": ["redis", "database", "network", "critical"],
     "remediation": "Enable Redis AUTH; restrict bind address to localhost."},
    # VNC / Remote
    {"cve": "CVE-2023-7001", "desc": "VNC server running without password or with weak password",
     "base_score": 8.0, "tags": ["vnc", "remote", "auth", "high", "linux", "windows"],
     "remediation": "Set strong VNC password; use VPN for remote access."},
]
 
# Load optional extra CVEs from cve_database.json
try:
    if os.path.exists("cve_database.json"):
        with open("cve_database.json", "r") as f:
            cve_kb.extend(json.load(f))
except Exception as e:
    print(f"Warning: Could not load extra CVE data: {e}")
 
# IMP-4: Expanded ISO 27001 Controls Mapping
iso_controls = {
    "ssh":        "A.13.1.1 Network Controls - Secure SSH configuration required.",
    "ftp":        "A.13.1.1 Network Controls - Insecure FTP service detected.",
    "telnet":     "A.13.1.1 Network Controls - Insecure Telnet must be disabled.",
    "web":        "A.14.1.2 Securing Application Services on Public Networks.",
    "http":       "A.14.1.2 Securing Application Services on Public Networks.",
    "auth":       "A.9.2.1 User Registration and De-registration.",
    "password":   "A.9.4.3 Password Management System.",
    "kernel":     "A.12.6.1 Management of Technical Vulnerabilities.",
    "smb":        "A.13.2.1 Information Transfer Policies.",
    "rdp":        "A.11.2.6 Security of Equipment and Assets Off-Premises.",
    "android":    "A.6.2.1 Mobile Device Policy.",
    "mobile":     "A.6.2.1 Mobile Device Policy.",
    "printer":    "A.11.2.9 Clear Desk and Clear Screen Policy.",
    "ipp":        "A.11.2.9 Clear Desk and Clear Screen Policy - IPP exposure.",
    "wifi":       "A.13.1.1 Network Controls - Wireless Security.",
    "router":     "A.13.1.1 Network Controls - Network Routing Control.",
    "switch":     "A.13.1.1 Network Controls - Segregation in Networks.",
    "firewall":   "A.13.1.2 Security of Network Services.",
    "iot":        "A.12.6.1 Management of Technical Vulnerabilities - IoT.",
    "projector":  "A.11.2.9 Clear Desk and Clear Screen Policy.",
    "camera":     "A.7.2.3 Physical Security - IP Camera.",
    "database":   "A.10.1.1 Policy on Cryptographic Controls - Database.",
    "mysql":      "A.10.1.1 Policy on Cryptographic Controls - MySQL.",
    "postgresql": "A.10.1.1 Policy on Cryptographic Controls - PostgreSQL.",
    "mongodb":    "A.10.1.1 Policy on Cryptographic Controls - MongoDB.",
    "redis":      "A.10.1.1 Policy on Cryptographic Controls - Redis.",
    "vnc":        "A.11.2.6 Security of Equipment and Assets Off-Premises - VNC.",
    "remote":     "A.11.2.6 Security of Equipment and Assets Off-Premises.",
    "snmp":       "A.13.1.1 Network Controls - SNMP default community string.",
    "default":    "A.9.2.4 Management of Secret Authentication Information.",
    "encryption": "A.10.1.1 Policy on the Use of Cryptographic Controls.",
    "network":    "A.13.1.1 Network Controls - General network exposure.",
}
 
# BUG-4 FIX: Build vectorizer ONCE at module load — not per request.
# Old code refitted the vectorizer inside analyze_risk() on every call.
# This wasted ~800ms per request. Now it only calls transform() per request.
_kb_corpus  = [item["desc"] + " " + " ".join(item["tags"]) for item in cve_kb]
_vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
_kb_vectors = _vectorizer.fit_transform(_kb_corpus)
 
 
def analyze_risk(asset: Dict) -> Dict:
    """
    AI-driven gap analysis and risk scoring using TF-IDF cosine similarity.
    """
 
    # BUG-5 FIX: os_version could be None from network scanner.
    # Direct dict access would throw TypeError. Use .get() with fallback.
    os_version = asset.get("os_version") or "Unknown"
    services   = asset.get("services") or []
 
    # Build device description for TF-IDF matching using ONLY useful data
    actual_services = [s for s in services if s.lower() not in ["network", "unknown"]]
    desc_parts = []
    
    os_t = asset.get("os_type", "")
    if os_t and os_t != "Unknown":
        desc_parts.append(os_t)
    if os_version and os_version != "Unknown":
        desc_parts.append(os_version)
    desc_parts.extend(actual_services)
    
    asset_desc = " ".join(desc_parts)
 
    match_indices = []
    if asset_desc.strip():
        # Transform (fast) — vectorizer already fitted at startup
        asset_vector = _vectorizer.transform([asset_desc])
        cosine_sims  = cosine_similarity(asset_vector, _kb_vectors).flatten()
        # BUG FIX: Raise threshold to 0.35 to require strong multi-word precision (OS+Service)
        # preventing generic OS names from dominating ML weights.
        match_indices = np.where(cosine_sims > 0.35)[0]
 
    # BUG-6 FIX: Deduplicate matched CVEs.
    # Old code could return the same CVE from both TF-IDF and keyword fallback,
    # doubling the remediation list and inflating gap analysis counts.
    seen_cve_ids: set = set()
    matched_cves: List[Dict] = []
    for i in match_indices:
        entry = cve_kb[i]
        if entry["cve"] not in seen_cve_ids:
            seen_cve_ids.add(entry["cve"])
            matched_cves.append(entry)
 
    # Exact Tag Match Fallback (Guaranteed assignment ONLY if AI finds nothing)
    # This prevents blindly assigning old CVEs (like EternalBlue) to modern OS (Windows 11)
    if not matched_cves:
        for item in cve_kb:
            if item["cve"] in seen_cve_ids:
                continue
            for service in services:
                if service.lower() in item["tags"] and service.lower() not in ["", "network", "unknown"]:
                    seen_cve_ids.add(item["cve"])
                    matched_cves.append(item)
                    break
        # REMOVED: Naive OS keyword fallback that flooded devices with false positives.

    # IMP-NEW: Live NVD Live API Fallback
    if not matched_cves:
        search_terms = []
        valid_services_found = False
        
        # Broad generic protocols return massive false positives on NVD if queried wildly.
        svc_ign = [
            "", "network", "unknown", "tcpwrapped", "general",
            "dns", "domain", "rpc", "msrpc", "netbios-ssn", "netbios",
            "http", "https", "ssl", "tls", "upnp", "mdns", "ssdp", "ipp"
        ]
        for svc in services:
            if svc.lower() not in svc_ign:
                valid_services_found = True
                search_terms.append(svc)
                
        # Take the most precise term to query (usually OS + service)
        if valid_services_found:
            os_t = asset.get("os_type", "")
            if os_t and os_t.lower() not in ["unknown", "unknown device", "network device", "network"]:
                search_terms.insert(0, os_t)
                
            query_str = " ".join(search_terms[:2])
            live_results = search_vulnerabilities(query_str)
            
            added_count = 0
            for res in live_results:
                if added_count >= 3:
                    break
                
                # NVD might return 15-year old vulnerabilities for generic queries.
                # Strictly filter out CVEs older than 2021 to ensure accuracy.
                try:
                    cve_year = int(res["cve"].split("-")[1])
                    if cve_year < 2021:
                        continue
                except Exception:
                    pass
                
                if res["cve"] not in seen_cve_ids:
                    seen_cve_ids.add(res["cve"])
                    matched_cves.append(res)
                    added_count += 1

 
    # ── Risk Scoring Formula ─────────────────────────────────────────────
    # Risk factor scaling: base score sets floor, criticality/exposure add weight.
    max_base_score     = max(c["base_score"] for c in matched_cves) if matched_cves else 0.0
    exposure_modifier  = min(0.2, len(services) * 0.05) # Adds up to +0.2
    criticality_factor = asset["asset_criticality"] / 10.0 # 0.1 to 1.0
    
    # Base risk starts heavily weighted by CVSS
    if max_base_score > 0:
        raw_risk = max_base_score * (0.8 + 0.2 * criticality_factor) + exposure_modifier
        risk_score = min(10.0, raw_risk)
    else:
        risk_score = 0.0
 
    # ── ISO 27001 Gap Analysis ───────────────────────────────────────────
    gaps: List[str]         = []
    remediations: List[str] = []
    used_controls: set      = set()
 
    for cve in matched_cves:
        rem_line = f"[{cve['cve']}] {cve['remediation']}"
        if rem_line not in remediations:
            remediations.append(rem_line)
        for tag in cve["tags"]:
            if tag in iso_controls and iso_controls[tag] not in used_controls:
                gaps.append(f"Gap [{cve['cve']}]: {iso_controls[tag]}")
                used_controls.add(iso_controls[tag])
 
    if not gaps:
        gaps.append("General: Ensure regular patching and vulnerability management.")
 
    if   risk_score >= 9.0: risk_level = "CRITICAL"
    elif risk_score >= 7.0: risk_level = "HIGH"
    elif risk_score >= 4.0: risk_level = "MEDIUM"
    else:                   risk_level = "LOW"
 
    # ── AI Enhanced Analysis (Groq) ──────────────────────────────────────
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    if groq_api_key and len(groq_api_key) > 10 and groq_api_key != "your_groq_api_key_here":
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            prompt = f"""
You are a senior cybersecurity auditor.
I am providing you with the details of an IT asset and its matched vulnerabilities. 
Please improve the gap analysis by providing precise ISO 27001 gaps and actionable, prioritized remediation steps.
Output JSON ONLY with two lists of strings: "gap_analysis" and "remediation_steps". Do not include any other text. Keep the steps and gaps concise and strictly technical.

Asset Details:
- OS: {asset.get('os_type')} {asset.get('os_version')}
- Services: {', '.join(services)}
- Criticality: {asset.get('asset_criticality')}
- Matched CVEs: {', '.join([c['cve'] for c in matched_cves]) if matched_cves else 'None'}
- Current Basic Gaps: {json.dumps(gaps)}
- Current Basic Remediations: {json.dumps(remediations)}

JSON Format strictly:
{{
  "gap_analysis": ["ISO 27001 Gap...", "ISO 27001 Gap..."],
  "remediation_steps": ["Step 1...", "Step 2..."]
}}
"""
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            ai_result = json.loads(chat_completion.choices[0].message.content)
            
            if isinstance(ai_result.get("gap_analysis"), list) and ai_result["gap_analysis"]:
                gaps = ai_result["gap_analysis"]
            if isinstance(ai_result.get("remediation_steps"), list) and ai_result["remediation_steps"]:
                remediations = ai_result["remediation_steps"]
        except Exception as e:
            print(f"Groq AI enhancement failed: {e}")

    return {
        "risk_score":        round(risk_score, 1),
        "cvss_base_score":   round(max_base_score, 1),
        "risk_level":        risk_level,
        "gap_analysis":      list(gaps),
        "remediation_steps": list(remediations),
        "matched_cves":      sorted([c["cve"] for c in matched_cves]),
    }
