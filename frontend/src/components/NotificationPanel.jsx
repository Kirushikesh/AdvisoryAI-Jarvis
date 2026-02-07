import { useState, useEffect } from 'react';
import './NotificationPanel.css';

const API_BASE = 'http://localhost:8000';

const NotificationPanel = () => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchNotifications();
        // Poll for new notifications every 30 seconds
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/notifications`);
            if (response.ok) {
                const data = await response.json();
                setNotifications(data.map(n => ({
                    ...n,
                    timestamp: new Date(n.timestamp),
                    agent: 'jarvis'
                })));
            }
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
            // Fallback to mock data if API is not available
            setNotifications([
                {
                    id: '1',
                    type: 'info',
                    title: 'Jarvis Offline',
                    message: 'Backend server is not running. Start it with: uv run uvicorn jarvis.api:app --reload',
                    timestamp: new Date(),
                    read: false,
                    agent: 'jarvis'
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (date) => {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / (1000 * 60));
        const hours = Math.floor(diff / (1000 * 60 * 60));

        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return date.toLocaleDateString();
    };

    const getTypeIcon = (type) => {
        switch (type) {
            case 'action':
                return (
                    <svg viewBox="0 0 24 24" fill="none">
                        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="currentColor" strokeWidth="2" />
                        <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                );
            case 'warning':
                return (
                    <svg viewBox="0 0 24 24" fill="none">
                        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" strokeWidth="2" />
                        <path d="M12 9v4M12 17h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                );
            case 'success':
                return (
                    <svg viewBox="0 0 24 24" fill="none">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke="currentColor" strokeWidth="2" />
                        <path d="M22 4L12 14.01l-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                );
            default:
                return (
                    <svg viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                        <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                );
        }
    };

    const markAsRead = (id) => {
        setNotifications(notifications.map(n =>
            n.id === id ? { ...n, read: true } : n
        ));
    };

    const unreadCount = notifications.filter(n => !n.read).length;

    return (
        <div className="notification-panel glass-card">
            <div className="notification-header">
                <div className="notification-title">
                    <h3>Notifications</h3>
                    {unreadCount > 0 && (
                        <span className="unread-badge">{unreadCount}</span>
                    )}
                </div>
                <button className="btn-text" onClick={fetchNotifications}>
                    {loading ? 'Loading...' : 'Refresh'}
                </button>
            </div>

            <div className="notification-list">
                {notifications.length === 0 ? (
                    <div className="notification-empty">
                        <p>No notifications yet</p>
                    </div>
                ) : (
                    notifications.map((notification, index) => (
                        <div
                            key={notification.id}
                            className={`notification-item ${notification.read ? 'read' : 'unread'} type-${notification.type}`}
                            onClick={() => markAsRead(notification.id)}
                            style={{ animationDelay: `${index * 0.1}s` }}
                        >
                            <div
                                className="notification-icon"
                                style={{ color: 'var(--color-jarvis)' }}
                            >
                                {getTypeIcon(notification.type)}
                            </div>
                            <div className="notification-content">
                                <div className="notification-meta">
                                    <span className="notification-agent">jarvis</span>
                                    <span className="notification-time">{formatTime(notification.timestamp)}</span>
                                </div>
                                <h4 className="notification-item-title">{notification.title}</h4>
                                <p className="notification-message">{notification.message}</p>
                            </div>
                            {!notification.read && <div className="unread-dot"></div>}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default NotificationPanel;
