// src/components/Math.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function Math() {
  return (
    <div>
      <h1>Rubiqs Math</h1>
      <p>This is the Math page.</p>
      <Link to="/">Back to Dashboard</Link>
    </div>
  );
}
