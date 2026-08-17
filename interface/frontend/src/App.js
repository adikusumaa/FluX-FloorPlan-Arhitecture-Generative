// ============================================================
// FILE: frontend/src/App.js
// ============================================================
import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [userText, setUserText] = useState('');
  const [weights, setWeights] = useState([25, 25, 25, 25]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [parsedData, setParsedData] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  const weightLabels = ['Keterbukaan', 'Sirkulasi', 'Rasionalitas', 'Adaptabilitas'];

  const handleGenerate = async () => {
    setLoading(true);
    setResults(null);
    setParsedData(null);
    setStatusMessage('Sedang memproses kebutuhan Anda...');

    try {
      const response = await axios.post(`${API_BASE_URL}/generate`, {
        user_text: userText,
        weights: weights.map(w => w / 100)
      });
      
      setStatusMessage('Selesai! Berikut 5 denah terbaik.');
      setResults(response.data.data);
      setParsedData(response.data.parsed_data);
    } catch (error) {
      console.error(error);
      setStatusMessage('Error: Gagal menghubungi server. Pastikan backend berjalan.');
    } finally {
      setLoading(false);
    }
  };

  const handleWeightChange = (index, value) => {
    const newWeights = [...weights];
    newWeights[index] = parseInt(value);
    setWeights(newWeights);
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'score-green';
    if (score >= 0.6) return 'score-blue';
    if (score >= 0.4) return 'score-orange';
    return 'score-red';
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
            <textarea
              className="apple-textarea"
              rows="4"
              placeholder="Contoh: Saya mau rumah 3 kamar tidur, 2 kamar mandi, luas 120m², dengan ruang tamu yang luas. Saya seorang lansia, jadi ingin akses mudah."
              value={userText}
              onChange={(e) => setUserText(e.target.value)}
            />
            
            <div className="weight-section">
              <label className="weight-label">Prioritas Desain (sesuaikan sesuai preferensi)</label>
              <div className="weight-grid">
                {weightLabels.map((label, idx) => (
                  <div key={idx} className="weight-item">
                    <div className="weight-header">
                      <span className="weight-name">{label}</span>
                      <span className="weight-value">{weights[idx]}%</span>
                    </div>
                    <input
                      type="range"
                      className="apple-slider"
                      min="0"
                      max="100"
                      value={weights[idx]}
                      onChange={(e) => handleWeightChange(idx, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            </div>

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

      {results && (
        <section className="results-section">
          <div className="results-header">
            <h2 className="section-title">5 Denah Terbaik untuk Anda</h2>
            <p className="section-subtitle">Berdasarkan preferensi Anda, berikut rekomendasi denah dengan skor tertinggi.</p>
          </div>

          <div className="results-grid">
            {results.map((plan) => (
              <div key={plan.id} className="result-card">
                <div className="result-card-image">
                  <img src={plan.image_url} alt={plan.id} />
                  <div className="result-card-badge">#{plan.rank}</div>
                </div>
                <div className="result-card-body">
                  <div className="result-card-header">
                    <span className="result-card-style">{plan.style}</span>
                    <span className="result-card-score">
                      {plan.scores.composite.toFixed(2)}
                    </span>
                  </div>
                  <div className="result-card-stats">
                    <div className="stat-item">
                      <span className="stat-label">EUI</span>
                      <span className="stat-value">{plan.energy.EUI} kWh/m²</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Luas</span>
                      <span className="stat-value">{plan.energy.total_area} m²</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Status</span>
                      <span className={`stat-value ${plan.energy.fire_safety_status === 'OK' ? 'stat-ok' : 'stat-warning'}`}>
                        {plan.energy.fire_safety_status}
                      </span>
                    </div>
                  </div>
                  <div className="result-card-scores">
                    {['O', 'C', 'R', 'A'].map((label, idx) => {
                      const keys = ['spatial_openness', 'circulation_efficiency', 'layout_rationality', 'adaptability'];
                      const val = plan.scores[keys[idx]];
                      return (
                        <div key={idx} className="score-dot">
                          <span className="score-dot-label">{label}</span>
                          <div className={`score-dot-bar ${getScoreColor(val)}`} style={{ width: `${val * 100}%` }}></div>
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
      )}
    </div>
  );
}

export default App;