import React, { useState, useEffect } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  Sparkles, 
  AlertCircle, 
  CheckCircle, 
  Loader2, 
  Cpu, 
  ShieldAlert 
} from 'lucide-react';

export default function ExtractModal({ 
  isOpen, 
  onClose, 
  onExtractionSuccess, 
  health,
  reExtractTarget,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [sampleList, setSampleList] = useState([]);
  const [selectedSample, setSelectedSample] = useState('');
  const [useUpload, setUseUpload] = useState(false);
  const [provider, setProvider] = useState('gemini');
  const [model, setModel] = useState('');
  const [noCache, setNoCache] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      if (reExtractTarget?.targetPath) {
        setSelectedSample(reExtractTarget.targetPath);
        setUseUpload(false);
        setNoCache(true); // Default to fresh re-extraction!
      }
      // Fetch available samples from API
      fetch('/api/samples')
        .then((res) => res.json())
        .then((data) => {
          if (data && data.files) {
            setSampleList(data.files);
            if (!reExtractTarget?.targetPath && data.files.length > 0) {
              setSelectedSample(data.files[0].path);
            }
          }
        })
        .catch((err) => console.error('Could not fetch samples:', err));
    }
  }, [isOpen, reExtractTarget]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatusMessage('Initializing extraction pipeline...');

    try {
      const formData = new FormData();
      if (useUpload && selectedFile) {
        formData.append('file', selectedFile);
      } else {
        formData.append('existing_path', selectedSample || 'samples/1.Policy Copy.pdf');
      }

      formData.append('provider', provider);
      if (model) formData.append('model', model);
      formData.append('no_cache', noCache);

      setStatusMessage(`Running retrieval & LLM extraction (${provider})... This may take 5-15 seconds...`);

      const res = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Extraction failed');
      }

      setStatusMessage('Done! Updating policy dashboard...');
      setTimeout(() => {
        setLoading(false);
        onExtractionSuccess(data.policy_id);
        onClose();
      }, 600);
    } catch (err) {
      console.error(err);
      setError(err.message || 'An unexpected error occurred during extraction.');
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '20px'
    }}>
      <div 
        className="glass-card animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '560px',
          background: '#0d1322',
          border: '1px solid var(--border-medium)',
          boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.8), 0 0 30px -5px var(--primary-glow)',
          padding: '24px',
          position: 'relative'
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ 
              width: '34px', 
              height: '34px', 
              borderRadius: '8px', 
              background: 'var(--primary-gradient)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#fff' 
            }}>
              <Sparkles size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>
                {reExtractTarget?.isReExtract ? 'Re-Extract Policy Intelligence' : 'Run Policy Extraction'}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {reExtractTarget?.policyName 
                  ? `Re-running extraction pipeline for: ${reExtractTarget.policyName}` 
                  : 'Parse GMC insurance policy PDF with grounding and QMS mapping'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="btn btn-ghost"
            style={{ padding: '6px' }}
            disabled={loading}
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          
          {/* Source Selection Toggle */}
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>
              Policy PDF Document:
            </label>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
              <button
                type="button"
                onClick={() => setUseUpload(false)}
                className={`btn ${!useUpload ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 1, fontSize: '0.8rem', padding: '8px' }}
              >
                <FileText size={14} />
                Select Existing Sample
              </button>
              <button
                type="button"
                onClick={() => setUseUpload(true)}
                className={`btn ${useUpload ? 'btn-primary' : 'btn-secondary'}`}
                style={{ flex: 1, fontSize: '0.8rem', padding: '8px' }}
              >
                <Upload size={14} />
                Upload Custom PDF
              </button>
            </div>

            {!useUpload ? (
              <select
                value={selectedSample}
                onChange={(e) => setSelectedSample(e.target.value)}
                className="form-select"
                disabled={loading}
              >
                {sampleList.map((s, idx) => (
                  <option key={idx} value={s.path}>
                    {s.name} ({Math.round(s.size_bytes / 1024)} KB)
                  </option>
                ))}
              </select>
            ) : (
              <div 
                style={{
                  border: '2px dashed var(--border-medium)',
                  borderRadius: '10px',
                  padding: '24px',
                  textAlign: 'center',
                  background: 'rgba(255, 255, 255, 0.02)',
                  cursor: 'pointer'
                }}
                onClick={() => document.getElementById('pdf-file-input').click()}
              >
                <input
                  id="pdf-file-input"
                  type="file"
                  accept="application/pdf"
                  style={{ display: 'none' }}
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  disabled={loading}
                />
                <Upload size={24} style={{ color: 'var(--primary)', margin: '0 auto 8px auto' }} />
                <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#fff' }}>
                  {selectedFile ? selectedFile.name : 'Click to browse or drop GMC PDF'}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                  Group Medical Cover policy schedule, endorsement, or wording PDF
                </div>
              </div>
            )}
          </div>

          {/* Engine / Provider Selection */}
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>
              LLM Provider:
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {[
                { id: 'gemini', name: 'Google Gemini', desc: 'gemini-3.5-flash-lite (Recommended)', badge: health?.providers_available?.gemini ? 'Active' : 'Key Needed' },
                { id: 'openai', name: 'OpenAI GPT', desc: 'gpt-4o-mini', badge: health?.providers_available?.openai ? 'Active' : 'Key Needed' },
                { id: 'ollama', name: 'Ollama Local', desc: 'Local private server', badge: 'Private' },
              ].map((p) => {
                const isSelected = provider === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => !loading && setProvider(p.id)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: '8px',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`,
                      background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                      cursor: loading ? 'default' : 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: isSelected ? '#fff' : 'var(--text-main)' }}>
                        {p.name}
                      </span>
                      <span style={{ fontSize: '0.65rem', color: isSelected ? '#a5b4fc' : 'var(--text-dim)' }}>
                        {p.badge}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                      {p.desc}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Cache Bypass Option */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              id="noCacheCheck"
              checked={noCache}
              onChange={(e) => setNoCache(e.target.checked)}
              disabled={loading}
              style={{ accentColor: 'var(--primary)' }}
            />
            <label htmlFor="noCacheCheck" style={{ fontSize: '0.78rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
              Force fresh extraction (bypass LLM response disk cache)
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{ 
              background: 'var(--danger-bg)', 
              border: '1px solid var(--danger-border)', 
              padding: '10px 14px', 
              borderRadius: '8px',
              color: '#fda4af',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Status message */}
          {loading && (
            <div style={{ 
              background: 'rgba(99, 102, 241, 0.1)', 
              border: '1px solid rgba(99, 102, 241, 0.3)', 
              padding: '12px 14px', 
              borderRadius: '8px',
              fontSize: '0.8rem',
              color: '#a5b4fc',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <Loader2 size={16} className="animate-spin" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Footer actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || (useUpload && !selectedFile)}
            >
              {loading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  {reExtractTarget?.isReExtract ? 'Re-Extracting...' : 'Extracting...'}
                </>
              ) : (
                <>
                  <Sparkles size={14} />
                  {reExtractTarget?.isReExtract ? 'Re-Extract Policy Now' : 'Start Extraction'}
                </>
              )}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}
