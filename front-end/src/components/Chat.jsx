// src/components/Chat.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function Chat() {
  return (
    <div>
      <h1>Rubiqs Chat</h1>
      <p>This is the chat page.</p>
      <Link to="/">Back to Dashboard</Link>
    </div>
  );
}
