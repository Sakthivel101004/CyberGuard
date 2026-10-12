from __future__ import annotations
import shutil
import os
import json
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()
 
if os.name == 'nt':
    for path in [r"C:\Program Files (x86)\Nmap", r"C:\Program Files\Nmap"]:
        if os.path.isdir(path) and path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
 
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from models import AssetInput, RiskReport, ReportRequest
from logic import analyze_risk
from network_scanner import scan_network
from network_report import generate_network_report
import sqlite3
from report import generate_report
 
app = FastAPI(title="CyberGuard - Gap Analysis & Vulnerability Assessment")
 
# BUG-7 FIX: Was allow_origins=["*"] with allow_credentials=True.
# That combination is rejected by browsers as a security violation.
# Restrict to localhost origins only, but include all Vite dev ports (5173-5180)
# in case the default port is already in use.
_LOCALHOST_ORIGINS = [
    *(f"http://localhost:{p}" for p in range(5173, 5181)),
    *(f"http://127.0.0.1:{p}" for p in range(5173, 5181)),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCALHOST_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
 
# ── Scan Progress Tracker (IMP-6: SSE for live progress bar) ────────────
class ScanStatus:
    def __init__(self):
        self.progress   = 0
        self.message    = "Idle"
        self.is_running = False
 
    def update(self, progress: int, message: str):
        self.progress = progress
        self.message  = message
 
scan_status = ScanStatus()
 
# IMP-8: New SSE endpoint — frontend EventSource connects to this
@app.get("/scan-progress")
async def get_progress():
    async def event_generator():
        yield f"data: {json.dumps({'progress': scan_status.progress, 'message': scan_status.message})}\n\n"
        while scan_status.is_running:
            yield f"data: {json.dumps({'progress': scan_status.progress, 'message': scan_status.message})}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
 
# ── Database Setup ───────────────────────────────────────────────────────
def init_db():
    # BUG-8 FIX: Use context manager so connection always closes safely
    with sqlite3.connect("assessments.db") as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname    TEXT,
                ip_address  TEXT,
                os_type     TEXT,
                risk_score  REAL,
                risk_level  TEXT,
                gaps        TEXT,
                remediation TEXT,
                timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("PRAGMA table_info(scans)")
        columns = [info[1] for info in c.fetchall()]
        for col in ["gaps", "remediation", "services", "asset_criticality"]:
            if col not in columns:
                try:
                    # Map asset_criticality as INTEGER, others as TEXT
                    col_type = "INTEGER DEFAULT 5" if col == "asset_criticality" else "TEXT"
                    c.execute(f"ALTER TABLE scans ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError:
                    pass
 
init_db()
 
# ── Endpoints ─────────────────────────────────────────────────────────────
 
@app.get("/")
async def root():
    return {"message": "CyberGuard API is running", "docs": "/docs"}
 
 
@app.post("/analyze", response_model=RiskReport)
async def analyze_asset(asset: AssetInput):
    try:
        results = analyze_risk(asset.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
    # DEBUG: Log what's being saved
    print(f"DEBUG: Saving asset {asset.hostname} ({asset.ip_address}) with services {asset.services} and criticality {asset.asset_criticality}")
    
    # BUG-8 FIX: context manager ensures connection closes even on error
    with sqlite3.connect("assessments.db") as conn:
        conn.execute(
            "INSERT INTO scans (hostname, ip_address, os_type, risk_score, risk_level, gaps, remediation, services, asset_criticality) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (asset.hostname, asset.ip_address, asset.os_type,
             results["risk_score"], results["risk_level"],
             json.dumps(results["gap_analysis"]),
             json.dumps(results["remediation_steps"]),
             json.dumps(asset.services),
             asset.asset_criticality)
        )
    return results
 
 
# BUG-9 FIX: Was two separate Body() params — always caused 422.
# Now uses ReportRequest wrapper model that matches the frontend payload.
@app.post("/generate-report")
async def create_report(payload: ReportRequest, background_tasks: BackgroundTasks):
    try:
        report_data = {**payload.asset.model_dump(), **payload.analysis.model_dump()}
        filename = generate_report(report_data)
        background_tasks.add_task(os.remove, filename)
        return FileResponse(path=filename, filename=filename, media_type='application/pdf')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.get("/history")
async def get_history():
    with sqlite3.connect("assessments.db") as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, hostname, ip_address, os_type, risk_score, risk_level, "
            "timestamp, gaps, remediation, services, asset_criticality FROM scans ORDER BY timestamp DESC LIMIT 50"
        )
        rows = c.fetchall()
 
    history = []
    for r in rows:
        gaps, rem, services = [], [], []
        try:
            if r[7]: gaps = json.loads(r[7])
            if r[8]: rem  = json.loads(r[8])
            if len(r) > 9 and r[9]: services = json.loads(r[9])
        except json.JSONDecodeError:
            pass
        history.append({
            "id": r[0], "hostname": r[1], "ip": r[2], "os": r[3],
            "risk": r[4], "level": r[5], "time": r[6],
            "gaps": gaps, "remediation": rem, "services": services,
            "asset_criticality": r[10] if len(r) > 10 else 5,
        })
    return history
 
 
@app.post("/network-scan")
async def network_scan(subnet: str = None, org_name: str = "Target Network"):
    if scan_status.is_running:
        raise HTTPException(status_code=400, detail="A network scan is already in progress. Please wait.")
        
    if not shutil.which("nmap"):
        raise HTTPException(
            status_code=503,
            detail="nmap is not installed. Download from https://nmap.org/download.html"
        )
 
    try:
        scan_status.is_running = True
        scan_status.update(10, "Discovering devices on network...")
        scan_result = await asyncio.to_thread(scan_network, subnet)
    except RuntimeError as e:
        scan_status.is_running = False
        scan_status.update(0, "Scan failed.")
        raise HTTPException(status_code=500, detail=str(e))
 
    if not scan_result["hosts"]:
        scan_status.is_running = False
        return {
            "subnet": scan_result["subnet"], "local_ip": scan_result["local_ip"],
            "total_hosts": 0, "results": [],
            "message": "No live hosts found on the network.",
        }
 
    all_results  = []
    total_hosts  = len(scan_result["hosts"])
 
    with sqlite3.connect("assessments.db") as conn:
        for i, host in enumerate(scan_result["hosts"]):
            scan_status.update(
                30 + int((i / total_hosts) * 60),
                f"Analysing {host['hostname']} ({host['ip']})..."
            )
            asset_payload = {
                "hostname":          host["hostname"],
                "ip_address":        host["ip"],
                "os_type":           host["os_type"],
                "os_version":        host.get("os_version") or "Unknown",  # IMP-7
                "services":          host["services"],
                "asset_criticality": host["asset_criticality"],
                "firmware_version":  None,
            }
            try:
                analysis = await asyncio.to_thread(analyze_risk, asset_payload)
            except Exception as e:
                analysis = {
                    "risk_score": 0.0, "risk_level": "UNKNOWN",
                    "gap_analysis": [f"Analysis error: {e}"],
                    "remediation_steps": [], "matched_cves": [], "cvss_base_score": 0.0,
                }
            # DEBUG: Log scan persistence
            print(f"DEBUG: Saving network asset {host['hostname']} with services {host['services']} and criticality {host['asset_criticality']}")
            
            conn.execute(
                "INSERT INTO scans (hostname, ip_address, os_type, risk_score, risk_level, gaps, remediation, services, asset_criticality) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (host["hostname"], host["ip"], host["os_type"],
                 analysis["risk_score"], analysis["risk_level"],
                 json.dumps(analysis["gap_analysis"]),
                 json.dumps(analysis["remediation_steps"]),
                 json.dumps(host["services"]),
                 host["asset_criticality"])
            )
            all_results.append({**host, **analysis})
 
    scan_status.update(100, "Scan complete!")
    scan_status.is_running = False
 
    return {
        "subnet":      scan_result["subnet"],
        "local_ip":    scan_result["local_ip"],
        "total_hosts": scan_result["total_hosts"],
        "org_name":    org_name,
        "results":     all_results,
    }
 
 
@app.post("/network-report")
async def create_network_report(payload: dict = Body(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        scan_meta = {
            "subnet":      payload.get("subnet"),
            "local_ip":    payload.get("local_ip"),
            "total_hosts": payload.get("total_hosts"),
        }
        filename = generate_network_report(
            scan_meta,
            payload.get("results", []),
            payload.get("org_name", "Target Network")
        )
        background_tasks.add_task(os.remove, filename)
        return FileResponse(path=filename, filename=filename, media_type='application/pdf')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)