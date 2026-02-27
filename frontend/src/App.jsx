import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import ClientsPage from './pages/ClientsPage';
import MeetingsPage from './pages/MeetingsPage';
import LoginPage from './pages/LoginPage';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');

  if (!isAuthenticated) {
    return <LoginPage onLogin={(user) => {
      setIsAuthenticated(true);
      setUsername(user);
    }} />;
  }

  return (
    <Router>
      <div className="app-layout">
        <Sidebar username={username} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/meetings" element={<MeetingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
