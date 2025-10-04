// src/components/Discussion.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function Discussion() {
  return (
    <div>
      <h1>Rubiqs Discussion</h1>
      <p>This is the discussion page.</p>
      <Link to="/">Back to Dashboard</Link>
    </div>
  );
}
