import React from 'react';

export default function Modal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" aria-hidden={!isOpen}>
      <div
        className="modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="compassTitle"
      >
        <h2 id="compassTitle">Rubiqs Compass</h2>
        <p>Modal content goes here.</p>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
