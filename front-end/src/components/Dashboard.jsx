// src/components/Dashboard.jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Modal from './Modal';

import logo from '../assets/rubiqs-logo-v2.png';
import graderImg from '../assets/blue-rubiqs-grader.png';

export default function Dashboard() {
  const [isModalOpen, setModalOpen] = useState(false);

  // Replace with real logic if needed
  const hasTool = (tool) => true;

  return (
    <>
      {/* Logo + subtitle */}
      <div className="logo-header">
        <img src={logo} alt="Rubiqs Logo" />
        <div className="subtitle">
          Mastery Tech for Modern Learners<br />
          by Rubiqs Design Studios
        </div>
      </div>

      {/* Dashboard card */}
      <main className="dashboard-card" role="main" aria-label="Rubiqs Suite Dashboard">
        <h1 className="dashboard-title">
          <span className="title-main">RUBIQS SUITE</span>
          <span className="title-sub">DASHBOARD</span>
        </h1>

        <div className="tile-container">
          
            <Link to="/grader" className="tile only-image" aria-label="Rubiqs Grader">
                <img src={graderImg} alt="Rubiqs Grader" />
            </Link>
        </div>
      </main>

      {/* Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
