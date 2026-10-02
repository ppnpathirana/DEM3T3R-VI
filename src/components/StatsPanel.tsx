import { DiseaseItem } from '../App';

type StatsPanelProps = {
  efficiency: number;
  patrolRoute: number;
  diseases: DiseaseItem[];
};

export default function StatsPanel({ efficiency, patrolRoute, diseases }: StatsPanelProps) {
  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        System Statistics
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        <div className="stat-pill">
          <div className="gauge-wrap">
            <div style={{ fontSize: '1.5rem', fontWeight: '700' }} className="gradient-text">
              {efficiency}%
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>Efficiency</div>
          </div>
        </div>
        
        <div className="stat-pill">
          <div style={{ marginBottom: '6px', fontSize: '0.65rem', color: 'var(--text-dim)' }}>
            Patrol Route
          </div>
          <div className="patrol-track">
            <div 
              className="patrol-fill"
              style={{ width: `${patrolRoute}%` }}
            />
          </div>
          <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
            {patrolRoute}% Complete
          </div>
        </div>
        
        <div className="stat-pill">
          <div style={{ fontSize: '1.5rem', fontWeight: '700' }} className="gradient-text-warm">
            {diseases.length}
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>Active Issues</div>
        </div>
      </div>
    </div>
  );
}
