import { Link } from 'react-router-dom';
import NotificationPanel from '../components/NotificationPanel';
import './DashboardPage.css';

const DashboardPage = () => {
    return (
        <div className="dashboard-page animate-fade-in">
            <div className="page-header">
                <h1 className="page-title">Welcome back</h1>
                <p className="page-subtitle">Here's what's happening with your clients today</p>
            </div>

            <div className="dashboard-grid">
                <div className="dashboard-main">
                    <NotificationPanel />
                </div>

                <div className="dashboard-sidebar">
                    <div className="quick-actions glass-card">
                        <h3>Quick Actions</h3>
                        <div className="action-buttons">
                            <Link to="/chat" className="action-card">
                                <div className="action-icon chat-icon">
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z" stroke="currentColor" strokeWidth="2" />
                                    </svg>
                                </div>
                                <div className="action-info">
                                    <h4>Start a Chat</h4>
                                    <p>Talk to Jarvis or agents</p>
                                </div>
                            </Link>

                            <Link to="/clients" className="action-card">
                                <div className="action-icon upload-icon">
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                        <polyline points="17,8 12,3 7,8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    </svg>
                                </div>
                                <div className="action-info">
                                    <h4>Upload Files</h4>
                                    <p>Add client documents</p>
                                </div>
                            </Link>
                        </div>
                    </div>

                    <div className="stats-card glass-card">
                        <h3>Today's Overview</h3>
                        <div className="stats-grid">
                            <div className="stat-item">
                                <span className="stat-value">16</span>
                                <span className="stat-label">Active Clients</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-value">3</span>
                                <span className="stat-label">Pending Reviews</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-value">12</span>
                                <span className="stat-label">Documents</span>
                            </div>
                            <div className="stat-item">
                                <span className="stat-value">98%</span>
                                <span className="stat-label">Compliance</span>
                            </div>
                        </div>
                    </div>

                    <div className="agents-card glass-card">
                        <h3>Your Agents</h3>
                        <div className="agents-list">
                            <div className="agent-row">
                                <div className="agent-avatar jarvis">J</div>
                                <div className="agent-details">
                                    <span className="agent-name">Jarvis</span>
                                    <span className="agent-role">Main Assistant</span>
                                </div>
                                <div className="agent-status-dot online"></div>
                            </div>
                            <div className="agent-row">
                                <div className="agent-avatar atlas">A</div>
                                <div className="agent-details">
                                    <span className="agent-name">Atlas</span>
                                    <span className="agent-role">RAG Specialist</span>
                                </div>
                                <div className="agent-status-dot online"></div>
                            </div>
                            <div className="agent-row">
                                <div className="agent-avatar emma">E</div>
                                <div className="agent-details">
                                    <span className="agent-name">Emma</span>
                                    <span className="agent-role">Paraplanner</span>
                                </div>
                                <div className="agent-status-dot online"></div>
                            </div>
                            <div className="agent-row">
                                <div className="agent-avatar colin">C</div>
                                <div className="agent-details">
                                    <span className="agent-name">Colin</span>
                                    <span className="agent-role">Compliance</span>
                                </div>
                                <div className="agent-status-dot online"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
