import React from 'react';

const getScoreColor = (score) => {
  if (score >= 0.8) return 'score-green';
  if (score >= 0.6) return 'score-blue';
  if (score >= 0.4) return 'score-orange';
  return 'score-red';
};

export default function OutputGallery({ results, onCardClick }) {
  if (!results || results.length === 0) return null;

  return (
    <section className="results-section">
      <div className="results-header">
        <h2 className="section-title">Top 5 Floor Plans for You</h2>
        <p className="section-subtitle">
          Based on your preferences, here are the highest‑scoring floor plan recommendations.
        </p>
      </div>

      <div className="results-grid">
        {results.map((plan, index) => (
          <div
            key={plan.id || index}
            className="result-card"
            onClick={() => onCardClick && onCardClick(plan)}
            style={{ cursor: 'pointer' }}
          >
            <div className="result-card-image">
              <img src={plan.image_url} alt={plan.id || `Floor Plan ${index + 1}`} />
              <div className="result-card-badge">#{plan.rank || index + 1}</div>
            </div>

            <div className="result-card-body">
              <div className="result-card-header">
                <span className="result-card-style">{plan.style || 'RPLAN'}</span>
                <span className="result-card-score">
                  {plan.scores?.composite?.toFixed(2) || '0.00'}
                </span>
              </div>

              <div className="result-card-stats">
                <div className="stat-item">
                  <span className="stat-label">EUI</span>
                  <span className="stat-value">{plan.energy?.EUI || '-'} kWh/m²</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Area</span>
                  <span className="stat-value">{plan.energy?.total_area || '-'} m²</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Status</span>
                  <span
                    className={`stat-value ${
                      plan.energy?.fire_safety_status === 'OK' ? 'stat-ok' : 'stat-warning'
                    }`}
                  >
                    {plan.energy?.fire_safety_status || '-'}
                  </span>
                </div>
              </div>

              <div className="result-card-scores">
                {['O', 'C', 'R', 'A'].map((label, idx) => {
                  const keys = [
                    'spatial_openness',
                    'circulation_efficiency',
                    'layout_rationality',
                    'adaptability',
                  ];
                  const val = plan.scores?.[keys[idx]] ?? 0;
                  return (
                    <div key={idx} className="score-dot">
                      <span className="score-dot-label">{label}</span>
                      <div
                        className={`score-dot-bar ${getScoreColor(val)}`}
                        style={{ width: `${val * 100}%` }}
                      />
                      <span className="score-dot-value">{val.toFixed(2)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}