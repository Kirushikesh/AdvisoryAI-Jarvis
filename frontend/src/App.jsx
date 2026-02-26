import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import ClientsPage from './pages/ClientsPage';
import MeetingsPage from './pages/MeetingsPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/meetings" element={<MeetingsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
