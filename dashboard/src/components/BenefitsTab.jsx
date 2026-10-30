import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  Search, 
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  FileText,
  Shield,
  Baby,
  Clock,
  Activity,
  PlusCircle,
  Truck,
  Sparkles
} from 'lucide-react';

function formatCurrency(val) {
  if (val === null || val === undefined) return null;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);
}

function StatusBadge({ status }) {
  const st = (status || 'not_mentioned').toLowerCase();
  if (st === 'covered') {
    return <span className="badge badge-covered"><CheckCircle2 size={12} /> Covered</span>;
  }
  if (st === 'not_covered') {
    return <span className="badge badge-not-covered"><XCircle size={12} /> Not Covered</span>;
  }
  return <span className="badge badge-not-mentioned"><HelpCircle size={12} /> Not Mentioned</span>;
}

export default function BenefitsTab({ policyDetail, onSelectPage }) {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedCards, setExpandedCards] = useState({});

  if (!policyDetail || !policyDetail.extracted) {
    return <div style={{ padding: '40px' }}>Loading benefits...</div>;
  }

  const { features = {} } = policyDetail.extracted;

  // Flatten and categorize benefits
  const categories = [
    { id: 'room', name: 'Room & Hospitalization', icon: Shield, data: features.room_hospitalization || {} },
    { id: 'maternity', name: 'Maternity & Newborn', icon: Baby, data: features.maternity || {} },
    { id: 'waiting', name: 'Waiting Periods', icon: Clock, data: features.waiting_periods || {} },
    { id: 'other_a', name: 'Outpatient & Health (A)', icon: Activity, data: features.other_benefits_a || {} },
    { id: 'other_b', name: 'Special Covers (B)', icon: Sparkles, data: features.other_benefits_b || {} },
    { id: 'infertility_ambulance', name: 'Infertility & Ambulance', icon: Truck, data: features.infertility_ambulance || {} },
    { id: 'buffer_waiver', name: 'Buffer & Waivers', icon: PlusCircle, data: features.buffer_waiver || {} },
  ];

  const allItems = [];
  categories.forEach((cat) => {
    Object.entries(cat.data).forEach(([key, val]) => {
      if (typeof val === 'object' && val !== null) {
        allItems.push({
          categoryKey: cat.id,
          categoryName: cat.name,
          icon: cat.icon,
          fieldKey: key,
          displayName: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
          ...val,
        });
      }
    });
  });

  const filteredItems = allItems.filter((item) => {
    if (activeCategory !== 'all' && item.categoryKey !== activeCategory) return false;
    if (statusFilter !== 'all' && (item.status || 'not_mentioned').toLowerCase() !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchName = item.displayName.toLowerCase().includes(q);
      const matchEvidence = (item.evidence || '').toLowerCase().includes(q);
      const matchLimit = (item.limit_text || '').toLowerCase().includes(q);
      if (!matchName && !matchEvidence && !matchLimit) return false;
    }
    return true;
  });

  const toggleExpand = (key) => {
    setExpandedCards((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Category Pills & Filters */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <button
            onClick={() => setActiveCategory('all')}
            className={`btn ${activeCategory === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            All Benefits ({allItems.length})
          </button>
          {categories.map((cat) => {
            const Icon = cat.icon;
            const count = Object.keys(cat.data).length;
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`btn ${isActive ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.8rem', padding: '6px 14px' }}
              >
                <Icon size={14} />
                {cat.name} ({count})
              </button>
            );
          })}
        </div>

        {/* Search & Status Controls */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: '1', maxWidth: '360px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search coverage terms, limits, or evidence..."
                className="form-input"
                style={{ paddingLeft: '36px' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-select"
              style={{ width: 'auto', padding: '6px 12px', fontSize: '0.8rem' }}
            >
              <option value="all">All Statuses</option>
              <option value="covered">Covered Only</option>
              <option value="not_covered">Not Covered</option>
              <option value="not_mentioned">Not Mentioned</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grid of Benefit Cards */}
      {filteredItems.length === 0 ? (
        <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-dim)' }}>
          No policy benefits match your query.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
          {filteredItems.map((item) => {
            const itemKey = `${item.categoryKey}_${item.fieldKey}`;
            const isExpanded = expandedCards[itemKey];
            const conf = Math.round((item.confidence || 0) * 100);

            return (
              <div
                key={itemKey}
                className="glass-card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  padding: '18px',
                  borderColor: item.status === 'covered' ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-subtle)',
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {item.categoryName}
                    </span>
                    <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', marginTop: '2px' }}>
                      {item.displayName}
                    </h4>
                  </div>
                  <StatusBadge status={item.status} />
                </div>

                {/* Quantitative Limits / Specifics */}
                <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '10px 12px', borderRadius: '8px', fontSize: '0.82rem' }}>
                  {item.limit_amount !== null && item.limit_amount !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Limit Amount:</span>
                      <span style={{ fontWeight: 700, color: '#818cf8' }}>{formatCurrency(item.limit_amount)}</span>
                    </div>
                  )}

                  {item.limit_percent_of_si !== null && item.limit_percent_of_si !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>% of Sum Insured:</span>
                      <span style={{ fontWeight: 700, color: '#38bdf8' }}>{item.limit_percent_of_si}%</span>
                    </div>
                  )}

                  {item.limit_days !== null && item.limit_days !== undefined && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Days Allowed:</span>
                      <span style={{ fontWeight: 700, color: '#fbbf24' }}>{item.limit_days} Days</span>
                    </div>
                  )}

                  {item.limit_text && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginTop: '4px' }}>
                      <strong>Specifics:</strong> {item.limit_text}
                    </div>
                  )}

                  {item.limit_amount === null && !item.limit_percent_of_si && !item.limit_days && !item.limit_text && (
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.78rem' }}>
                      {item.status === 'covered' ? 'Covered under base sum insured with standard terms' : 'No explicit monetary limit specified'}
                    </div>
                  )}
                </div>

                {/* Evidence snippet */}
                {item.evidence && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', borderLeft: '2px solid var(--primary)', paddingLeft: '10px', fontStyle: 'italic' }}>
                    "{item.evidence}"
                  </div>
                )}

                {/* Source Page & Confidence Footer */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between', 
                  marginTop: 'auto', 
                  paddingTop: '8px', 
                  borderTop: '1px solid var(--border-subtle)',
                  fontSize: '0.72rem',
                  color: 'var(--text-dim)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>Confidence: <strong>{conf}%</strong></span>
                    {item.source_pages && item.source_pages.length > 0 && (
                      <button 
                        onClick={() => onSelectPage && onSelectPage(item.source_pages[0])}
                        style={{
                          background: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid var(--border-subtle)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          color: '#818cf8',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        <FileText size={11} /> Page {item.source_pages.join(', ')}
                      </button>
                    )}
                  </div>

                  {item.conditions && item.conditions.length > 0 && (
                    <button
                      onClick={() => toggleExpand(itemKey)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      {item.conditions.length} condition(s) {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    </button>
                  )}
                </div>

                {/* Expanded conditions */}
                {isExpanded && item.conditions && item.conditions.length > 0 && (
                  <div style={{ 
                    background: 'rgba(0,0,0,0.4)', 
                    padding: '10px 12px', 
                    borderRadius: '6px', 
                    fontSize: '0.75rem',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <strong style={{ color: 'var(--text-muted)' }}>Special Conditions:</strong>
                    <ul style={{ paddingLeft: '16px', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {item.conditions.map((cond, ci) => (
                        <li key={ci} style={{ color: 'var(--text-main)' }}>{cond}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
