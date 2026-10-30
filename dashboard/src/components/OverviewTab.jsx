import React from 'react';
import { 
  DollarSign, 
  Users, 
  Shield, 
  Calendar, 
  Check, 
  X, 
  AlertCircle, 
  Info,
  TrendingUp,
  FileCheck,
  Building,
  Heart
} from 'lucide-react';

function formatCurrency(val) {
  if (val === null || val === undefined) return 'Not Specified';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);
}

export default function OverviewTab({ policyDetail }) {
  if (!policyDetail || !policyDetail.extracted) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading policy details...</div>;
  }

  const { extracted } = policyDetail;
  const policy = extracted.policy_details || {};
  const demo = extracted.demographics || {};
  const fam = policy.family_structure || {};
  const doc = extracted.document_info || {};
  const features = extracted.features || {};

  const room = features.room_hospitalization || {};
  const mat = features.maternity || {};
  const wait = features.waiting_periods || {};

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Stat Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        
        {/* Total Premium Card */}
        <div className="stat-card">
          <div className="stat-label">
            <DollarSign size={16} color="var(--primary)" /> Total Inception Premium
          </div>
          <div className="stat-value" style={{ color: '#818cf8' }}>
            {formatCurrency(policy.premium_including_gst || policy.premium_excluding_gst)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Excl. GST: {formatCurrency(policy.premium_excluding_gst)}
          </div>
        </div>

        {/* Total Covered Lives Card */}
        <div className="stat-card">
          <div className="stat-label">
            <Users size={16} color="var(--info)" /> Total Lives Insured
          </div>
          <div className="stat-value" style={{ color: '#38bdf8' }}>
            {demo.total_lives_stated || demo.total_lives_computed || 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: demo.count_mismatch ? 'var(--warning)' : 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            {demo.count_mismatch ? (
              <>⚠️ Census mismatch (Computed: {demo.total_lives_computed})</>
            ) : (
              <>✓ Census reconciled (Computed: {demo.total_lives_computed})</>
            )}
          </div>
        </div>

        {/* Sum Insured Range */}
        <div className="stat-card">
          <div className="stat-label">
            <Shield size={16} color="var(--success)" /> Sum Insured Tiers
          </div>
          <div className="stat-value" style={{ color: '#34d399' }}>
            {policy.sum_insured_tiers && policy.sum_insured_tiers.length > 0 ? (
              formatCurrency(policy.sum_insured_tiers[policy.sum_insured_tiers.length - 1].amount)
            ) : 'Custom'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            {policy.sum_insured_tiers ? `${policy.sum_insured_tiers.length} distinct grade tier(s)` : 'No tiers specified'}
          </div>
        </div>

        {/* Policy Tenure */}
        <div className="stat-card">
          <div className="stat-label">
            <Calendar size={16} color="var(--warning)" /> Policy Tenure
          </div>
          <div className="stat-value" style={{ color: '#fbbf24' }}>
            {policy.tenure_months ? `${policy.tenure_months} Months` : '12 Months'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Valid: {policy.policy_start_date} to {policy.policy_end_date}
          </div>
        </div>

      </div>

      {/* Main Grid: Family & Demographics + Tiers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
        
        {/* Family Definition & Composition */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Heart size={18} color="#f43f5e" /> Family Floater & Definition
            </h3>
            <span className="badge badge-primary">Floater Plan</span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '18px' }}>
            {[
              { label: 'Employee', covered: fam.employee },
              { label: 'Spouse', covered: fam.spouse },
              { label: 'Children', covered: fam.children },
              { label: 'Parents', covered: fam.parents },
              { label: 'Parents-in-law', covered: fam.parents_in_law },
            ].map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px 14px',
                  borderRadius: '8px',
                  background: item.covered ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                  border: `1px solid ${item.covered ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.82rem',
                  fontWeight: 500,
                  color: item.covered ? '#34d399' : 'var(--text-dim)'
                }}
              >
                {item.covered ? <Check size={14} /> : <X size={14} />}
                <span>{item.label}</span>
              </div>
            ))}
          </div>

          {fam.conditions && fam.conditions.length > 0 && (
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                Composition Conditions & Notes:
              </div>
              <ul style={{ paddingLeft: '18px', fontSize: '0.8rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {fam.conditions.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Census breakdown numbers */}
          <div style={{ marginTop: '18px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
              Member Census Breakdown:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Employees</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>{demo.num_employees || 0}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Spouses</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>{demo.num_spouses || 0}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Children</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>{demo.num_children || 0}</div>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Parents</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>{demo.num_parents || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sum Insured Tiers */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building size={18} color="var(--primary)" /> Sum Insured Structure
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Source Page: {policy.source_pages?.join(', ') || '1'}
            </span>
          </div>

          {policy.sum_insured_tiers && policy.sum_insured_tiers.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Grade / Category</th>
                  <th style={{ textAlign: 'right' }}>Sum Insured Amount</th>
                </tr>
              </thead>
              <tbody>
                {policy.sum_insured_tiers.map((tier, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 500 }}>{tier.grade_or_category || `Grade Tier ${idx + 1}`}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#818cf8' }}>
                      {formatCurrency(tier.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)' }}>
              No tiered structure parsed. Single floater applied.
            </div>
          )}

          {/* Quick Coverage Highlights */}
          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
              Core Coverage Limits at a Glance:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Room Rent:</span>
                <span style={{ fontWeight: 600, color: '#fff' }}>
                  {room.room_rent?.limit_amount ? `Max ${formatCurrency(room.room_rent.limit_amount)}/day` : '1% of SI'} 
                  {room.room_rent?.limit_percent_of_si ? ` (${room.room_rent.limit_percent_of_si}%)` : ''}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ color: 'var(--text-muted)' }}>ICU Charges:</span>
                <span style={{ fontWeight: 600, color: '#fff' }}>
                  {room.icu_charges?.limit_amount ? `Max ${formatCurrency(room.icu_charges.limit_amount)}/day` : '2% of SI'}
                  {room.icu_charges?.limit_percent_of_si ? ` (${room.icu_charges.limit_percent_of_si}%)` : ''}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Normal / C-Section Delivery:</span>
                <span style={{ fontWeight: 600, color: '#fff' }}>
                  {formatCurrency(mat.normal_delivery_metro?.limit_amount)} / {formatCurrency(mat.c_section_metro?.limit_amount)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                <span style={{ color: 'var(--text-muted)' }}>Pre / Post Hospitalization:</span>
                <span style={{ fontWeight: 600, color: '#fff' }}>
                  {room.pre_hospitalization_days?.limit_days || 30} Days / {room.post_hospitalization_days?.limit_days || 60} Days
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
