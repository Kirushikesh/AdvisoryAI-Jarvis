import { useState, useRef, useEffect } from 'react';
import ChatMessage from '../components/ChatMessage';
import './ChatPage.css';

const agents = [
    { id: 'jarvis', name: 'Jarvis', role: 'Main Assistant', color: '#6366f1' },
    { id: 'atlas', name: 'Atlas', role: 'RAG Specialist', color: '#10b981' },
    { id: 'emma', name: 'Emma', role: 'Paraplanner', color: '#ec4899' },
    { id: 'colin', name: 'Colin', role: 'Compliance', color: '#f59e0b' }
];

const API_BASE = 'http://localhost:8000';

const ChatPage = () => {
    const [selectedAgent, setSelectedAgent] = useState(agents[0]);
    const [messages, setMessages] = useState([
        {
            id: 1,
            sender: 'agent',
            agent: 'jarvis',
            content: "Hello! I'm Jarvis, your financial advisor assistant. How can I help you today?",
            timestamp: new Date()
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [threadId, setThreadId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleAgentChange = (e) => {
        const agent = agents.find(a => a.id === e.target.value);
        setSelectedAgent(agent);
        // Reset thread when switching agents
        setThreadId(null);

        // Clear chat history and add greeting from new agent
        const greeting = {
            id: Date.now(),
            sender: 'agent',
            agent: agent.id,
            content: `Hi there! I'm ${agent.name}, the ${agent.role}. How can I assist you?`,
            timestamp: new Date()
        };
        setMessages([greeting]); // Replace all messages with just the greeting
    };

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        // Add user message
        const userMessage = {
            id: Date.now(),
            sender: 'user',
            content: inputValue,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        const messageText = inputValue;
        setInputValue('');
        setIsTyping(true);

        try {
            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    agent: selectedAgent.id,
                    thread_id: threadId
                })
            });

            if (!response.ok) {
                throw new Error('Chat request failed');
            }

            const data = await response.json();

            // Save thread ID for conversation continuity
            setThreadId(data.thread_id);

            const agentMessage = {
                id: Date.now() + 1,
                sender: 'agent',
                agent: selectedAgent.id,
                content: data.response,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, agentMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage = {
                id: Date.now() + 1,
                sender: 'agent',
                agent: selectedAgent.id,
                content: "I'm sorry, I encountered an error processing your request. Please make sure the backend server is running.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-page animate-fade-in">
            <div className="chat-header glass-card">
                <div className="chat-header-info">
                    <h2>Chat with Agent</h2>
                    <p className="text-muted">Select an agent and start a conversation</p>
                </div>
                <div className="agent-selector">
                    <label htmlFor="agent-select">Agent:</label>
                    <select
                        id="agent-select"
                        className="select"
                        value={selectedAgent.id}
                        onChange={handleAgentChange}
                    >
                        {agents.map(agent => (
                            <option key={agent.id} value={agent.id}>
                                {agent.name} - {agent.role}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="chat-container glass-card">
                <div className="messages-container">
                    {messages.map(message => (
                        <ChatMessage
                            key={message.id}
                            message={message}
                            agentColor={agents.find(a => a.id === message.agent)?.color}
                        />
                    ))}
                    {isTyping && (
                        <div className="typing-indicator">
                            <div
                                className="typing-avatar"
                                style={{ background: selectedAgent.color }}
                            >
                                {selectedAgent.name[0]}
                            </div>
                            <div className="typing-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-container">
                    <div className="chat-input-wrapper">
                        <input
                            type="text"
                            className="input chat-input"
                            placeholder={`Message ${selectedAgent.name}...`}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                        />
                        <button
                            className="btn btn-primary send-button"
                            onClick={handleSend}
                            disabled={!inputValue.trim() || isTyping}
                        >
                            <svg viewBox="0 0 24 24" fill="none">
                                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M22 2l-7 20-4-9-9-4 20-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatPage;
