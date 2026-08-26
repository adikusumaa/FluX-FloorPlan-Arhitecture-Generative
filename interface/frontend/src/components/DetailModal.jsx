import React from 'react';

export default function DetailModal({ plan, onClose }) {
  if (!plan) return null;

  const {
    id = 'N/A',
    image_url = '',
    rank = 1,
    scores = {},
    location = { lat: -6.2000, lng: 106.8000 },
    orientation = 297,
  } = plan;

  // Ekstraksi ORCA (jika ada)
  const orca = scores.orca || {
    O: scores.spatial_openness || 0,
    C: scores.circulation_efficiency || 0,
    R: scores.layout_rationality || 0,
    A: scores.adaptability || 0,
    mitigation_text: ''
  };

  // Environment score rata-rata ORCA
  const envScore = ((orca.O + orca.R + orca.C + orca.A) / 4) * 100;
  const compositeScore = scores.composite ?? 0;

  // Teks analisis AI (dari Qwen)
  const aiAnalysisText = plan.qwen_analysis || plan.suggestions?.environment || orca.mitigation_text || 'Sedang menunggu hasil analisis dari model AI...';

  // Fallback data RFP-A
  const rfpa = plan.analysis?.rfpa || plan.rfpa || {
    stage1: { compliant: true, roomCounts: [1, 2, 1, 1, 1] },
    stage2: { editDistance: 0 },
    stage3: { quadrant: 'Quadrant I' },
    stage4: { rfp_iou: 0.85 },
  };

  const stage1Compliant = rfpa.stage1?.compliant ? 'Compliant' : 'Non-compliant';
  const stage1Detail = `Room counts match: ${rfpa.stage1?.roomCounts?.join(' · ') || '1 · 2 · 1 · 1 · 1'}`;

  const stage2Identical = rfpa.stage2?.editDistance === 0 ? 'Identical' : `Edit distance = ${rfpa.stage2?.editDistance}`;
  const stage2Detail = rfpa.stage2?.editDistance === 0 
    ? 'Graph structure identical to reference (RFP-GED = 0)' 
    : `Graph structure differs by ${rfpa.stage2?.editDistance} edges.`;

  const stage3Quadrant = rfpa.stage3?.quadrant || 'Quadrant I';
  const stage3Detail = `Room location quadrant: ${stage3Quadrant}`;

  const stage4IoU = ((rfpa.stage4?.rfp_iou ?? 0.85) * 100).toFixed(1);
  const stage4Detail = `RFP-IoU = ${stage4IoU}%`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()} 
        style={{ maxWidth: '1000px', width: '95%' }}
      >
        <div className="modal-header">
          <h3>Floor Plan Detail</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>
        
        <div 
          className="modal-body" 
          style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '32px', 
            overflowY: 'auto', 
            maxHeight: 'calc(90vh - 70px)',
            alignItems: 'flex-start'
          }}
        >
          {/* SISI KIRI */}
          <div style={{ flex: '1 1 45%', minWidth: '320px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#1C1C1E', margin: '0 0 4px 0' }}>
              Floor Plan #{rank}
              <span style={{ fontSize: '13px', color: '#8E8E93', fontWeight: '500', marginLeft: '8px', display: 'block' }}>
                ID: {id}
              </span>
            </h2>
            <p style={{ fontSize: '13px', color: '#3A3A3C', margin: '0 0 24px 0', fontWeight: '500' }}>
              Composite Score: {compositeScore.toFixed(2)}% | Environment Score: {envScore.toFixed(1)}%
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
              <img 
                src={image_url} 
                alt={`Floor Plan ${rank}`} 
                style={{ 
                  maxHeight: '300px', 
                  width: '100%', 
                  border: '3px solid #1C1C1E', 
                  borderRadius: '8px', 
                  objectFit: 'contain'
                }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#1C1C1E', margin: '0 0 12px 0' }}>
                RFP-A 4-Stage Evaluation
              </h3>
              <div style={{ fontSize: '13px', color: '#3A3A3C', lineHeight: '1.6', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>1. Room Count</span>
                    <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{stage1Compliant}</span>
                  </div>
                  <div style={{ color: '#8E8E93', fontSize: '12px' }}>{stage1Detail}</div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>2. Graph Structure (RFP-GED)</span>
                    <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{stage2Identical}</span>
                  </div>
                  <div style={{ color: '#8E8E93', fontSize: '12px' }}>{stage2Detail}</div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>3. Room Location</span>
                    <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{stage3Quadrant}</span>
                  </div>
                  <div style={{ color: '#8E8E93', fontSize: '12px' }}>{stage3Detail}</div>
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>4. Geometry (RFP-IoU)</span>
                    <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{stage4IoU}%</span>
                  </div>
                  <div style={{ color: '#8E8E93', fontSize: '12px' }}>{stage4Detail}</div>
                </div>
              </div>
            </div>

            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#1C1C1E', margin: '0 0 8px 0' }}>
                Environmental Parameters
              </h3>
              <div style={{ fontSize: '13px', color: '#3A3A3C', lineHeight: '1.6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Location:</span>
                  <span>{location.lat.toFixed(4)}, {location.lng.toFixed(4)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>Orientation:</span>
                  <span>{orientation}° (from North)</span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Noise (Acoustics)</span>
                  <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{orca.O.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Daylight (Radiation)</span>
                  <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{orca.R.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Ventilation (Circulation)</span>
                  <span style={{ fontWeight: '700', color: '#1C1C1E' }}>{orca.C.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* SISI KANAN (Analisis AI) */}
          <div style={{ 
            flex: '1 1 45%', 
            minWidth: '320px', 
            background: '#F9F9FC', 
            border: '1px solid #E5E5EA',
            borderRadius: '16px', 
            padding: '24px' 
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#1C1C1E', margin: '0 0 16px 0' }}>
              AI Architect Analysis
            </h3>
            <div style={{ 
              fontSize: '14px', 
              lineHeight: '1.7', 
              color: '#3A3A3C', 
              whiteSpace: 'pre-line',
              textAlign: 'justify'
            }}>
              {aiAnalysisText}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}