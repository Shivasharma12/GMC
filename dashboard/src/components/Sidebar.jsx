import React from 'react';
import { 
  FileText, 
  Shield, 
  PlusCircle, 
  Server, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  ChevronRight,
  Sparkles
} from 'lucide-react';

export default function Sidebar({
  policies,
  selectedPolicyId,
  onSelectPolicy,
  onOpenExtractModal,
  health,
  loading
}) {
  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '24px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'var(--primary-gradient)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          boxShadow: '0 4px 12px -2px var(--primary-glow)'
        }}>
          <Shield size={20} />
        </div>
        <div>
          <h1 style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
            GMC Extractor
            <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', borderRadius: '4px' }}>v2.0</span>
          </h1>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Insurance Policy Intelligence</p>
        </div>
      </div>

      {/* Action: Run New Extraction */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <button 
          onClick={onOpenExtractModal}
          className="btn btn-primary"
          style={{ width: '100%', padding: '11px 16px', fontSize: '0.85rem' }}
        >
          <Sparkles size={16} />
          Extract New Policy
        </button>
      </div>

      {/* Policies List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 12px' }}>
        <div style={{ 
          fontSize: '0.7rem', 
          fontWeight: 700, 
          textTransform: 'uppercase', 
          letterSpacing: '0.06em', 
          color: 'var(--text-dim)', 
          padding: '0 8px 10px 8px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>Processed Policies</span>
          <span style={{ 
            background: 'rgba(255, 255, 255, 0.08)', 
            padding: '2px 7px', 
            borderRadius: '999px',
            color: 'var(--text-muted)'
          }}>
            {policies.length}
          </span>
        </div>

        {loading && policies.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
            Loading policies...
          </div>
        ) : policies.length === 0 ? (
          <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            <FileText size={28} style={{ opacity: 0.3, margin: '0 auto 8px auto' }} />
            <p>No extracted policies found.</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              Click "Extract New Policy" above.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {policies.map((p) => {
              const isSelected = p.id === selectedPolicyId;
              const confPercent = Math.round((p.confidence || 0) * 100);
              const confColor = confPercent >= 80 ? 'var(--success)' : confPercent >= 50 ? 'var(--warning)' : 'var(--danger)';

              return (
                <div
                  key={p.id}
                  onClick={() => onSelectPolicy(p.id)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                    border: `1px solid ${isSelected ? 'rgba(99, 102, 241, 0.4)' : 'transparent'}`,
                    transition: 'all 0.15s ease',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ 
                        fontWeight: 600, 
                        fontSize: '0.85rem', 
                        color: isSelected ? '#fff' : 'var(--text-main)', 
                        whiteSpace: 'nowrap', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis' 
                      }}>
                        {p.insurer_name || p.filename}
                      </div>
                      <div style={{ 
                        fontSize: '0.73rem', 
                        color: 'var(--text-dim)', 
                        marginTop: '2px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        <span>{p.policy_number || p.id}</span>
                      </div>
                    </div>
                    <span style={{ 
                      fontSize: '0.72rem', 
                      fontWeight: 700, 
                      color: confColor,
                      background: 'rgba(0,0,0,0.3)',
                      padding: '2px 6px',
                      borderRadius: '4px'
                    }}>
                      {confPercent}%
                    </span>
                  </div>

                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '10px', 
                    marginTop: '8px', 
                    fontSize: '0.7rem', 
                    color: 'var(--text-dim)' 
                  }}>
                    {p.total_lives && (
                      <span>👥 {p.total_lives} lives</span>
                    )}
                    {p.provider && (
                      <span style={{ textTransform: 'capitalize' }}>⚡ {p.provider}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Backend & Environment Health Status */}
      <div style={{ 
        padding: '16px 20px', 
        borderTop: '1px solid var(--border-subtle)', 
        background: 'rgba(7, 9, 14, 0.5)',
        fontSize: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontWeight: 600 }}>
            <Server size={14} /> Pipeline API
          </span>
          <span style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '4px', 
            color: health ? 'var(--success)' : 'var(--danger)',
            fontSize: '0.7rem',
            fontWeight: 600
          }}>
            <span style={{ 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              backgroundColor: health ? 'var(--success)' : 'var(--danger)',
              display: 'inline-block' 
            }} />
            {health ? 'Connected' : 'Offline'}
          </span>
        </div>

        {health && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
            <span className={`badge ${health.providers_available?.gemini ? 'badge-covered' : 'badge-not-mentioned'}`} style={{ fontSize: '0.65rem' }}>
              Gemini
            </span>
            <span className={`badge ${health.providers_available?.openai ? 'badge-covered' : 'badge-not-mentioned'}`} style={{ fontSize: '0.65rem' }}>
              OpenAI
            </span>
            <span className="badge badge-covered" style={{ fontSize: '0.65rem' }}>
              Mock
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}
