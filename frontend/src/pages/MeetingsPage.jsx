import { useState, useEffect, useCallback } from 'react';
import './MeetingsPage.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Time slots from 8 AM to 6 PM
const TIME_SLOTS = [];
for (let h = 8; h <= 17; h++) {
    TIME_SLOTS.push(`${String(h).padStart(2, '0')}:00`);
}

function getWeekDates(baseDate) {
    const d = new Date(baseDate);
    const day = d.getDay(); // 0=Sun
    const start = new Date(d);
    start.setDate(d.getDate() - day); // go to Sunday
    const dates = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(start);
        date.setDate(start.getDate() + i);
        dates.push(date);
    }
    return dates;
}

function formatDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function isToday(d) {
    const today = new Date();
    return d.getFullYear() === today.getFullYear() &&
        d.getMonth() === today.getMonth() &&
        d.getDate() === today.getDate();
}

const MeetingsPage = () => {
    const [meetings, setMeetings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedMeeting, setSelectedMeeting] = useState(null);
    const [atlasInsight, setAtlasInsight] = useState('');
    const [atlasLoading, setAtlasLoading] = useState(false);
    const [weekOffset, setWeekOffset] = useState(0);

    const baseDate = new Date();
    baseDate.setDate(baseDate.getDate() + weekOffset * 7);
    const weekDates = getWeekDates(baseDate);

    useEffect(() => {
        fetchMeetings();
    }, []);

    const fetchMeetings = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/meetings`);
            if (res.ok) {
                const data = await res.json();
                setMeetings(data);
            }
        } catch (err) {
            console.error('Failed to fetch meetings:', err);
        } finally {
            setLoading(false);
        }
    };

    const openMeeting = useCallback((meeting) => {
        setSelectedMeeting(meeting);
        setAtlasInsight('');
        setAtlasLoading(false);
    }, []);

    const closeMeeting = useCallback(() => {
        setSelectedMeeting(null);
        setAtlasInsight('');
        setAtlasLoading(false);
    }, []);

    const getAtlasInsights = async () => {
        if (!selectedMeeting || atlasLoading) return;
        setAtlasLoading(true);
        setAtlasInsight('');

        const prompt = `I have an upcoming meeting with my client. Please help me prepare by providing key insights, talking points, and any important considerations.

Meeting Details:
- Client: ${selectedMeeting.client_name}
- Email: ${selectedMeeting.client_email}
- Subject: ${selectedMeeting.subject}
- Date: ${selectedMeeting.date}
- Time: ${selectedMeeting.start_time} – ${selectedMeeting.end_time}

Meeting Notes & Agenda:
${selectedMeeting.content}

Based on the above, please provide:
1. Key preparation points for this meeting
2. Important questions to ask the client
3. Any risks or sensitive topics to be mindful of
4. Recommended next steps to propose`;

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: prompt,
                    agent: 'atlas',
                }),
            });
            if (res.ok) {
                const data = await res.json();
                setAtlasInsight(data.response);
            } else {
                setAtlasInsight('Failed to get insights. Please try again.');
            }
        } catch (err) {
            console.error('Atlas insights error:', err);
            setAtlasInsight('Connection error. Please check that the backend is running.');
        } finally {
            setAtlasLoading(false);
        }
    };

    // Build a map: "YYYY-MM-DD|HH" -> meeting
    const meetingMap = {};
    meetings.forEach((m, idx) => {
        const hour = parseInt(m.start_time.split(':')[0], 10);
        const key = `${m.date}|${String(hour).padStart(2, '0')}`;
        meetingMap[key] = { ...m, colorIndex: idx % 6 };
    });

    const weekStart = weekDates[0];
    const weekEnd = weekDates[6];
    const weekLabel = `${MONTH_NAMES[weekStart.getMonth()]} ${weekStart.getDate()} – ${MONTH_NAMES[weekEnd.getMonth()]} ${weekEnd.getDate()}, ${weekEnd.getFullYear()}`;

    return (
        <div className="meetings-page animate-fade-in">
            <div className="page-header">
                <h1 className="page-title">Meetings</h1>
                <p className="page-subtitle">Upcoming client meetings for Abimanyu Chamika</p>
            </div>

            <div className="calendar-container">
                <div className="calendar-header">
                    <h2>📅 Weekly Calendar</h2>
                    <div className="calendar-nav">
                        <button
                            className="calendar-nav-btn"
                            onClick={() => setWeekOffset(w => w - 1)}
                            aria-label="Previous week"
                        >
                            ‹
                        </button>
                        <span className="calendar-week-label">{weekLabel}</span>
                        <button
                            className="calendar-nav-btn"
                            onClick={() => setWeekOffset(w => w + 1)}
                            aria-label="Next week"
                        >
                            ›
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="calendar-loading">
                        <div className="loading-dot" />
                        <div className="loading-dot" />
                        <div className="loading-dot" />
                    </div>
                ) : (
                    <div className="calendar-grid">
                        {/* Day headers row */}
                        <div className="calendar-corner" />
                        {weekDates.map((d) => (
                            <div
                                key={formatDate(d)}
                                className={`calendar-day-header ${isToday(d) ? 'is-today' : ''}`}
                            >
                                <div className="day-name">{DAY_NAMES[d.getDay()]}</div>
                                <div className="day-number">{d.getDate()}</div>
                            </div>
                        ))}

                        {/* Time slot rows */}
                        {TIME_SLOTS.map((slot) => {
                            const hour = slot.split(':')[0];
                            return (
                                <div className="calendar-row" key={slot}>
                                    <div className="time-label">
                                        {parseInt(hour) <= 12
                                            ? `${parseInt(hour)} AM`
                                            : `${parseInt(hour) - 12} PM`}
                                        {parseInt(hour) === 12 && 'PM' && ''}
                                    </div>
                                    {weekDates.map((d) => {
                                        const dateStr = formatDate(d);
                                        const key = `${dateStr}|${hour}`;
                                        const meeting = meetingMap[key];
                                        return (
                                            <div className="calendar-cell" key={key}>
                                                {meeting && (
                                                    <div
                                                        className={`meeting-event meeting-color-${meeting.colorIndex}`}
                                                        onClick={() => openMeeting(meeting)}
                                                        role="button"
                                                        tabIndex={0}
                                                        onKeyDown={(e) => e.key === 'Enter' && openMeeting(meeting)}
                                                    >
                                                        <span className="event-time">
                                                            {meeting.start_time} – {meeting.end_time}
                                                        </span>
                                                        <span className="event-subject">{meeting.subject}</span>
                                                        <span className="event-client">{meeting.client_name}</span>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Meeting Detail Modal */}
            {selectedMeeting && (
                <div className="meeting-modal-overlay" onClick={closeMeeting}>
                    <div className="meeting-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="meeting-modal-header">
                            <h3>{selectedMeeting.subject}</h3>
                            <button className="modal-close-btn" onClick={closeMeeting} aria-label="Close">
                                ✕
                            </button>
                        </div>

                        <div className="meeting-modal-body">
                            <div className="meeting-detail-row">
                                <div className="detail-icon">
                                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                <div>
                                    <div className="detail-label">Client</div>
                                    <div className="detail-value">{selectedMeeting.client_name}</div>
                                </div>
                            </div>

                            <div className="meeting-detail-row">
                                <div className="detail-icon">
                                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <polyline points="22,6 12,13 2,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                <div>
                                    <div className="detail-label">Email</div>
                                    <div className="detail-value">
                                        <a href={`mailto:${selectedMeeting.client_email}`}>
                                            {selectedMeeting.client_email}
                                        </a>
                                    </div>
                                </div>
                            </div>

                            <div className="meeting-detail-row">
                                <div className="detail-icon">
                                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                                        <polyline points="12 6 12 12 16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                <div>
                                    <div className="detail-label">Schedule</div>
                                    <div className="detail-value">
                                        {selectedMeeting.date} · {selectedMeeting.start_time} – {selectedMeeting.end_time}
                                    </div>
                                </div>
                            </div>

                            <div>
                                <div className="detail-label" style={{ marginBottom: '8px' }}>Meeting Notes & Agenda</div>
                                <div className="meeting-content-block">
                                    {selectedMeeting.content}
                                </div>
                            </div>
                        </div>

                        <div className="atlas-insights-section">
                            {!atlasInsight && (
                                <button
                                    className="atlas-btn"
                                    onClick={getAtlasInsights}
                                    disabled={atlasLoading}
                                >
                                    {atlasLoading ? (
                                        <>
                                            <div className="atlas-spinner" />
                                            Getting insights...
                                        </>
                                    ) : (
                                        <>
                                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                                                <circle cx="12" cy="12" r="4" fill="currentColor" />
                                                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                            </svg>
                                            Get Insights with Atlas
                                        </>
                                    )}
                                </button>
                            )}

                            {atlasInsight && (
                                <div className="atlas-response">
                                    <div className="atlas-response-header">
                                        <div className="atlas-avatar">A</div>
                                        <span>Atlas Insights</span>
                                    </div>
                                    <div className="atlas-response-body">
                                        {atlasInsight}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MeetingsPage;
