import React from 'react';

export default function CrewSummary({ summary }) {
  if (!summary) return null;

  // Parsing teks berdasarkan tag [LABEL]
  const sections = {};
  let currentSection = 'INTRO';
  sections[currentSection] = [];

  summary.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) return;

    const match = trimmed.match(/^\[(.*?)\]$/);
    if (match) {
      currentSection = match[1];
      sections[currentSection] = [];
    } else {
      sections[currentSection].push(trimmed);
    }
  });

  const renderList = (items, type) => (
    <ul className={`summary-list ${type}`}>
      {items.map((item, idx) => {
        const cleanItem = item.replace(/^-\s*/, '').replace(/\*\*/g, '');
        return (
          <li key={idx} className="summary-list-item">
            <span className={`list-bullet ${type}`}>
              {type === 'pros' ? '✓' : type === 'cons' ? '✕' : '•'}
            </span>
            <span>{cleanItem}</span>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="crew-summary-container">
      <div className="crew-summary-card">
        <h3 className="crew-summary-title">AI Executive Summary</h3>

        <div className="crew-summary-body">
          <div className="summary-header-cards">
            {sections['LOCATION'] && (
              <div className="summary-mini-card">
                <span className="mini-card-label">📍 Location</span>
                <span className="mini-card-value">{sections['LOCATION'].join(' ')}</span>
              </div>
            )}
            {sections['BEST CANDIDATE'] && (
              <div className="summary-mini-card highlight">
                <span className="mini-card-label">🏆 Best Candidate</span>
                <span className="mini-card-value">{sections['BEST CANDIDATE'].join(' ')}</span>
              </div>
            )}
          </div>

          <div className="summary-split-grid">
            {sections['PROS'] && (
              <div className="summary-section-block">
                <h4 className="section-block-title pros-title">Pros</h4>
                {renderList(sections['PROS'], 'pros')}
              </div>
            )}
            {sections['CONS'] && (
              <div className="summary-section-block">
                <h4 className="section-block-title cons-title">Cons</h4>
                {renderList(sections['CONS'], 'cons')}
              </div>
            )}
          </div>

          {sections['MAIN RECOMMENDATIONS'] && (
            <div className="summary-section-block full-width">
              <h4 className="section-block-title neutral-title">💡 Main Recommendations</h4>
              {renderList(sections['MAIN RECOMMENDATIONS'], 'neutral')}
            </div>
          )}

          {sections['CONCLUSION'] && (
            <div className="summary-conclusion">
              <div className="conclusion-badge">Conclusion</div>
              <p>{sections['CONCLUSION'].join(' ')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}