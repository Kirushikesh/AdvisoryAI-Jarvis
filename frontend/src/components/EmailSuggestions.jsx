import { useState, useEffect } from 'react';
import './EmailSuggestions.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EmailIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" strokeWidth="2" />
        <path d="M2 8l10 6 10-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);

const CheckIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

const EditIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);

const RejectIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
        <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);

const SpinnerIcon = () => (
    <svg className="spinner-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeOpacity="0.25" />
        <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
);

const EmailCard = ({ suggestion, onApprove, onReject }) => {
    const [expanded, setExpanded] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editedBody, setEditedBody] = useState(suggestion.body);
    const [status, setStatus] = useState('idle'); // idle | loading | success | error
    const [statusMsg, setStatusMsg] = useState('');
    const [removing, setRemoving] = useState(false);

    const formatTime = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    };

    const bodyPreview = suggestion.body.split('\n').slice(0, 2).join(' ').trim();

    const handleApprove = async () => {
        setStatus('loading');
        try {
            const res = await fetch(
                `${API_BASE}/api/email-suggestions/${suggestion.id}/approve`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(editing && editedBody !== suggestion.body ? { edited_body: editedBody } : {}),
                }
            );
            const data = await res.json();
            if (res.ok && data.success) {
                setStatus('success');
                setStatusMsg(data.message || 'Email sent and archived.');
                setTimeout(() => {
                    setRemoving(true);
                    setTimeout(() => onApprove(suggestion.id), 400);
                }, 1800);
            } else {
                throw new Error(data.detail || 'Unknown error');
            }
        } catch (err) {
            setStatus('error');
            setStatusMsg(err.message);
        }
    };

    const handleReject = async () => {
        try {
            await fetch(`${API_BASE}/api/email-suggestions/${suggestion.id}/reject`, {
                method: 'POST',
            });
        } catch (_) {
            // Fire-and-forget; dismiss optimistically
        }
        setRemoving(true);
        setTimeout(() => onReject(suggestion.id), 400);
    };

    const handleEditToggle = () => {
        if (editing) {
            setEditing(false);
        } else {
            setEditing(true);
            setExpanded(true);
        }
    };

    return (
        <div className={`email-card ${removing ? 'removing' : ''}`}>
            {/* Header */}
            <div className="email-card-header">
                <div className="email-header-left">
                    <div className="jarvis-icon-badge">
                        <EmailIcon />
                    </div>
                    <div className="email-header-meta">
                        <span className="suggested-by-label">
                            <span className="jarvis-dot" />
                            Suggested by Jarvis
                        </span>
                        <span className="email-date">{formatTime(suggestion.created_at)}</span>
                    </div>
                </div>
                <span className="client-chip">{suggestion.client_name}</span>
            </div>

            {/* Email Details */}
            <div className="email-card-body">
                <div className="email-field">
                    <span className="field-label">To</span>
                    <span className="field-value to-value">{suggestion.to}</span>
                </div>
                <div className="email-field">
                    <span className="field-label">Subject</span>
                    <span className="field-value subject-value">{suggestion.subject}</span>
                </div>

                {/* Body preview / edit */}
                {editing ? (
                    <div className="email-body-edit">
                        <textarea
                            className="body-textarea"
                            value={editedBody}
                            onChange={(e) => setEditedBody(e.target.value)}
                            rows={8}
                        />
                    </div>
                ) : (
                    <div className="email-body-preview">
                        <p className={`body-text ${expanded ? 'expanded' : 'collapsed'}`}>
                            {expanded ? suggestion.body : bodyPreview}
                        </p>
                        <button
                            className="toggle-expand"
                            onClick={() => setExpanded(!expanded)}
                        >
                            {expanded ? 'Show less ↑' : 'Read full email ↓'}
                        </button>
                    </div>
                )}
            </div>

            {/* Status message */}
            {status === 'success' && (
                <div className="email-status-msg success-msg">
                    <CheckIcon /> {statusMsg}
                </div>
            )}
            {status === 'error' && (
                <div className="email-status-msg error-msg">
                    ⚠ {statusMsg}
                </div>
            )}

            {/* Footer */}
            <div className="email-card-footer">
                <div className="emma-verified-badge">
                    <div className="emma-avatar">E</div>
                    <span>Verified by Emma</span>
                </div>

                {status !== 'success' && (
                    <div className="email-actions">
                        <button
                            className="action-btn approve-btn"
                            onClick={handleApprove}
                            disabled={status === 'loading'}
                            title="Approve & Send"
                        >
                            {status === 'loading' ? (
                                <><SpinnerIcon /> Sending…</>
                            ) : (
                                <><CheckIcon /> Approve & Send</>
                            )}
                        </button>
                        <button
                            className="action-btn edit-btn"
                            onClick={handleEditToggle}
                            disabled={status === 'loading'}
                            title={editing ? 'Cancel edit' : 'Edit email'}
                        >
                            <EditIcon /> {editing ? 'Cancel' : 'Edit'}
                        </button>
                        <button
                            className="action-btn reject-btn"
                            onClick={handleReject}
                            disabled={status === 'loading'}
                            title="Reject suggestion"
                        >
                            <RejectIcon /> Reject
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const EmailSuggestions = () => {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchSuggestions = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/email-suggestions`);
            if (res.ok) {
                const data = await res.json();
                setSuggestions(data);
            }
        } catch (err) {
            console.error('Failed to fetch email suggestions:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSuggestions();
        const interval = setInterval(fetchSuggestions, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleApproved = (id) => {
        setSuggestions(prev => prev.filter(s => s.id !== id));
    };

    const handleRejected = (id) => {
        setSuggestions(prev => prev.filter(s => s.id !== id));
    };

    if (loading) return null;
    if (suggestions.length === 0) return null;

    return (
        <div className="email-suggestions-panel glass-card">
            <div className="suggestions-header">
                <div className="suggestions-title">
                    <div className="suggestions-title-icon">
                        <EmailIcon />
                    </div>
                    <div>
                        <h3>Email Drafts</h3>
                        <p className="suggestions-subtitle">Jarvis has prepared these for your review</p>
                    </div>
                </div>
                <span className="suggestions-count-badge">{suggestions.length}</span>
            </div>

            <div className="suggestions-list">
                {suggestions.map((s, i) => (
                    <EmailCard
                        key={s.id}
                        suggestion={s}
                        onApprove={handleApproved}
                        onReject={handleRejected}
                        style={{ animationDelay: `${i * 0.08}s` }}
                    />
                ))}
            </div>
        </div>
    );
};

export default EmailSuggestions;
