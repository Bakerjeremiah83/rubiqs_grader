// src/components/Grader.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function Grader() {
  return (
    <div>
      <h1>Rubiqs Grader</h1>
      <p>This is the grader page.</p>
      <Link to="/">Back to Dashboard</Link>
    </div>
  );
}
