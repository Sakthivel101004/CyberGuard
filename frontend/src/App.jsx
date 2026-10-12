import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './index.css'

const api = axios.create({ baseURL: 'http://localhost:8000' })

// ── Helpers ────────────────────────────────────────────────
const riskColor = (level) => ({
  CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#d97706',
  LOW: '#16a34a', UNKNOWN: '#6b7280',
}[level] || '#6b7280')

const Badge = ({ level }) => {
  const cls = {
    CRITICAL: 'bg-[rgba(220,38,38,0.18)] text-[#dc2626] border border-[rgba(220,38,38,0.35)]',
    HIGH:     'bg-[rgba(234,88,12,0.18)]  text-[#ea580c] border border-[rgba(234,88,12,0.4)]',
    MEDIUM:   'bg-[rgba(217,119,6,0.18)]  text-[#d97706]',
    LOW:      'bg-[rgba(22,163,74,0.18)]  text-[#16a34a] border border-[rgba(22,163,74,0.4)]',
  }[level] || 'bg-white/10 text-[#9ca3af]'
  return <span className={`badge ${cls}`}>{level}</span>
}

const ScoreRing = ({ score, level }) => {
  const pct  = (score / 10) * 100
  const clr  = riskColor(level)
  const r    = 18, cx = 24, cy = 24
  const circ = 2 * Math.PI * r
  return (
    <svg width="48" height="48" className="flex-shrink-0">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={clr} strokeWidth="4"
        strokeDasharray={`${(pct / 100) * circ} ${circ}`} strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`} />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize="10" fontWeight="700" fill={clr}>{score}</text>
    </svg>
  )
}

// ── SVG Icons ──────────────────────────────────────────────
const Ico = ({ d, size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {typeof d === 'string' ? <path d={d} /> : d}
  </svg>
)

const IcoOverview   = () => <Ico d={<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>} />
const IcoNetwork    = () => <Ico d={<><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/></>} />
const IcoShield     = () => <Ico d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
const IcoMonitor    = () => <Ico d={<><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></>} />
const IcoFile       = () => <Ico d={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>} />
const IcoSearch     = () => <Ico d={<><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>} />
const IcoUpload     = () => <Ico d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>} />
const IcoDownload   = () => <Ico d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>} />
const IcoArrow      = () => <Ico d={<><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></>} />
const IcoBolt       = () => <Ico d={<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>} />
const IcoServer     = () => <Ico d={<><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></>} />
const IcoAlert      = () => <Ico d={<><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>} />
const IcoDoc        = () => <Ico d={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></>} />
const IcoWifi       = () => <Ico d={<><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/></>} />

// ══════════════════════════════════════════════════════════
function App() {
  const [formData, setFormData] = useState({
    hostname: '', ip_address: '', os_type: 'Linux', os_version: '',
    services: '', asset_criticality: 5,
  })
  const [loading, setLoading]                 = useState(false)
  const [networkScanning, setNetworkScanning] = useState(false)
  const [result, setResult]                   = useState(null)
  const [networkResult, setNetworkResult]     = useState(null)
  const [history, setHistory]                 = useState([])
  const [activeTab, setActiveTab]             = useState('dashboard')
  const [orgName, setOrgName]                 = useState('Target Network')
  const [expandedDevice, setExpandedDevice]   = useState(null)
  const [scanProgress, setScanProgress]       = useState({ progress: 0, message: 'Idle' })
  const scanEventSource = useRef(null)

  useEffect(() => {
    fetchHistory()
    return () => { if (scanEventSource.current) scanEventSource.current.close() }
  }, [])

  const fetchHistory = async () => {
    try { const res = await api.get('/history'); setHistory(res.data) }
    catch (err) { console.error('Failed to fetch history', err) }
  }

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value })

  const handleAnalyze = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      const payload = {
        ...formData,
        services: formData.services.split(',').map(s => s.trim()).filter(Boolean),
        asset_criticality: parseInt(formData.asset_criticality),
      }
      const res = await api.post('/analyze', payload)
      setResult(res.data); fetchHistory()
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally { setLoading(false) }
  }

  const handleNetworkScan = async () => {
    setNetworkScanning(true); setNetworkResult(null)
    setScanProgress({ progress: 0, message: 'Initiating scan...' })
    if (scanEventSource.current) scanEventSource.current.close()
    scanEventSource.current = new EventSource('http://localhost:8000/scan-progress')
    scanEventSource.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setScanProgress(data)
      if (data.progress === 100) scanEventSource.current.close()
    }
    scanEventSource.current.onerror = () => scanEventSource.current.close()
    try {
      const res = await api.post(`/network-scan?org_name=${encodeURIComponent(orgName)}`)
      setNetworkResult(res.data); fetchHistory()
    } catch (err) {
      if (scanEventSource.current) scanEventSource.current.close()
      alert('Network scan failed: ' + (err.response?.data?.detail || err.message))
    } finally { setNetworkScanning(false) }
  }

  const downloadReport = async (scanData) => {
    try {
      let asset = {}, analysis = {}
      if (scanData?.gaps) {
        asset    = { hostname: scanData.hostname, ip_address: scanData.ip, os_type: scanData.os, os_version: scanData.os_version || 'Unknown', services: scanData.services || [], asset_criticality: Math.min(10, Math.max(1, Math.round(scanData.risk || 5))) }
        analysis = { risk_score: scanData.risk, risk_level: scanData.level, gap_analysis: scanData.gaps, remediation_steps: scanData.remediation || [], matched_cves: scanData.matched_cves || [], cvss_base_score: scanData.cvss_base_score || 0 }
      } else if (result) {
        asset    = { ...formData, services: typeof formData.services === 'string' ? formData.services.split(',').map(s => s.trim()).filter(Boolean) : formData.services, asset_criticality: parseInt(formData.asset_criticality) }
        analysis = result
      } else { alert('No scan data available.'); return }
      const res  = await api.post('/generate-report', { asset, analysis }, { responseType: 'blob' })
      const url  = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url; link.setAttribute('download', `report_${asset.hostname}.pdf`)
      document.body.appendChild(link); link.click(); link.parentNode.removeChild(link)
      setTimeout(() => window.URL.revokeObjectURL(url), 100)
    } catch (err) {
      if (err.response?.data instanceof Blob) {
        const t = await err.response.data.text()
        try { alert('Error: ' + JSON.parse(t).detail) } catch { alert('Error generating report') }
      } else { alert('Error: ' + (err.response?.data?.detail || err.message)) }
    }
  }

  const downloadNetworkReport = async () => {
    if (!networkResult) { alert('Run a network scan first.'); return }
    try {
      const res  = await api.post('/network-report', networkResult, { responseType: 'blob' })
      const url  = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url; link.setAttribute('download', 'network_report.pdf')
      document.body.appendChild(link); link.click(); link.parentNode.removeChild(link)
      setTimeout(() => window.URL.revokeObjectURL(url), 100)
    } catch (err) { alert('Error: ' + err.message) }
  }

  const handleExportCSV = () => {
    if (!history.length) { alert('No data to export.'); return }
    const headers = ['ID','Hostname','IP Address','OS','Risk Score','Risk Level','Detected At','Vulns']
    const rows = history.map(h =>
      [h.id, h.hostname, h.ip, h.os, h.risk, h.level, new Date(h.time).toLocaleString(), h.gaps?.length || 0].map(v => `"${v}"`).join(',')
    )
    const blob = new Blob([[headers.join(','), ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url  = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url; link.setAttribute('download', 'cyberguard_assets.csv')
    document.body.appendChild(link); link.click(); document.body.removeChild(link)
  }

  // Derived data
  const uniqueAssets = (() => {
    const map = new Map()
    history.forEach(h => { if (!map.has(h.hostname) || new Date(h.time) > new Date(map.get(h.hostname).time)) map.set(h.hostname, h) })
    return Array.from(map.values())
  })()
  const totalVulns    = history.reduce((a, c) => a + (c.gaps?.length || 0), 0)
  const criticalCount = history.filter(h => h.level === 'CRITICAL').length

  // ── OVERVIEW ────────────────────────────────────────────
  const renderDashboard = () => (
    <div className="animate-fade-in">
      {/* Top stats row */}
      <div className="grid grid-cols-4 gap-4 mb-5">
        {/* Avg Risk Score */}
        <div className="stat-card">
          <div className="flex flex-col gap-1.5">
            <span className="text-[0.72rem] text-muted font-medium">Avg Risk Score</span>
            <div className="h-[3px] w-12 rounded-full bg-gradient-to-r from-accent to-accent-2 mt-1" />
          </div>
          <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-muted"><IcoBolt /></div>
        </div>
        {/* Scanned Assets */}
        <div className="stat-card">
          <div className="flex flex-col gap-1">
            <span className="text-[0.72rem] text-muted font-medium">Scanned Assets</span>
            <span className="text-[1.9rem] font-bold text-[#e6edf3] leading-none">{uniqueAssets.length}</span>
          </div>
          <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-muted"><IcoServer /></div>
        </div>
        {/* Total Threats */}
        <div className="stat-card">
          <div className="flex flex-col gap-1">
            <span className="text-[0.72rem] text-muted font-medium">Total Threats</span>
            <span className="text-[1.9rem] font-bold text-[#d97706] leading-none">{totalVulns}</span>
          </div>
          <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-muted"><IcoAlert /></div>
        </div>
        {/* Critical Risks */}
        <div className="stat-card">
          <div className="flex flex-col gap-1">
            <span className="text-[0.72rem] text-muted font-medium">Critical Risks</span>
            <span className="text-[1.9rem] font-bold text-[#dc2626] leading-none">{criticalCount}</span>
          </div>
          <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-muted"><IcoShield /></div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-[1fr_320px] gap-5 items-start">
        {/* ── Gap Analysis Form */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-accent"><IcoSearch /></span>
            <h2 className="text-[1rem] font-bold text-[#e6edf3]">New Gap Analysis</h2>
          </div>
          <p className="text-[0.79rem] text-muted mb-5">Initialize an AI-driven vulnerability assessment for a single asset.</p>

          <form onSubmit={handleAnalyze}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-[0.78rem] text-muted font-medium mb-1.5">Hostname</label>
                <input className="form-input" name="hostname" value={formData.hostname} onChange={handleChange} required />
              </div>
              <div>
                <label className="block text-[0.78rem] text-muted font-medium mb-1.5">IP Address</label>
                <input className="form-input" name="ip_address" value={formData.ip_address} onChange={handleChange} required />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-[0.78rem] text-muted font-medium mb-1.5">OS Type</label>
                <select className="form-input" name="os_type" value={formData.os_type} onChange={handleChange}>
                  <option value="Linux">Linux</option>
                  <option value="Windows">Windows</option>
                  <option value="Android">Android</option>
                  <option value="CiscoIOS">Network Device</option>
                  <option value="iOS">iOS</option>
                  <option value="MacOS">MacOS</option>
                </select>
              </div>
              <div>
                <label className="block text-[0.78rem] text-muted font-medium mb-1.5">OS Version</label>
                <input className="form-input" name="os_version" value={formData.os_version}
                  onChange={handleChange} placeholder="e.g. Ubuntu 22.04" />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-[0.78rem] text-muted font-medium mb-1.5">Exposed Services &amp; Protocols</label>
              <input className="form-input" name="services" value={formData.services}
                onChange={handleChange} placeholder="e.g., SSH, Nginx, Redis..." />
            </div>

            <div className="mb-5">
              <div className="flex justify-between items-center mb-2">
                <label className="text-[0.78rem] text-muted font-medium">Business Critical</label>
                <span className="text-[0.72rem] bg-white/[0.08] px-2 py-0.5 rounded font-medium">Level {formData.asset_criticality}</span>
              </div>
              <input type="range" className="form-input border-none bg-transparent p-0"
                name="asset_criticality" min="1" max="10"
                value={formData.asset_criticality} onChange={handleChange} />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-[0.9rem]">
              <IcoSearch />
              {loading ? 'Running Analysis...' : 'Initialize Analysis'}
            </button>
          </form>
        </div>

        {/* ── Right panel: awaiting / result */}
        <div className="card p-6 min-h-[300px] flex flex-col">
          {result ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-[0.95rem] font-bold text-[#e6edf3]">Scan Results</h2>
                <Badge level={result.risk_level} />
              </div>
              <div className="text-center mb-4">
                <div className="text-5xl font-extrabold" style={{ color: riskColor(result.risk_level) }}>
                  {result.risk_score}/10
                </div>
                <div className="text-[0.75rem] text-muted mt-1">
                  CVSS: {result.cvss_base_score} · {result.matched_cves.length} CVEs
                </div>
              </div>
              {result.gap_analysis.slice(0, 4).map((gap, i) => (
                <div key={i} className="gap-item">{gap}</div>
              ))}
              {result.matched_cves.length > 0 && (
                <div className="flex flex-wrap mt-3">
                  {result.matched_cves.map((c, i) => <span key={i} className="cve-tag">{c}</span>)}
                </div>
              )}
              <button onClick={() => downloadReport(null)} className="btn-primary w-full mt-4">
                <IcoDoc /> Download PDF Report
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 text-center gap-2 py-8">
              <div className="awaiting-icon"><IcoShield /></div>
              <div className="text-[0.95rem] font-semibold text-[#e6edf3]">Awaiting Target</div>
              <div className="text-[0.8rem] text-muted max-w-[180px] leading-relaxed">
                Push 'Initialize Analysis' to begin risk assessment and CVE mapping.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )

  // ── NETWORK SCAN ────────────────────────────────────────
  const renderNetworkScan = () => {
    const results  = networkResult?.results || []
    const critical = results.filter(r => r.risk_level === 'CRITICAL').length
    const high     = results.filter(r => r.risk_level === 'HIGH').length
    const medium   = results.filter(r => r.risk_level === 'MEDIUM').length
    const low      = results.filter(r => r.risk_level === 'LOW').length
    return (
      <div className="animate-fade-in">
        {/* Page header */}
        <div className="mb-5">
          <h1 className="flex items-center gap-2 text-[1.15rem] font-bold text-[#e6edf3] mb-1">
            <span className="text-muted"><IcoNetwork /></span> Network Topology Scanner
          </h1>
          <p className="text-[0.8rem] text-muted">Deep autonomous network packet inspection and vulnerability enumeration.</p>
        </div>

        {/* Scan control */}
        <div className="card p-5 mb-5">
          <div className="text-[0.75rem] text-muted mb-2">Organizational Context</div>
          <div className="flex items-center gap-3">
            <input className="form-input flex-1" value={orgName} onChange={e => setOrgName(e.target.value)} />
            <button onClick={handleNetworkScan} disabled={networkScanning} className="btn-primary whitespace-nowrap">
              <IcoSearch /> {networkScanning ? 'Scanning...' : 'Scan Network'}
            </button>
            {networkResult && (
              <button onClick={downloadNetworkReport} className="btn-secondary whitespace-nowrap">
                <IcoUpload /> Export PDF Report
              </button>
            )}
          </div>
          {networkScanning && (
            <div className="mt-4">
              <div className="flex justify-between text-[0.78rem] text-muted mb-1.5">
                <span>{scanProgress.message}</span>
                <span>{scanProgress.progress}%</span>
              </div>
              <div className="h-1.5 bg-white/[0.08] rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-accent to-accent-2 rounded-full transition-all duration-500"
                  style={{ width: `${scanProgress.progress}%` }} />
              </div>
            </div>
          )}
        </div>

        {networkResult && (
          <>
            {/* Stats + subnet row */}
            <div className="grid gap-3 mb-5" style={{ gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr 200px' }}>
              {[
                { label: 'HOSTS',    value: networkResult.total_hosts, icon: '🖥️',  color: '' },
                { label: 'CRITICAL', value: critical, icon: '🔴', color: 'text-[#dc2626]' },
                { label: 'HIGH',     value: high,     icon: '🟠', color: 'text-[#ea580c]' },
                { label: 'MEDIUM',   value: medium,   icon: '🟡', color: 'text-[#d97706]' },
                { label: 'LOW',      value: low,      icon: '🟢', color: 'text-[#16a34a]' },
              ].map((s, i) => (
                <div key={i} className="bg-surface border border-white/[0.07] rounded-xl p-3.5 text-center">
                  <div className="text-lg mb-1">{s.icon}</div>
                  <div className={`text-2xl font-bold ${s.color || 'text-[#e6edf3]'}`}>{s.value}</div>
                  <div className="text-[0.65rem] text-muted uppercase tracking-widest mt-0.5">{s.label}</div>
                </div>
              ))}
              {/* Active subnet */}
              <div className="bg-surface border border-white/[0.07] rounded-xl p-3.5 flex items-center justify-between">
                <div>
                  <div className="text-[0.65rem] font-semibold uppercase tracking-widest text-accent mb-1">Active Subnet</div>
                  <div className="text-[0.95rem] font-bold">{networkResult.subnet}</div>
                </div>
                <span className="text-muted"><IcoWifi /></span>
              </div>
            </div>

            {/* Device cards */}
            <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(330px,1fr))' }}>
              {results.map((dev, i) => (
                <div key={dev.ip}
                  className="bg-surface border border-white/[0.07] rounded-xl px-5 py-4 cursor-pointer hover:border-white/[0.13] hover:bg-surface-2 transition-all duration-150"
                  style={{ borderLeft: `3px solid ${riskColor(dev.risk_level)}` }}
                  onClick={() => setExpandedDevice(expandedDevice === i ? null : i)}>

                  <div className="flex items-center gap-3">
                    <ScoreRing score={dev.risk_score} level={dev.risk_level} />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-[0.88rem] truncate">{dev.hostname}</div>
                      <div className="text-[0.73rem] text-muted mt-0.5">{dev.ip} · {dev.device_type}</div>
                      <div className="text-[0.7rem] text-dim mt-0.5">
                        OS: {dev.os_type}{dev.os_version !== 'Unknown' ? ` — ${dev.os_version}` : ''}
                      </div>
                    </div>
                    <Badge level={dev.risk_level} />
                    <span className="text-muted text-sm"><IcoArrow /></span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mt-3.5">
                    {(dev.services || []).map((s, j) => <span key={j} className="service-tag">{s}</span>)}
                  </div>

                  {expandedDevice === i && (
                    <div className="mt-4 pt-4 border-t border-white/[0.07]">
                      {dev.gap_analysis?.length > 0 && (
                        <>
                          <div className="text-[0.7rem] font-semibold uppercase tracking-wider text-[#dc2626] mb-2">⚠ Security Gaps</div>
                          {dev.gap_analysis.map((g, k) => <div key={k} className="gap-item">{g}</div>)}
                        </>
                      )}
                      {dev.remediation_steps?.length > 0 && (
                        <>
                          <div className="text-[0.7rem] font-semibold uppercase tracking-wider text-[#16a34a] mt-3 mb-2">✓ Remediation</div>
                          {dev.remediation_steps.map((r, k) => <div key={k} className="gap-item">{r}</div>)}
                        </>
                      )}
                      {dev.matched_cves?.length > 0 && (
                        <>
                          <div className="text-[0.7rem] font-semibold uppercase tracking-wider text-purple-300 mt-3 mb-1">Matched CVEs</div>
                          <div>{dev.matched_cves.map((c, k) => <span key={k} className="cve-tag">{c}</span>)}</div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {!networkResult && !networkScanning && (
          <div className="card px-6 py-12">
            <div className="flex flex-col items-center justify-center text-center gap-2">
              <div className="awaiting-icon"><IcoWifi /></div>
              <div className="text-[0.95rem] font-semibold">No Scan Results</div>
              <div className="text-[0.8rem] text-muted max-w-[200px] leading-relaxed">
                Click Penetrate Network to discover all devices on this subnet.
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── VULNERABILITIES ─────────────────────────────────────
  const renderVulnerabilities = () => {
    const allGaps = history.flatMap(h =>
      (h.gaps || []).map(gap => ({ hostname: h.hostname, ip: h.ip, gap, level: h.level, date: h.time }))
    )
    return (
      <div className="animate-fade-in">
        <div className="mb-5">
          <h1 className="flex items-center gap-2 text-[1.15rem] font-bold text-[#e6edf3]">
            <span className="text-muted"><IcoShield /></span> Scans Database
          </h1>
        </div>
        <div className="card overflow-hidden p-0">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                {['Severity', 'Issue', 'Target Asset', 'Detected'].map(h => (
                  <th key={h} className="data-th">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allGaps.length === 0 ? (
                <tr><td colSpan="4" className="data-td text-center text-muted py-12">No vulnerabilities recorded yet.</td></tr>
              ) : allGaps.map((item, i) => (
                <tr key={i}>
                  <td className="data-td"><Badge level={item.level} /></td>
                  <td className="data-td max-w-[380px]">
                    <span className="block truncate text-[0.83rem]">{item.gap}</span>
                  </td>
                  <td className="data-td">
                    <span className="font-semibold text-[0.88rem]">{item.hostname}</span>
                    <br />
                    <span className="text-[0.72rem] text-muted">{item.ip}</span>
                  </td>
                  <td className="data-td text-[0.8rem] text-muted">{new Date(item.date).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  // ── ASSETS ──────────────────────────────────────────────
  const renderAssets = () => (
    <div className="animate-fade-in">
      <div className="flex items-start justify-between mb-5">
        <h1 className="flex items-center gap-2 text-[1.15rem] font-bold text-[#e6edf3]">
          <span className="text-muted"><IcoMonitor /></span> Assets Database
        </h1>
        <button onClick={handleExportCSV} className="btn-secondary">
          <IcoUpload /> CSV Export
        </button>
      </div>
      <div className="card overflow-hidden p-0">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {['Hostname', 'IP Address', 'OS Detail', 'Risk Profiling', 'Controls'].map(h => (
                <th key={h} className="data-th">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {uniqueAssets.length === 0 ? (
              <tr><td colSpan="5" className="data-td text-center text-muted py-12">No assets recorded yet.</td></tr>
            ) : uniqueAssets.map((a) => (
              <tr key={a.hostname}>
                <td className="data-td font-semibold text-[0.88rem]">{a.hostname}</td>
                <td className="data-td text-muted text-[0.8rem]">{a.ip}</td>
                <td className="data-td text-muted">{a.os || 'Unknown'}</td>
                <td className="data-td">
                  <div className="flex items-center gap-2">
                    <Badge level={a.level} />
                    <span className="text-[0.75rem] text-muted">{a.risk}/10</span>
                  </div>
                </td>
                <td className="data-td">
                  <button className="btn-rescan" onClick={() => {
                    const mappedServices = Array.isArray(a.services) ? a.services.join(', ') : (a.services || '')
                    setFormData({
                      hostname: a.hostname,
                      ip_address: a.ip,
                      os_type: a.os,
                      os_version: a.os_version || 'Unknown',
                      services: mappedServices,
                      asset_criticality: Number(a.asset_criticality) || 5
                    })
                    setActiveTab('dashboard')
                  }}>Rescan</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  // ── REPORTS ─────────────────────────────────────────────
  const renderReports = () => (
    <div className="animate-fade-in">
      <div className="mb-5">
        <h1 className="flex items-center gap-2 text-[1.15rem] font-bold text-[#e6edf3]">
          <span className="text-muted"><IcoFile /></span> Reports Database
        </h1>
      </div>
      <div className="card overflow-hidden p-0">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {['ID', 'Asset', 'Risk Vector', 'Date Authored', 'Download'].map(h => (
                <th key={h} className="data-th">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr><td colSpan="5" className="data-td text-center text-muted py-12">No reports yet.</td></tr>
            ) : history.map((h) => (
              <tr key={h.id}>
                <td className="data-td text-muted text-[0.8rem]">#{h.id}</td>
                <td className="data-td">
                  <span className="font-semibold text-[0.88rem]">{h.hostname}</span>
                  <span className="text-[0.72rem] text-muted ml-2">{h.ip}</span>
                </td>
                <td className="data-td"><Badge level={h.level} /></td>
                <td className="data-td text-[0.8rem] text-muted">{new Date(h.time).toLocaleString()}</td>
                <td className="data-td">
                  <button
                    onClick={() => downloadReport(h)}
                    title="Download PDF"
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: '6px',
                      padding: '5px 12px', borderRadius: '8px',
                      background: 'rgba(79,142,247,0.12)',
                      border: '1px solid rgba(79,142,247,0.3)',
                      color: '#4f8ef7', fontSize: '0.75rem', fontWeight: 700,
                      cursor: 'pointer', transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background='rgba(79,142,247,0.25)'; e.currentTarget.style.borderColor='rgba(79,142,247,0.6)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background='rgba(79,142,247,0.12)'; e.currentTarget.style.borderColor='rgba(79,142,247,0.3)'; }}
                  >
                    <IcoDownload />
                    PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  // ── NAV ─────────────────────────────────────────────────
  const navItems = [
    { id: 'dashboard', label: 'Overview',        Icon: IcoOverview },
    { id: 'network',   label: 'Network Scan',    Icon: IcoNetwork  },
    { id: 'scans',     label: 'Vulnerabilities', Icon: IcoShield   },
    { id: 'assets',    label: 'Assets',          Icon: IcoMonitor  },
    { id: 'reports',   label: 'Reports',         Icon: IcoFile     },
  ]

  // ══════════════════════════════════════════════════════
  return (
    <div className="flex h-full min-h-screen">
      {/* ── SIDEBAR ─────────────────────────────────────── */}
      <aside className="w-[178px] min-w-[178px] bg-base border-r border-white/[0.07] flex flex-col py-6 fixed top-0 left-0 h-full z-50">
        {/* Brand */}
        <div className="flex items-center gap-2.5 px-5 pb-6">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <span className="text-[1.05rem] font-bold text-[#e6edf3] tracking-tight">CyberGuard</span>
        </div>

        <div className="text-[0.62rem] font-semibold uppercase tracking-[0.1em] text-dim px-5 mb-2">
          Main Navigation
        </div>

        <nav className="flex flex-col gap-0.5 px-3">
          {navItems.map(({ id, label, Icon }) => (
            <button key={id}
              className={`nav-item ${activeTab === id ? 'active' : ''}`}
              onClick={() => setActiveTab(id)}>
              <span className={`${activeTab === id ? 'text-accent' : 'text-muted'} opacity-90`}><Icon /></span>
              {label}
            </button>
          ))}
        </nav>
      </aside>

      {/* ── MAIN ────────────────────────────────────────── */}
      <main className="ml-[178px] flex-1 p-7 overflow-y-auto">
        {activeTab === 'dashboard'  && renderDashboard()}
        {activeTab === 'network'    && renderNetworkScan()}
        {activeTab === 'scans'      && renderVulnerabilities()}
        {activeTab === 'assets'     && renderAssets()}
        {activeTab === 'reports'    && renderReports()}
      </main>
    </div>
  )
}

export default App