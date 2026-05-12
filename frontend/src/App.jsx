import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Chat from './components/Chat';
import { api, setAuthToken } from './api';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setAuthToken(token);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogin = () => setIsLoggedIn(true);
  const handleLogout = () => {
    localStorage.removeItem('token');
    setAuthToken(null);
    setIsLoggedIn(false);
  };

  return (
    <Routes>
      <Route path="/login" element={<Login onLogin={handleLogin} />} />
      <Route
        path="/chat"
        element={isLoggedIn ? <Chat onLogout={handleLogout} /> : <Navigate to="/login" />}
      />
      <Route path="*" element={<Navigate to={isLoggedIn ? "/chat" : "/login"} />} />
    </Routes>
  );
}

export default App;
