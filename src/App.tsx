import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Home } from './pages/Home';
import { Upload } from './pages/Upload';
import { Results } from './pages/Results';
import { AdCreatives } from './pages/AdCreatives';
import { Dashboard } from './pages/Dashboard';

function App() {
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('theme') === 'dark'
  );

  // Apply theme on load
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const toggleTheme = () => {
    setDarkMode(!darkMode);
  };

  return (
    <Router>
      <div
        className={`min-h-screen ${
          darkMode
            ? 'bg-gray-900 text-gray-200'
            : 'bg-gray-50 text-gray-900'
        }`}
      >
        {/* Pass toggleTheme and darkMode to Navigation */}
        <Navigation toggleTheme={toggleTheme} darkMode={darkMode} />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/results" element={<Results />} />
            <Route path="/ad-creatives" element={<AdCreatives />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
