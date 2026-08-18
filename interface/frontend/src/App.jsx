import { useState } from 'react';
import MapPicker from './components/MapPicker'
import NLPInput from './components/NLPInput'
import OutputGallery from './components/OutputGallery'
import useStore from './store/useStore'
import { generateFloorplan } from './services/api'
import './App.css'
import mapIcon from './assets/LocationPNG.png';
import DetailModal from './components/DetailModal';

function App() {
  const { 
    coordinates, 
    userText,
    loading, 
    results, 
    error, 
    setCoordinates, 
    setUserText,
    setLoading, 
    setResults, 
    setError 
  } = useStore()

  // State untuk modal peta
  const [showMapModal, setShowMapModal] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const handleGenerate = async () => {
    if (!userText || userText.length < 10) {
      alert('Deskripsi minimal 10 karakter')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await generateFloorplan(coordinates, userText)
      setResults(data)
    } catch (err) {
      setError(err.message || 'Gagal generate')
    }
  }

  // Fungsi untuk menutup modal setelah koordinat dipilih
  const handleCoordinatesChange = (coords) => {
    setCoordinates(coords)
    setShowMapModal(false) // tutup modal setelah klik
  }

  return (
    <div className="app-container">
      {/* ===== NAVIGASI ===== */}
      <nav className="nav-bar">
        <div className="nav-content">
          <div className="nav-logo">
            <span className="logo-text">FluX!</span>
          </div>
          <div className="nav-links">
            <a href="#" className="nav-link">Beranda</a>
            <a href="#" className="nav-link">Tentang</a>
            <button className="nav-cta">Mulai</button>
          </div>
        </div>
      </nav>

      {/* ===== HERO ===== */}
      <section className="hero">
        <h1 className="hero-title">
          Desain Denah Impian<br />dengan Kecerdasan Buatan
        </h1>
        <p className="hero-subtitle">
          Cukup tuliskan kebutuhan rumah Anda, FluX! akan menghasilkan 5 denah terbaik 
          yang optimal secara energi dan tata ruang.
        </p>
      </section>

      {/* ===== INPUT SECTION ===== */}
      <section className="input-section">
        <div className="input-card">
          <div className="input-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 className="section-title">Deskripsikan Kebutuhan Anda</h2>
              <p className="section-subtitle">
                Tulis secara natural, FluX! akan memahami dan menghasilkan denah terbaik.
              </p>
            </div>
            {/* Ikon Peta di pojok kanan */}
            <button 
                className="map-icon-btn"
                onClick={() => setShowMapModal(true)}
                title="Klik untuk pilih lokasi di peta"
            >
            <img src={mapIcon} alt="Pilih lokasi" className="map-icon-img" />
            </button>
          </div>

          <div className="input-body">
            <NLPInput 
              userText={userText}
              onTextChange={setUserText}
            />

            <button
              className={`apple-button ${loading ? 'apple-button-loading' : ''}`}
              onClick={handleGenerate}
              disabled={loading || !userText}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Memproses...
                </>
              ) : (
                'Generate Denah'
              )}
            </button>

            {error && (
              <p className="status-message status-error">{error}</p>
            )}
          </div>
        </div>
      </section>

      {/* ===== HASIL ===== */}
      {results && (
        <section className="results-section">
          <div className="results-header">
            <h2 className="section-title">5 Denah Terbaik untuk Anda</h2>
            <p className="section-subtitle">
              Berdasarkan preferensi Anda, berikut rekomendasi denah dengan skor tertinggi.
            </p>
          </div>
          <OutputGallery results={results} onCardClick={setSelectedPlan} />
        </section>
      )}

      {/* ===== MODAL MAP PICKER ===== */}
      {showMapModal && (
        <div className="modal-overlay" onClick={() => setShowMapModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Pilih Lokasi di Peta</h3>
              <button className="modal-close" onClick={() => setShowMapModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              <MapPicker 
                coordinates={coordinates} 
                onCoordinatesChange={handleCoordinatesChange} 
              />
              <p className="map-hint">Klik pada peta untuk memilih lokasi, peta akan otomatis tertutup.</p>
            </div>
          </div>
        </div>
      )}

      {/* DETAIL MODAL */}
        {selectedPlan && (
            <DetailModal plan={selectedPlan} onClose={() => setSelectedPlan(null)} />
      )}
    </div>
  )
}

export default App