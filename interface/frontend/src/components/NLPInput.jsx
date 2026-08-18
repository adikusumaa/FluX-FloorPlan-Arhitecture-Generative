import React from 'react';

export default function NLPInput({ userText, onTextChange }) {
  return (
    <textarea
      className="apple-textarea"
      rows="4"
      placeholder="Contoh: Saya mau rumah 3 kamar tidur, 2 kamar mandi, luas 120m², dengan ruang tamu yang luas. Saya seorang lansia, jadi ingin akses mudah."
      value={userText}
      onChange={(e) => onTextChange(e.target.value)}
    />
  );
}