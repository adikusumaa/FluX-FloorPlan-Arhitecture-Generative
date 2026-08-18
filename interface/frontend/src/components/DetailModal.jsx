import React from 'react';

export default function DetailModal({ plan, onClose }) {
  if (!plan) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 text-3xl font-light"
          onClick={onClose}
        >
          &times;
        </button>
        <img
          src={plan.image_url}
          alt="Detail Denah"
          className="w-full rounded-xl mb-4"
        />
        <h3 className="text-2xl font-bold">Skor Komposit: {plan.scores?.composite?.toFixed(2) || 'N/A'}</h3>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <div><strong>Keterbukaan:</strong> {plan.scores?.spatial_openness?.toFixed(2)}</div>
          <div><strong>Sirkulasi:</strong> {plan.scores?.circulation_efficiency?.toFixed(2)}</div>
          <div><strong>Rasionalitas:</strong> {plan.scores?.layout_rationality?.toFixed(2)}</div>
          <div><strong>Adaptabilitas:</strong> {plan.scores?.adaptability?.toFixed(2)}</div>
        </div>
        {plan.suggestions && (
          <div className="mt-4 p-4 bg-gray-50 rounded-xl">
            <h4 className="font-semibold mb-2">Saran Lingkungan</h4>
            <ul className="list-disc list-inside text-sm">
              <li>Pencahayaan: {plan.suggestions.lighting}</li>
              <li>Ventilasi: {plan.suggestions.ventilation}</li>
              <li>Kebisingan: {plan.suggestions.noise}</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}