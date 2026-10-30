import React, { useState, useRef, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  RefreshCw, 
  ExternalLink, 
  AlertTriangle, 
  CheckCircle, 
  Calendar, 
  Layers, 
  Users,
  FileCode2,
  ShieldCheck,
  Search,
  ChevronDown,
  Check
} from 'lucide-react';

export default function Header({
  policySummary,
  activeTab,
  setActiveTab,
  onOpenExtractModal,
}) {
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setExportMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!policySummary) {
    return (
      <header className="top-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 28px' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Select or extract a policy to begin
        </div>
        <button 
          onClick={() => onOpenExtractModal?.()}
          className="btn btn-primary"
          style={{ fontSize: '0.82rem', padding: '7px 14px' }}
        >
          <RefreshCw size={14} />
          Extract New Policy
        </button>
      </header>
    );
  }

  const confPercent = Math.round((policySummary.confidence || 0) * 100);
  const confClass = confPercent >= 80 ? 'badge-covered' : confPercent >= 50 ? 'badge-warning' : 'badge-not-covered';

  const handleDownload = (type, label) => {
    if (!policySummary?.id) return;
    const policyId = policySummary.id;
    const extMap = {
      csv: 'qms.csv',
      qms: 'qms.json',
      json: 'json',
      report: 'report.md'
    };
    const downloadUrl = `/api/policies/${encodeURIComponent(policyId)}/export/${type}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `${policyId}.${extMap[type] || type}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setDownloadSuccess(label);
    setTimeout(() => {
      setDownloadSuccess(null);
      setExportMenuOpen(false);
    }, 1200);
  };

  return (
    <div>
      {/* Top Bar */}
      <header className="top-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: 0 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ 
                fontSize: '1.15rem', 
                fontWeight: 700, 
                color: '#fff', 
                letterSpacing: '-0.02em',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {policySummary.insurer_name}
              </h2>
              <span className={`badge ${confClass}`}>
                <ShieldCheck size={12} />
                {confPercent}% Confidence
              </span>
              {policySummary.count_mismatch && (
                <span className="badge badge-warning" title="Census mismatch detected: Stated total does not equal sum of parts">
                  <AlertTriangle size={12} /> Mismatch
                </span>
              )}
            </div>

            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '14px', 
              fontSize: '0.75rem', 
              color: 'var(--text-muted)',
              marginTop: '2px'
            }}>
              <span>
                <strong>Policy:</strong> {policySummary.policy_number}
              </span>
              <span>•</span>
              <span>
                <strong>TPA:</strong> {policySummary.tpa_name}
              </span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Calendar size={12} /> {policySummary.policy_start_date || 'N/A'} → {policySummary.policy_end_date || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', position: 'relative' }}>
          <button 
            onClick={() => onOpenExtractModal?.({
              isReExtract: true,
              targetPath: policySummary.pdf_path,
              policyName: policySummary.insurer_name || policySummary.id
            })}
            className="btn btn-secondary"
            title="Re-run extraction pipeline with fresh settings or bypass cache"
            style={{ fontSize: '0.8rem', padding: '7px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} />
            Re-Extract
          </button>

          <div ref={dropdownRef} style={{ position: 'relative' }}>
            <button 
              onClick={() => setExportMenuOpen(!exportMenuOpen)}
              className="btn btn-secondary"
              title="Download exports or view tables"
              style={{ 
                fontSize: '0.8rem', 
                padding: '7px 12px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px',
                background: exportMenuOpen ? 'var(--btn-secondary-hover, #2d3748)' : undefined
              }}
            >
              <Download size={14} />
              Export Data
              <ChevronDown size={12} style={{ transform: exportMenuOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
            </button>

            {exportMenuOpen && (
              <div style={{
                position: 'absolute',
                right: 0,
                top: 'calc(100% + 6px)',
                width: '240px',
                backgroundColor: '#0f172a',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                borderRadius: '8px',
                boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
                zIndex: 100,
                padding: '6px',
                display: 'flex',
                flexDirection: 'column',
                gap: '2px',
                animation: 'fadeIn 0.15s ease'
              }}>
                <div style={{ padding: '6px 8px', fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                  Direct File Downloads
                </div>

                <button
                  onClick={() => handleDownload('csv', 'QMS CSV')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={14} color="#38bdf8" />
                    <span>Download <strong>QMS CSV</strong></span>
                  </span>
                  {downloadSuccess === 'QMS CSV' && <Check size={14} color="#34d399" />}
                </button>

                <button
                  onClick={() => handleDownload('qms', 'QMS JSON')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileCode2 size={14} color="#34d399" />
                    <span>Download <strong>QMS JSON</strong></span>
                  </span>
                  {downloadSuccess === 'QMS JSON' && <Check size={14} color="#34d399" />}
                </button>

                <button
                  onClick={() => handleDownload('json', 'Full JSON')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileCode2 size={14} color="#a78bfa" />
                    <span>Download <strong>Full JSON</strong></span>
                  </span>
                  {downloadSuccess === 'Full JSON' && <Check size={14} color="#34d399" />}
                </button>

                <button
                  onClick={() => handleDownload('report', 'Audit Report')}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: '#e2e8f0',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={14} color="#fbbf24" />
                    <span>Download <strong>Audit Report</strong></span>
                  </span>
                  {downloadSuccess === 'Audit Report' && <Check size={14} color="#34d399" />}
                </button>

                <div style={{ height: '1px', backgroundColor: 'rgba(148, 163, 184, 0.2)', margin: '4px 0' }} />

                <button
                  onClick={() => {
                    setActiveTab('exports');
                    setExportMenuOpen(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    width: '100%'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <ExternalLink size={13} />
                  <span>View & Search Tables in Tab</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button 
          onClick={() => setActiveTab('overview')}
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
        >
          <Layers size={16} />
          Executive Overview
        </button>
        <button 
          onClick={() => setActiveTab('benefits')}
          className={`tab-btn ${activeTab === 'benefits' ? 'active' : ''}`}
        >
          <ShieldCheck size={16} />
          Coverage & Benefits Matrix
        </button>
        <button 
          onClick={() => setActiveTab('audit')}
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
        >
          <FileText size={16} />
          Grounding & Validation Audit
        </button>
        <button 
          onClick={() => setActiveTab('pdf')}
          className={`tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
        >
          <Search size={16} />
          Original PDF Document
        </button>
        <button 
          onClick={() => setActiveTab('exports')}
          className={`tab-btn ${activeTab === 'exports' ? 'active' : ''}`}
        >
          <FileCode2 size={16} />
          QMS Schema & Raw Exports
        </button>
      </nav>
    </div>
  );
}
