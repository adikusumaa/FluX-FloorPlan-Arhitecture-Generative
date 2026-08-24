import React from 'react';

export default function NLPInput({ userText, onTextChange }) {
  return (
    <textarea
      className="apple-textarea"
      rows="4"
      placeholder="Example: I want a house with 3 bedrooms, 2 bathrooms, 120m², with a spacious living room. I am elderly, so I want easy access."
      value={userText}
      onChange={(e) => onTextChange(e.target.value)}
    />
  );
}