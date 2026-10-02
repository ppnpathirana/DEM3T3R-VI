import { BACKEND_URL } from '../backendUrl';
import React, { useState } from 'react';
import { DiseaseItem } from '../App';

type CameraCardProps = {
  selectedCrop: string;
  diseases: DiseaseItem[];
};

export default function CameraCard({ selectedCrop, diseases }: CameraCardProps) {
  const [camKey, setCamKey] = useState(0);

  return (
    <div className="glass-card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="card-header-dot" />
          <span>Live Field Camera Feed & AI Detection</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setCamKey(k => k + 1)}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.15)',
              color: 'var(--text-secondary, #aaa)',
              borderRadius: '6px',
              fontSize: '0.7rem',
              padding: '3px 8px',
              cursor: 'pointer'
            }}
          >
            🔄 Reconnect
          </button>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #aaa)' }}>
            Crop: <span className="gradient-text" style={{ fontWeight: '700' }}>{selectedCrop.toUpperCase()}</span>
          </div>
        </div>
      </div>

      <div className="video-wrapper video-corners" style={{ minHeight: '340px', background: '#0a0812', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
        <img
          key={camKey}
          src={`${BACKEND_URL}/video_feed?k=${camKey}`}
          alt="Live Camera Stream"
          onError={() => setTimeout(() => setCamKey(k => k + 1), 2000)}
          style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
        />
        <div className="video-scan-line" />
        <div className="video-overlay-badge">
          <span>🔴</span> LIVE 1080P
        </div>

        {diseases && diseases.length > 0 && (
          <div className="detection-overlay">
            <div style={{ color: 'var(--success, #00ff88)', fontWeight: '700', marginBottom: '4px', fontSize: '0.8rem' }}>
              AI Diagnostics:
            </div>
            {diseases.slice(0, 3).map((disease, idx) => (
              <div key={idx} style={{ color: '#fff', fontSize: '0.75rem', marginBottom: '2px' }}>
                • {(disease.class || (disease as any).name || 'Anomaly').replace(/_/g, ' ')} ({((disease.confidence ?? 0.8) * 100).toFixed(0)}%)
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-dim, #777)', display: 'flex', justifyContent: 'space-between' }}>
        <span>Hardware: ESP32-S3 Cam Stream</span>
        <span>Resolution: 1920×1080 @ 30fps</span>
      </div>
    </div>
  );
}
