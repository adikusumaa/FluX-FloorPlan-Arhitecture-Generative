import React from 'react';

/**
 * DetailModal - Displays floor plan details with RFP-A metrics and environmental suggestions.
 * @param {Object} plan - Selected floor plan data.
 * @param {Function} onClose - Function to close the modal.
 */
export default function DetailModal({ plan, onClose }) {
  if (!plan) return null;

  // Extract data with default values if not available
  const {
    id = 'N/A',
    image_url = '',
    rank = 1,
    // RFP-A Scores
    rfpa = {
      stage1: { compliant: true, roomCounts: [1, 2, 1, 1, 1] }, // [living, bed, bath, kitchen, balcony]
      stage2: { graphId: 'G-123', editDistance: 0 },
      stage3: { quadrant: 'Quadrant I' },
      stage4: { rfp_iou: 0.85 },
    },
    compositeScore = 0.85,
    // Environment
    location = {
      lat: -6.2,
      lng: 106.8,
    },
    orientation = {
      livingRoom: 'South',
      bedrooms: 'North-East',
    },
    suggestions = {
      lighting: 'Orient the living room toward the south for maximum daylight.',
      ventilation: 'Create cross-ventilation with openings on the east and west sides.',
    },
  } = plan;

  // Helper to render a stage row
  const renderStage = (title, value, detail = '') => (
    <div className="border-b border-gray-100 py-3 last:border-0">
      <div className="flex justify-between items-start">
        <span className="font-medium text-gray-700">{title}</span>
        <span className="text-sm font-semibold text-blue-600">{value}</span>
      </div>
      {detail && <p className="text-xs text-gray-500 mt-1">{detail}</p>}
    </div>
  );

  const stage1Detail = rfpa.stage1.compliant
    ? `Room counts match: ${rfpa.stage1.roomCounts.join(' · ')} (Living room, Bedrooms, Bathrooms, Kitchen, Balcony)`
    : `Room counts do not match: ${rfpa.stage1.roomCounts.join(' · ')}`;

  const stage2Detail =
    rfpa.stage2.editDistance === 0
      ? 'Graph structure identical to reference (RFP-GED = 0)'
      : `Edit distance = ${rfpa.stage2.editDistance}`;

  const stage3Detail = `Room location quadrant: ${rfpa.stage3.quadrant}`;

  const stage4Detail = `RFP-IoU = ${(rfpa.stage4.rfp_iou * 100).toFixed(1)}% (higher is better)`;

  const envSuggestions = [
    { label: 'Lighting', value: suggestions.lighting },
    { label: 'Ventilation', value: suggestions.ventilation },
  ];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl max-w-4xl w-full max-h-[95vh] overflow-y-auto p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          className="absolute top-3 right-4 text-gray-400 hover:text-gray-700 text-3xl font-light transition-colors"
          onClick={onClose}
          aria-label="Close"
        >
          &times;
        </button>

        {/* Header */}
        <h2 className="text-2xl font-bold text-gray-800 mb-1">
          Floor Plan #{rank}
          <span className="ml-3 text-sm font-normal text-gray-500">ID: {id}</span>
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Based on your preferences, this floor plan has a composite score of{' '}
          <span className="font-semibold text-blue-600">
            {(compositeScore * 100).toFixed(1)}%
          </span>
        </p>

        {/* Image */}
        <div className="bg-gray-100 rounded-xl overflow-hidden mb-5">
          <img
            src={image_url}
            alt={`Floor Plan ${rank}`}
            className="w-full h-auto max-h-[50vh] object-contain"
          />
        </div>

        {/* RFP-A Metrics */}
        <div className="bg-gray-50 rounded-xl p-4 mb-5">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">RFP-A</span>
            4‑Stage Evaluation
          </h3>
          <div className="divide-y divide-gray-200">
            {renderStage(
              '1. Room Count',
              rfpa.stage1.compliant ? '✅ Compliant' : '❌ Non‑compliant',
              stage1Detail
            )}
            {renderStage(
              '2. Graph Structure (RFP‑GED)',
              rfpa.stage2.editDistance === 0 ? '✅ Identical' : `Edit distance ${rfpa.stage2.editDistance}`,
              stage2Detail
            )}
            {renderStage('3. Room Location', rfpa.stage3.quadrant || '—', stage3Detail)}
            {renderStage('4. Geometry (RFP‑IoU)', `${(rfpa.stage4.rfp_iou * 100).toFixed(1)}%`, stage4Detail)}
          </div>
        </div>

        {/* Environmental Suggestions & Orientation */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center gap-2">
            <span className="text-xl">🌿</span> Environmental Suggestions
          </h3>
          <div className="text-sm space-y-1">
            <p className="text-gray-700">
              <span className="font-medium">Location:</span> {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
            </p>
            <p className="text-gray-700">
              <span className="font-medium">Living room orientation:</span> {orientation.livingRoom || 'Not specified'}
            </p>
            <p className="text-gray-700">
              <span className="font-medium">Bedroom orientation:</span> {orientation.bedrooms || 'Not specified'}
            </p>
            <div className="mt-3 pt-3 border-t border-blue-200">
              {envSuggestions.map((item, idx) => (
                <div key={idx} className="flex items-start gap-2 mt-1">
                  <span className="text-blue-500 mt-0.5">•</span>
                  <span>
                    <span className="font-medium">{item.label}:</span> {item.value || '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}