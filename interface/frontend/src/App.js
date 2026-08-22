import { useState } from 'react';
import MapPicker from './components/MapPicker';
import NLPInput from './components/NLPInput';
import OutputGallery from './components/OutputGallery';
import DetailModal from './components/DetailModal';
import useStore from './store/useStore';
import { generateFloorplan } from './services/api';
import mapIcon from './assets/LocationPNG.png';
import './App.css';

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
    setError,
  } = useStore();

  const [showMapModal, setShowMapModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  const handleGenerate = async () => {
    if (!userText || userText.length < 10) {
      alert('Please describe your dream home (min. 10 characters).');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await generateFloorplan(coordinates, userText);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleCoordinatesChange = (coords) => {
    setCoordinates(coords);
    setShowMapModal(false);
  };

  return (
    <div className="app-container">
      {/* ===== NAV ===== */}
      <nav className="nav-bar">
        <div className="nav-content">
          <div className="nav-logo">
            <span className="logo-text">FluX!</span>
          </div>
          <div className="nav-links">
            <a href="#" className="nav-link">Home</a>
            <a href="#" className="nav-link">About</a>
            <button className="nav-cta">Get Started</button>
          </div>
        </div>
      </nav>

      {/* ===== HERO ===== */}
      <section className="hero">
        <h1 className="hero-title">
          Design Your Dream Floor Plan<br />with Artificial Intelligence
        </h1>
        <p className="hero-subtitle">
          Simply describe your home requirements, and FluX! will generate the 5 best floor plans
          optimised for energy efficiency and spatial quality.
        </p>
      </section>

      {/* ===== INPUT SECTION ===== */}
      <section className="input-section">
        <div className="input-card">
          <div
            className="input-header"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <h2 className="section-title">Describe Your Needs</h2>
              <p className="section-subtitle">
                Write naturally – FluX! will understand and produce the best layouts.
              </p>
            </div>
            {/* Map Icon Button */}
            <button
              className="map-icon-btn"
              onClick={() => setShowMapModal(true)}
              title="Click to select location on map"
            >
              <img src={mapIcon} alt="Select location" className="map-icon-img" />
            </button>
          </div>

          <div className="input-body">
            <NLPInput userText={userText} onTextChange={setUserText} />

            <button
              className={`apple-button ${loading ? 'apple-button-loading' : ''}`}
              onClick={handleGenerate}
              disabled={loading || !userText}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Processing...
                </>
              ) : (
                'Generate Floor Plans'
              )}
            </button>

            {error && <p className="status-message status-error">{error}</p>}
          </div>
        </div>
      </section>

      {/* ===== RESULTS ===== */}
      {results && results.length > 0 && (
        <section className="results-section">
          <div className="results-header">
            <h2 className="section-title">Top 5 Floor Plans for You</h2>
            <p className="section-subtitle">
              Based on your preferences, here are the highest‑scoring recommendations.
            </p>
          </div>
          <OutputGallery results={results} onCardClick={setSelectedPlan} />
        </section>
      )}

      {/* ===== MAP MODAL ===== */}
      {showMapModal && (
        <div className="modal-overlay" onClick={() => setShowMapModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Select Location on Map</h3>
              <button className="modal-close" onClick={() => setShowMapModal(false)}>
                ✕
              </button>
            </div>
            <div className="modal-body">
              <MapPicker
                coordinates={coordinates}
                onCoordinatesChange={handleCoordinatesChange}
              />
              <p className="map-hint">Click on the map to pick a location – the modal will close automatically.</p>
            </div>
          </div>
        </div>
      )}

      {/* ===== DETAIL MODAL ===== */}
      {selectedPlan && (
        <DetailModal plan={selectedPlan} onClose={() => setSelectedPlan(null)} />
      )}
    </div>
  );
}

export default App;