import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OverviewTab from './components/OverviewTab';
import BenefitsTab from './components/BenefitsTab';
import AuditTab from './components/AuditTab';
import PdfViewerTab from './components/PdfViewerTab';
import ExportsTab from './components/ExportsTab';
import ExtractModal from './components/ExtractModal';
import { Loader2, AlertCircle } from 'lucide-react';

export default function App() {
  const [policies, setPolicies] = useState([]);
  const [selectedPolicyId, setSelectedPolicyId] = useState(null);
  const [policyDetail, setPolicyDetail] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [targetPdfPage, setTargetPdfPage] = useState(1);
  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);
  const [reExtractTarget, setReExtractTarget] = useState(null);
  const [health, setHealth] = useState(null);
  const [loadingPolicies, setLoadingPolicies] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState(null);

  // Fetch server health & policies on mount
  useEffect(() => {
    fetchHealth();
    loadPolicies();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err) {
      console.warn('API server health check failed:', err);
    }
  };

  const loadPolicies = async (autoSelectId = null) => {
    setLoadingPolicies(true);
    try {
      const res = await fetch('/api/policies');
      if (res.ok) {
        const data = await res.json();
        const list = data.policies || [];
        setPolicies(list);
        
        const nextId = autoSelectId || (list.length > 0 ? list[0].id : null);
        if (nextId) {
          setSelectedPolicyId(nextId);
          loadPolicyDetail(nextId);
        }
      }
    } catch (err) {
      console.error('Failed to load policies:', err);
      setError('Unable to connect to backend server. Make sure "python main.py serve" is running.');
    } finally {
      setLoadingPolicies(false);
    }
  };

  const loadPolicyDetail = async (id) => {
    if (!id) return;
    setLoadingDetail(true);
    try {
      const res = await fetch(`/api/policies/${id}`);
      if (res.ok) {
        const data = await res.json();
        setPolicyDetail(data);
      } else {
        console.error('Failed to load policy detail for', id);
      }
    } catch (err) {
      console.error('Error fetching policy detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSelectPolicy = (id) => {
    setSelectedPolicyId(id);
    loadPolicyDetail(id);
  };

  const handleJumpToPdfPage = (pageNumber) => {
    setTargetPdfPage(pageNumber);
    setActiveTab('pdf');
  };

  const handleExtractionSuccess = (newPolicyId) => {
    loadPolicies(newPolicyId);
    setActiveTab('overview');
  };

  const handleOpenExtractModal = (reExtractInfo = null) => {
    setReExtractTarget(reExtractInfo);
    setIsExtractModalOpen(true);
  };

  return (
    <div className="app-layout">
      {/* Left Sidebar */}
      <Sidebar
        policies={policies}
        selectedPolicyId={selectedPolicyId}
        onSelectPolicy={handleSelectPolicy}
        onOpenExtractModal={() => handleOpenExtractModal(null)}
        health={health}
        loading={loadingPolicies}
      />

      {/* Main Content Area */}
      <main className="main-content">
        <Header
          policySummary={policyDetail?.summary}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          onOpenExtractModal={handleOpenExtractModal}
        />

        {error && (
          <div style={{ margin: '20px 28px', padding: '14px 18px', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: '10px', color: '#fda4af', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={18} />
            <span style={{ fontSize: '0.85rem' }}>{error}</span>
          </div>
        )}

        {loadingDetail ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '10px', padding: '100px 0' }}>
            <Loader2 size={24} className="animate-spin" />
            <span>Loading policy intelligence...</span>
          </div>
        ) : (
          <div className="animate-fade-in" style={{ flex: 1 }}>
            {activeTab === 'overview' && (
              <OverviewTab policyDetail={policyDetail} />
            )}

            {activeTab === 'benefits' && (
              <BenefitsTab 
                policyDetail={policyDetail} 
                onSelectPage={handleJumpToPdfPage} 
              />
            )}

            {activeTab === 'audit' && (
              <AuditTab policyDetail={policyDetail} />
            )}

            {activeTab === 'pdf' && (
              <PdfViewerTab 
                policyDetail={policyDetail} 
                targetPage={targetPdfPage} 
              />
            )}

            {activeTab === 'exports' && (
              <ExportsTab policyDetail={policyDetail} />
            )}
          </div>
        )}
      </main>

      {/* Extraction Modal */}
      <ExtractModal
        isOpen={isExtractModalOpen}
        onClose={() => {
          setIsExtractModalOpen(false);
          setReExtractTarget(null);
        }}
        onExtractionSuccess={handleExtractionSuccess}
        health={health}
        reExtractTarget={reExtractTarget}
      />
    </div>
  );
}
