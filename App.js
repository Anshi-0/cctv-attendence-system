import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import LiveCamera from './pages/LiveCamera';
import Persons from './pages/Persons';
import AttendanceLogs from './pages/AttendanceLogs';
import UnknownFaces from './pages/UnknownFaces';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="brand-icon">
              <svg viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2"/>
                <circle cx="16" cy="16" r="6" fill="currentColor" opacity="0.3"/>
                <circle cx="16" cy="16" r="3" fill="currentColor"/>
                <path d="M8 8 L12 12 M24 8 L20 12 M8 24 L12 20 M24 24 L20 20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="brand-text">
              <span className="brand-name">CCTV Watch</span>
              <span className="brand-sub">Attendance System</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <IconGrid /> Dashboard
            </NavLink>
            <NavLink to="/camera" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <IconCamera /> Live Camera
            </NavLink>
            <NavLink to="/persons" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <IconUsers /> Persons
            </NavLink>
            <NavLink to="/logs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <IconLog /> Attendance Logs
            </NavLink>
            <NavLink to="/unknown" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <IconAlert /> Unknown Faces
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <span className="version-tag">v2.0.0 · MTCNN + dlib</span>
          </div>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/camera" element={<LiveCamera />} />
            <Route path="/persons" element={<Persons />} />
            <Route path="/logs" element={<AttendanceLogs />} />
            <Route path="/unknown" element={<UnknownFaces />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

const IconGrid = () => (
  <svg viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
);
const IconCamera = () => (
  <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"/></svg>
);
const IconUsers = () => (
  <svg viewBox="0 0 20 20" fill="currentColor"><path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>
);
const IconLog = () => (
  <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z" clipRule="evenodd"/></svg>
);
const IconAlert = () => (
  <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
);

export default App;
