import React, { useState } from 'react';
import useStore from './store/useStore';
import { generateFloorplan } from './services/api';
import MapPicker from './components/MapPicker';
import NLPInput from './components/NLPInput';
import OutputGallery from './components/OutputGallery';
import DetailModal from './components/DetailModal';
import './App.css';

function App() {
  const {
    userText,
    weights,
    coordinates,
    loading,
    results,
    parsedData,
    statusMessage,
    setUserText,
    setWeights,
    setCoordinates,
    setLoading,
    setResults,
    setError,
    setStatusMessage,
    reset,
  } = useStore();

  const [selectedPlan, setSelectedPlan] = useState(null);

  const handleGenerate = async () => {
    if (!userText) {
      setStatusMessage('Mohon tuliskan kebutuhan rumah Anda.');
      return;
    }

    setLoading(true);
    setResults(null);
    setStatusMessage('Sedang memproses kebutuhan Anda...');

    try {
      const response = await generateFloorplan(userText, weights, coordinates);
      setStatusMessage('Selesai! Berikut 5 denah terbaik.');
      setResults(response.data, response.parsed_data);
    } catch (error) {
      console.error(error);
      setStatusMessage('Error: Gagal menghubungi server. Pastikan backend berjalan.');
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWeightChange = (index, value) => {
    const newWeights = [...weights];
    newWeights[index] = value;
    setWeights(newWeights);
  };

  return (
    <div className="app-container">
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

      <section className="hero">
        <h1 className="hero-title">
          Desain Denah Impian<br />dengan Kecerdasan Buatan
        </h1>
        <p className="hero-subtitle">
          Cukup tuliskan kebutuhan rumah Anda, FluX! akan menghasilkan 5 denah terbaik 
          yang optimal secara energi dan tata ruang.
        </p>
      </section>

      <section className="input-section">
        <div className="input-card">
          <div className="input-header">
            <h2 className="section-title">Deskripsikan Kebutuhan Anda</h2>
            <p className="section-subtitle">Tulis secara natural, FluX! akan memahami dan menghasilkan denah terbaik.</p>
          </div>

          <div className="input-body">
            {/* MAP PICKER */}
            <div className="mb-6">
              <label className="block font-medium mb-2 text-gray-700">Pilih Lokasi (klik peta)</label>
              <MapPicker coordinates={coordinates} onCoordinatesChange={setCoordinates} />
              <p className="text-xs text-gray-500 mt-1">
                Latitude: {coordinates.lat.toFixed(5)}, Longitude: {coordinates.lng.toFixed(5)}
              </p>
            </div>

            {/* NLP INPUT */}
            <NLPInput
              userText={userText}
              onTextChange={setUserText}
              weights={weights}
              onWeightChange={handleWeightChange}
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

            {statusMessage && (
              <p className={`status-message ${statusMessage.includes('Selesai') ? 'status-success' : statusMessage.includes('Error') ? 'status-error' : 'status-info'}`}>
                {statusMessage}
              </p>
            )}

            {parsedData && (
              <div className="parsed-container">
                <h4>Hasil Pemahaman AI:</h4>
                <pre className="parsed-json">
                  {JSON.stringify(parsedData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* OUTPUT GALLERY */}
      <OutputGallery results={results} onCardClick={setSelectedPlan} />

      {/* DETAIL MODAL */}
      {selectedPlan && (
        <DetailModal plan={selectedPlan} onClose={() => setSelectedPlan(null)} />
      )}
    </div>
  );
}

export default App;