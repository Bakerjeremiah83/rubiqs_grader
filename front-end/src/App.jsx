import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Notes from './components/Notes';
import Chat from './components/Chat';
import Math from './components/Math';
import Speak from './components/Speak';
import Grader from './components/Grader';
import Discussion from './components/Discussion';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/notes" element={<Notes />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/math" element={<Math />} />
        <Route path="/speak" element={<Speak />} />
        <Route path="/grader" element={<Grader />} />
        <Route path="/discussion" element={<Discussion />} />
      </Routes>
    </Router>
  );
}

export default App;
