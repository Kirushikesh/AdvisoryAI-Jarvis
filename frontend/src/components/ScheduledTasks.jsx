import { useState, useEffect } from 'react';
import './ScheduledTasks.css';

const API_BASE_URL = 'http://localhost:8000';

const ScheduledTasks = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchTasks = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/scheduled-tasks`);
            if (response.ok) {
                const data = await response.json();
                setTasks(data);
            }
        } catch (error) {
            console.error('Failed to fetch scheduled tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, []);

    const formatNextRun = (nextRun) => {
        if (!nextRun) return 'Not scheduled';
        const date = new Date(nextRun);
        return date.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getTaskIcon = (description) => {
        if (description.toLowerCase().includes('birthday')) return '🎂';
        if (description.toLowerCase().includes('tax')) return '📋';
        if (description.toLowerCase().includes('review')) return '📊';
        if (description.toLowerCase().includes('reminder')) return '⏰';
        return '📅';
    };

    if (loading) {
        return (
            <div className="scheduled-tasks glass-card">
                <h3>Scheduled Tasks</h3>
                <div className="loading">Loading...</div>
            </div>
        );
    }

    return (
        <div className="scheduled-tasks glass-card">
            <div className="tasks-header">
                <h3>Scheduled Tasks</h3>
                <span className="task-count">{tasks.length} tasks</span>
            </div>

            {tasks.length === 0 ? (
                <div className="no-tasks">
                    <span className="no-tasks-icon">📅</span>
                    <p>No scheduled tasks</p>
                </div>
            ) : (
                <div className="tasks-list">
                    {tasks.map((task) => (
                        <div key={task.id} className="task-item">
                            <div className="task-icon">
                                {getTaskIcon(task.description)}
                            </div>
                            <div className="task-content">
                                <div className="task-name">{task.name}</div>
                                <div className="task-description">{task.description}</div>
                                <div className="task-schedule">
                                    <span className="cron-badge">{task.cron}</span>
                                    <span className="next-run">Next: {formatNextRun(task.next_run)}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ScheduledTasks;
