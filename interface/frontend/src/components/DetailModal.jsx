import React from 'react';

/**
 * DetailModal - Menampilkan detail denah dengan metrik RFP-A dan saran lingkungan.
 * @param {Object} plan - Data denah yang dipilih.
 * @param {Function} onClose - Fungsi untuk menutup modal.
 */
export default function DetailModal({ plan, onClose }) {
  if (!plan) return null;

  // Ekstraksi data dengan nilai default jika tidak tersedia
  const {
    id = 'N/A',
    image_url = '',
    rank = 1,
    // RFP-A Scores
    rfpa = {
      stage1: { compliant: true, roomCounts: [1, 2, 1, 1, 1] }, // [living, bed, bath, kitchen, balcony]
      stage2: { graphId: 'G-123', editDistance: 0 },           // kategori graph, atau edit distance
      stage3: { quadrant: 'Quadrant I' },                     // posisi ruang
      stage4: { rfp_iou: 0.85 },                              // RFP-IoU (0-1)
    },
    compositeScore = 0.85,    // skor keseluruhan (misal rata-rata)
    // Lingkungan
    location = {
      lat: -6.2,
      lng: 106.8,
    },
    orientation = {
      livingRoom: 'South',
      bedrooms: 'North-East',
    },
    suggestions = {
      lighting: 'Orientasikan ruang tamu menghadap selatan untuk pencahayaan maksimal.',
      ventilation: 'Buat cross-ventilation dengan bukaan di sisi timur dan barat.',
      // noise dihilangkan sesuai permintaan
    },
  } = plan;

  // Fungsi untuk menampilkan stage secara visual
  const renderStage = (title, value, detail = '') => (
    <div className="border-b border-gray-100 py-3 last:border-0">
      <div className="flex justify-between items-start">
        <span className="font-medium text-gray-700">{title}</span>
        <span className="text-sm font-semibold text-blue-600">{value}</span>
      </div>
      {detail && <p className="text-xs text-gray-500 mt-1">{detail}</p>}
    </div>
  );

  // Detail ruangan per stage
  const stage1Detail = rfpa.stage1.compliant
    ? `Jumlah ruang sesuai: ${rfpa.stage1.roomCounts.join(' · ')} (Ruang tamu, Kamar tidur, Kamar mandi, Dapur, Balkon)`
    : `Jumlah ruang tidak sesuai: ${rfpa.stage1.roomCounts.join(' · ')}`;

  const stage2Detail = rfpa.stage2.editDistance === 0
    ? 'Struktur graf identik dengan acuan (RFP-GED = 0)'
    : `Edit distance = ${rfpa.stage2.editDistance}`;

  const stage3Detail = `Kuadran lokasi ruang: ${rfpa.stage3.quadrant}`;

  const stage4Detail = `RFP-IoU = ${(rfpa.stage4.rfp_iou * 100).toFixed(1)}% (semakin tinggi semakin mirip)`;

  // Saran lingkungan
  const envSuggestions = [
    { label: 'Pencahayaan', value: suggestions.lighting },
    { label: 'Ventilasi', value: suggestions.ventilation },
    // { label: 'Kebisingan', value: suggestions.noise }, // sengaja dihilangkan
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
        {/* Tombol tutup */}
        <button
          className="absolute top-3 right-4 text-gray-400 hover:text-gray-700 text-3xl font-light transition-colors"
          onClick={onClose}
          aria-label="Tutup"
        >
          &times;
        </button>

        {/* Header */}
        <h2 className="text-2xl font-bold text-gray-800 mb-1">
          Denah #{rank}
          <span className="ml-3 text-sm font-normal text-gray-500">ID: {id}</span>
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Berdasarkan preferensi Anda, denah ini memiliki skor komposit{' '}
          <span className="font-semibold text-blue-600">
            {(compositeScore * 100).toFixed(1)}%
          </span>
        </p>

        {/* Gambar */}
        <div className="bg-gray-100 rounded-xl overflow-hidden mb-5">
          <img
            src={image_url}
            alt={`Denah ${rank}`}
            className="w-full h-auto max-h-[50vh] object-contain"
          />
        </div>

        {/* RFP-A Metrics */}
        <div className="bg-gray-50 rounded-xl p-4 mb-5">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">RFP-A</span>
            Evaluasi 4 Tahap
          </h3>
          <div className="divide-y divide-gray-200">
            {renderStage('1. Jumlah Ruang', rfpa.stage1.compliant ? '✅ Sesuai' : '❌ Tidak sesuai', stage1Detail)}
            {renderStage('2. Struktur Graf (RFP-GED)', rfpa.stage2.editDistance === 0 ? '✅ Identik' : `Edit distance ${rfpa.stage2.editDistance}`, stage2Detail)}
            {renderStage('3. Lokasi Ruang', rfpa.stage3.quadrant || '—', stage3Detail)}
            {renderStage('4. Geometri (RFP-IoU)', `${(rfpa.stage4.rfp_iou * 100).toFixed(1)}%`, stage4Detail)}
          </div>
        </div>

        {/* Saran Lingkungan & Orientasi */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center gap-2">
            <span className="text-xl">🌿</span> Saran Lingkungan
          </h3>
          <div className="text-sm space-y-1">
            <p className="text-gray-700">
              <span className="font-medium">Lokasi:</span> {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
            </p>
            <p className="text-gray-700">
              <span className="font-medium">Orientasi ruang tamu:</span> {orientation.livingRoom || 'Belum ditentukan'}
            </p>
            <p className="text-gray-700">
              <span className="font-medium">Orientasi kamar tidur:</span> {orientation.bedrooms || 'Belum ditentukan'}
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