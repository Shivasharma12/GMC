import React, { useState } from 'react';
import { 
  FileText, 
  ExternalLink, 
  Download, 
  ZoomIn, 
  Maximize2, 
  Layers 
} from 'lucide-react';

export default function PdfViewerTab({ policyDetail, targetPage }) {
  const [activePage, setActivePage] = useState(targetPage || 1);

  if (!policyDetail) {
    return <div style={{ padding: '40px' }}>Loading PDF preview...</div>;
  }

  const { pdf_url, summary } = policyDetail;
  const totalPages = summary?.total_pages || 8;

  // Build page jump buttons
  const pageNav = [];
  for (let i = 1; i <= totalPages; i++) {
    pageNav.push(i);
  }

  const pdfSrcWithPage = pdf_url ? `${pdf_url}#page=${activePage}` : null;

  return (
    <div style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '16px', height: 'calc(100vh - 120px)' }}>
      
      {/* PDF Controls Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Jump to Page:
          </span>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {pageNav.map((pg) => (
              <button
                key={pg}
                onClick={() => setActivePage(pg)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: '1px solid',
                  borderColor: activePage === pg ? 'var(--primary)' : 'var(--border-subtle)',
                  background: activePage === pg ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  color: activePage === pg ? '#fff' : 'var(--text-dim)',
                  transition: 'all 0.15s ease'
                }}
              >
                p.{pg}
              </button>
            ))}
          </div>
        </div>

        {pdf_url && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <a 
              href={pdf_url} 
              target="_blank" 
              rel="noreferrer"
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              <ExternalLink size={13} />
              Open in New Tab
            </a>
            <a 
              href={`${pdf_url}?download=true`} 
              download={summary?.filename || 'policy.pdf'}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              <Download size={13} />
              Download PDF
            </a>
          </div>
        )}
      </div>

      {/* Embedded PDF Frame */}
      <div style={{ 
        flex: 1, 
        borderRadius: '12px', 
        overflow: 'hidden', 
        border: '1px solid var(--border-subtle)',
        background: '#1a1f2c',
        position: 'relative'
      }}>
        {pdf_url ? (
          <iframe
            key={activePage}
            src={pdfSrcWithPage}
            title="GMC Policy Document"
            style={{ width: '100%', height: '100%', border: 'none' }}
          />
        ) : (
          <div style={{ 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            color: 'var(--text-muted)',
            gap: '12px'
          }}>
            <FileText size={48} style={{ opacity: 0.3 }} />
            <p>Original PDF file not found in samples or uploads folder.</p>
          </div>
        )}
      </div>

    </div>
  );
}
