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
        {results.map((plan, index) => {
          const compositeScore = plan.scores?.composite ?? 0;
          const energy = plan.energy || {};
          
          // Mengambil nilai ORCA aktual dari plan.scores.orca
          const orca = plan.scores?.orca || { O: 0, R: 0, C: 0, A: 0 };
          
          const metrics = [
            { label: 'O', val: orca.O },
            { label: 'R', val: orca.R },
            { label: 'C', val: orca.C },
            { label: 'A', val: orca.A },
          ];

          return (
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
                  <span className="result-card-style">{plan.style || 'Modern'}</span>
                  <span className="result-card-score">
                    {compositeScore.toFixed(2)}
                  </span>
                </div>

                <div className="result-card-stats">
                  <div className="stat-item">
                    <span className="stat-label">EUI</span>
                    <span className="stat-value">
                      {energy.EUI !== undefined ? `${energy.EUI.toFixed(2)} kWh/m²` : '-'}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Area</span>
                    <span className="stat-value">
                      {energy.total_area !== undefined ? `${energy.total_area.toFixed(2)} m²` : '-'}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Status</span>
                    <span className={`stat-value ${energy.fire_safety_status === 'OK' ? 'stat-ok' : 'stat-warning'}`}>
                      {energy.fire_safety_status || '-'}
                    </span>
                  </div>
                </div>

                <div className="result-card-scores">
                  {metrics.map(({ label, val }) => (
                    <div key={label} className="score-dot">
                      <span className="score-dot-label">{label}</span>
                      <div
                        className={`score-dot-bar ${getScoreColor(val)}`}
                        style={{ width: `${Math.min(val * 100, 100)}%` }}
                      />
                      <span className="score-dot-value">{val.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}