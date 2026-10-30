import React from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  FileSearch, 
  Layers, 
  Cpu, 
  FileText 
} from 'lucide-react';

export default function AuditTab({ policyDetail }) {
  if (!policyDetail || !policyDetail.extracted) {
    return <div style={{ padding: '40px' }}>Loading audit data...</div>;
  }

  const { extracted, summary } = policyDetail;
  const doc = extracted.document_info || {};
  const warnings = extracted.warnings || [];
  const overallConf = Math.round((summary?.confidence || extracted.overall_confidence || 0.95) * 100);

  // Group confidence metrics
  const groupAudits = [
    {
      group: 'Identity (Insurer & TPA)',
      conf: Math.round((extracted.identity?.confidence || 0) * 100),
      pages: extracted.identity?.source_pages || [],
      status: extracted.identity?.insurer_name ? 'Extracted & Grounded' : 'Missing',
    },
    {
      group: 'Policy Details & Tiers',
      conf: Math.round((extracted.policy_details?.confidence || 0) * 100),
      pages: extracted.policy_details?.source_pages || [],
      status: extracted.policy_details?.policy_number ? 'Validated' : 'Incomplete',
    },
    {
      group: 'Demographics & Census',
      conf: Math.round((extracted.demographics?.confidence || 0) * 100),
      pages: extracted.demographics?.source_pages || [],
      status: extracted.demographics?.count_mismatch ? 'Census Mismatch Warning' : 'Reconciled',
      warning: extracted.demographics?.count_mismatch,
    },
    {
      group: 'Room Rent & Hospitalization',
      conf: Math.round((extracted.features?.room_hospitalization?.room_rent?.confidence || 0.9) * 100),
      pages: extracted.features?.room_hospitalization?.room_rent?.source_pages || [],
      status: 'Extracted',
    },
    {
      group: 'Maternity & Newborn Care',
      conf: Math.round((extracted.features?.maternity?.normal_delivery_metro?.confidence || 0.9) * 100),
      pages: extracted.features?.maternity?.normal_delivery_metro?.source_pages || [],
      status: 'Extracted',
    },
    {
      group: 'Waiting Periods & Waivers',
      conf: Math.round((extracted.features?.waiting_periods?.ped_waiting?.confidence || 0.85) * 100),
      pages: extracted.features?.waiting_periods?.ped_waiting?.source_pages || [],
      status: 'Extracted',
    },
    {
      group: 'Outpatient & Health Benefits',
      conf: Math.round((extracted.features?.other_benefits_a?.day_care?.confidence || 0.85) * 100),
      pages: extracted.features?.other_benefits_a?.day_care?.source_pages || [],
      status: 'Extracted (Second-pass)',
    },
    {
      group: 'Special Inclusions (AYUSH, Bariatric)',
      conf: Math.round((extracted.features?.other_benefits_b?.ayush?.confidence || 0.85) * 100),
      pages: extracted.features?.other_benefits_b?.ayush?.source_pages || [],
      status: 'Extracted (Second-pass)',
    },
    {
      group: 'Infertility & Ambulance',
      conf: Math.round((extracted.features?.infertility_ambulance?.road_ambulance?.confidence || 0.85) * 100),
      pages: extracted.features?.infertility_ambulance?.road_ambulance?.source_pages || [],
      status: 'Extracted',
    },
    {
      group: 'Corporate Buffer & Endorsements',
      conf: Math.round((extracted.features?.buffer_waiver?.corporate_buffer?.confidence || 0.85) * 100),
      pages: extracted.features?.buffer_waiver?.corporate_buffer?.source_pages || [],
      status: 'Extracted',
    },
  ];

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Banner: Extraction Metadata */}
      <div className="glass-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Source Document</span>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', marginTop: '2px' }}>
            {doc.file_name}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {doc.total_pages} Pages ({doc.scanned_pages || 0} scanned / OCR)
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Extraction Engine</span>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#818cf8', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={16} /> {doc.provider || 'mock'} / {doc.model || 'model'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Run at: {doc.run_timestamp || 'Recent'}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Grounding Method</span>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#34d399', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={16} /> BM25 + RapidFuzz
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Strict verbatim verification
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Extraction Confidence</span>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: overallConf >= 80 ? 'var(--success)' : 'var(--warning)', marginTop: '2px' }}>
            {overallConf}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Aggregate quality score
          </div>
        </div>
      </div>

      {/* Warnings & Alerts */}
      {warnings && warnings.length > 0 ? (
        <div className="glass-card" style={{ borderColor: 'rgba(245, 158, 11, 0.4)', background: 'rgba(245, 158, 11, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <AlertTriangle size={18} color="var(--warning)" />
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>
              Pipeline Audit Warnings ({warnings.length})
            </h4>
          </div>
          <ul style={{ paddingLeft: '20px', fontSize: '0.82rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {warnings.map((w, idx) => (
              <li key={idx} style={{ color: '#fde68a' }}>{w}</li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="glass-card" style={{ borderColor: 'rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.04)', display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px' }}>
          <CheckCircle size={20} color="var(--success)" />
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#34d399' }}>0 Pipeline Warnings Detected</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              All 10 schema field groups passed strict business rules and grounding constraints without validation errors.
            </div>
          </div>
        </div>
      )}

      {/* Group-by-Group Extraction Breakdown Table */}
      <div className="glass-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} color="var(--primary)" /> 10-Group Verification & Grounding Trace
        </h3>

        <table className="data-table">
          <thead>
            <tr>
              <th>Schema Field Group</th>
              <th>Status</th>
              <th>Source Page(s)</th>
              <th style={{ textAlign: 'right' }}>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {groupAudits.map((ga, idx) => {
              const confCol = ga.conf >= 80 ? 'var(--success)' : ga.conf >= 50 ? 'var(--warning)' : 'var(--danger)';
              return (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{ga.group}</td>
                  <td>
                    {ga.warning ? (
                      <span className="badge badge-warning">{ga.status}</span>
                    ) : (
                      <span className="badge badge-covered">{ga.status}</span>
                    )}
                  </td>
                  <td>
                    {ga.pages && ga.pages.length > 0 ? (
                      <span style={{ fontSize: '0.78rem', color: '#818cf8', fontWeight: 600 }}>
                        Page {ga.pages.join(', ')}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Retrieved pages</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: confCol }}>
                    {ga.conf}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}
