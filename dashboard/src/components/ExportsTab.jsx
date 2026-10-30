import React, { useState } from 'react';
import { 
  Download, 
  Copy, 
  Check, 
  Table as TableIcon, 
  FileCode, 
  FileText, 
  Search,
  ExternalLink
} from 'lucide-react';

export default function ExportsTab({ policyDetail }) {
  const [activeExportMode, setActiveExportMode] = useState('csv');
  const [copied, setCopied] = useState(false);
  const [tableSearch, setTableSearch] = useState('');

  if (!policyDetail) {
    return <div style={{ padding: '40px' }}>Loading export data...</div>;
  }

  const { extracted, qms, csv_text, csv_rows, report_markdown, summary } = policyDetail;
  const policyId = summary?.id || 'policy';

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadFile = (content, filename, type) => {
    const blob = new Blob([content], { type: `${type};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.setAttribute('download', filename);
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 10000);
  };

  const filteredCsvRows = (csv_rows || []).filter((row) => {
    if (!tableSearch) return true;
    const q = tableSearch.toLowerCase();
    return Object.values(row).some((val) => String(val || '').toLowerCase().includes(q));
  });

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Export Sub-Tabs & Actions Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveExportMode('csv')}
            className={`btn ${activeExportMode === 'csv' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <TableIcon size={14} />
            QMS CSV Table
          </button>
          <button
            onClick={() => setActiveExportMode('qms_json')}
            className={`btn ${activeExportMode === 'qms_json' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <FileCode size={14} />
            QMS Standard JSON
          </button>
          <button
            onClick={() => setActiveExportMode('raw_json')}
            className={`btn ${activeExportMode === 'raw_json' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <FileCode size={14} />
            Full Extracted JSON
          </button>
          <button
            onClick={() => setActiveExportMode('report')}
            className={`btn ${activeExportMode === 'report' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <FileText size={14} />
            Markdown Review Report
          </button>
        </div>

        {/* Download & Copy Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          {activeExportMode === 'csv' && (
            <a
              href={`/api/policies/${encodeURIComponent(policyId)}/export/csv`}
              download={`${policyId}.qms.csv`}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
            >
              <Download size={14} />
              Download CSV
            </a>
          )}

          {activeExportMode === 'qms_json' && (
            <>
              <button
                onClick={() => handleCopy(JSON.stringify(qms, null, 2))}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px' }}
              >
                {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy JSON'}
              </button>
              <a
                href={`/api/policies/${encodeURIComponent(policyId)}/export/qms`}
                download={`${policyId}.qms.json`}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
              >
                <Download size={14} />
                Download QMS JSON
              </a>
            </>
          )}

          {activeExportMode === 'raw_json' && (
            <>
              <button
                onClick={() => handleCopy(JSON.stringify(extracted, null, 2))}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px' }}
              >
                {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy JSON'}
              </button>
              <a
                href={`/api/policies/${encodeURIComponent(policyId)}/export/json`}
                download={`${policyId}.json`}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
              >
                <Download size={14} />
                Download Extracted JSON
              </a>
            </>
          )}

          {activeExportMode === 'report' && (
            <>
              <button
                onClick={() => handleCopy(report_markdown)}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px' }}
              >
                {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                {copied ? 'Copied!' : 'Copy Report'}
              </button>
              <a
                href={`/api/policies/${encodeURIComponent(policyId)}/export/report`}
                download={`${policyId}.report.md`}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '7px 12px', textDecoration: 'none' }}
              >
                <Download size={14} />
                Download Report (.md)
              </a>
            </>
          )}
        </div>
      </div>

      {/* Content Panes */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        
        {/* CSV Preview */}
        {activeExportMode === 'csv' && (
          <div>
            <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ position: 'relative', width: '280px' }}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                <input
                  type="text"
                  value={tableSearch}
                  onChange={(e) => setTableSearch(e.target.value)}
                  placeholder="Filter table rows..."
                  className="form-input"
                  style={{ padding: '6px 10px 6px 30px', fontSize: '0.78rem' }}
                />
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Showing {filteredCsvRows.length} rows
              </span>
            </div>

            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {filteredCsvRows.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(filteredCsvRows[0]).map((h, i) => (
                        <th key={i}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCsvRows.map((row, rIdx) => (
                      <tr key={rIdx}>
                        {Object.values(row).map((val, cIdx) => (
                          <td key={cIdx}>
                            {String(val || '—')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)' }}>
                  No matching CSV rows.
                </div>
              )}
            </div>
          </div>
        )}

        {/* QMS Standard JSON */}
        {activeExportMode === 'qms_json' && (
          <div style={{ padding: '20px', maxHeight: '650px', overflowY: 'auto', background: '#0a0e17' }}>
            <pre style={{ fontSize: '0.8rem', color: '#a5b4fc', lineHeight: 1.6 }}>
              {JSON.stringify(qms, null, 2)}
            </pre>
          </div>
        )}

        {/* Raw Extracted JSON */}
        {activeExportMode === 'raw_json' && (
          <div style={{ padding: '20px', maxHeight: '650px', overflowY: 'auto', background: '#0a0e17' }}>
            <pre style={{ fontSize: '0.8rem', color: '#6ee7b7', lineHeight: 1.6 }}>
              {JSON.stringify(extracted, null, 2)}
            </pre>
          </div>
        )}

        {/* Markdown Report */}
        {activeExportMode === 'report' && (
          <div style={{ padding: '28px', maxHeight: '650px', overflowY: 'auto', color: 'var(--text-main)' }}>
            <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontSize: '0.88rem' }}>
              {report_markdown || 'No report generated for this policy.'}
            </pre>
          </div>
        )}

      </div>

    </div>
  );
}
