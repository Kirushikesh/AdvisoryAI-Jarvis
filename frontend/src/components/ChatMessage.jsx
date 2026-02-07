import './ChatMessage.css';

const ChatMessage = ({ message, agentColor }) => {
    const isAgent = message.sender === 'agent';

    const formatTime = (date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Format message content - handle markdown-like formatting
    const formatContent = (content) => {
        if (!content) return '';

        // Split by newlines and process each line
        const lines = content.split('\n');

        return lines.map((line, index) => {
            // Handle numbered lists (1. 2. 3. etc)
            if (/^\d+\.\s/.test(line)) {
                const text = line.replace(/^\d+\.\s/, '');
                return (
                    <div key={index} className="list-item numbered">
                        <span className="list-marker">{line.match(/^\d+/)[0]}.</span>
                        <span>{formatInlineText(text)}</span>
                    </div>
                );
            }

            // Handle bullet points (- or *)
            if (/^[-*]\s/.test(line)) {
                const text = line.replace(/^[-*]\s/, '');
                return (
                    <div key={index} className="list-item bullet">
                        <span className="list-marker">•</span>
                        <span>{formatInlineText(text)}</span>
                    </div>
                );
            }

            // Handle headers (lines that are all caps or start with #)
            if (/^#+\s/.test(line)) {
                const text = line.replace(/^#+\s/, '');
                return <div key={index} className="message-header">{text}</div>;
            }

            // Handle labeled lines (VERDICT:, REASON:, etc.)
            if (/^[A-Z][A-Z\s]+:/.test(line)) {
                const match = line.match(/^([A-Z][A-Z\s]+):\s*(.*)/);
                if (match) {
                    return (
                        <div key={index} className="labeled-line">
                            <span className="label">{match[1]}:</span>
                            <span>{formatInlineText(match[2])}</span>
                        </div>
                    );
                }
            }

            // Empty lines become spacing
            if (line.trim() === '') {
                return <div key={index} className="line-break" />;
            }

            // Regular paragraph
            return <p key={index}>{formatInlineText(line)}</p>;
        });
    };

    // Format inline text (bold, code, etc.)
    const formatInlineText = (text) => {
        if (!text) return '';

        // Simple inline formatting - bold (**text**) and code (`code`)
        const parts = [];
        let remaining = text;
        let key = 0;

        // Process bold text
        while (remaining.length > 0) {
            const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
            const codeMatch = remaining.match(/`(.*?)`/);

            if (boldMatch && (!codeMatch || remaining.indexOf(boldMatch[0]) < remaining.indexOf(codeMatch[0]))) {
                const idx = remaining.indexOf(boldMatch[0]);
                if (idx > 0) parts.push(remaining.substring(0, idx));
                parts.push(<strong key={key++}>{boldMatch[1]}</strong>);
                remaining = remaining.substring(idx + boldMatch[0].length);
            } else if (codeMatch) {
                const idx = remaining.indexOf(codeMatch[0]);
                if (idx > 0) parts.push(remaining.substring(0, idx));
                parts.push(<code key={key++}>{codeMatch[1]}</code>);
                remaining = remaining.substring(idx + codeMatch[0].length);
            } else {
                parts.push(remaining);
                break;
            }
        }

        return parts.length > 0 ? parts : text;
    };

    return (
        <div className={`chat-message ${isAgent ? 'agent' : 'user'}`}>
            {isAgent && (
                <div
                    className="message-avatar"
                    style={{ background: agentColor || 'var(--color-accent-primary)' }}
                >
                    {message.agent?.[0]?.toUpperCase() || 'A'}
                </div>
            )}
            <div className="message-content">
                {isAgent && (
                    <span className="message-sender">{message.agent}</span>
                )}
                <div className="message-bubble">
                    <div className="message-text">
                        {formatContent(message.content)}
                    </div>
                </div>
                <span className="message-time">{formatTime(message.timestamp)}</span>
            </div>
        </div>
    );
};

export default ChatMessage;
