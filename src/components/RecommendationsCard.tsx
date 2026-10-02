import { Recommendation } from '../App';

type RecommendationsCardProps = {
  recommendation: Recommendation | null;
};

export default function RecommendationsCard({ recommendation }: RecommendationsCardProps) {
  if (!recommendation) {
    return (
      <div className="glass-card">
        <div className="card-header">
          <div className="card-header-dot" />
          AI Recommendations
        </div>
        <div style={{ 
          textAlign: 'center', 
          padding: '20px', 
          color: 'var(--text-dim)',
          fontSize: '0.85rem'
        }}>
          Select a crop and detect disease to get AI recommendations
        </div>
      </div>
    );
  }

  const sections = [
    { key: 'reason', title: '🔍 REASON', className: 'reason', content: recommendation.reason },
    { key: 'recovery', title: '💊 RECOVERY PLAN', className: 'recovery', content: recommendation.recovery },
    { key: 'prediction', title: '🔮 PREDICTION', className: 'prediction', content: recommendation.prediction },
    { key: 'fertilizer', title: '🌱 FERTILIZER & TREATMENT', className: 'fertilizer', content: recommendation.fertilizer },
  ];

  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        AI Recommendations
      </div>
      
      <div style={{ marginBottom: '12px', fontSize: '0.85rem' }}>
        <span style={{ color: 'var(--text-secondary)' }}>Disease: </span>
        <span className="gradient-text" style={{ fontWeight: '600' }}>
          {recommendation.disease.replace(/_/g, ' ')}
        </span>
        <span style={{ color: 'var(--warning)', marginLeft: '8px' }}>
          ({(recommendation.confidence * 100).toFixed(1)}%)
        </span>
      </div>
      
      {sections.map((section) => (
        <div key={section.key} className={`rec-section ${section.className}`}>
          <div className="rec-title">{section.title}</div>
          <div className="rec-content">
            {section.content || 'Loading...'}
          </div>
        </div>
      ))}
    </div>
  );
}
