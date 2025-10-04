// src/components/Speak.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function Speak() {
  return (
    <div>
      <h1>Rubiqs Speak</h1>
      <p>This is the speak page.</p>
      <Link to="/">Back to Dashboard</Link>
    </div>
  );
}
