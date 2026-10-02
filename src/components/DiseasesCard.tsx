/**
 * @file DiseasesCard.tsx
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */

import { DiseaseItem } from '../App';

type DiseasesCardProps = {
  diseases: DiseaseItem[];
};

export default function DiseasesCard({ diseases }: DiseasesCardProps) {
  const getSeverity = (confidence: number) => {
    if (confidence > 0.7) return 'critical';
    if (confidence > 0.4) return 'warning';
    return 'low';
  };

  const getColor = (confidence: number) => {
    if (confidence > 0.7) return 'var(--critical)';
    if (confidence > 0.4) return 'var(--warning)';
    return 'var(--success)';
  };

  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        Detected Diseases
      </div>
      
      {diseases.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '20px', 
          color: 'var(--text-dim)',
          fontSize: '0.85rem'
        }}>
          No diseases detected
        </div>
      ) : (
        <div>
          {diseases.map((disease, idx) => {
            const conf = typeof disease?.confidence === 'number' ? disease.confidence : 0.5;
            const diseaseName = (disease?.class || (disease as any)?.name || 'Plant Anomaly').replace(/_/g, ' ');
            const severity = getSeverity(conf);
            const color = getColor(conf);
            const percentage = (conf * 100).toFixed(1);
            const count = disease?.count ?? 1;
            
            return (
              <div key={idx} className={`disease-item ${severity}`}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  marginBottom: '6px'
                }}>
                  <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>
                    {diseaseName}
                  </span>
                  <span style={{ color, fontWeight: '700' }}>
                    {percentage}%
                  </span>
                </div>
                
                <div className="progress-bar-wrap">
                  <div 
                    className="progress-bar"
                    style={{ 
                      width: `${percentage}%`,
                      background: `linear-gradient(90deg, ${color}, ${color}88)`
                    }}
                  />
                </div>
                
                <div style={{ 
                  marginTop: '6px', 
                  fontSize: '0.7rem', 
                  color: 'var(--text-dim)',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span>Severity: {severity.charAt(0).toUpperCase() + severity.slice(1)}</span>
                  <span>Detected {count} times</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
