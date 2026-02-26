import { useState, useRef, useEffect, useCallback } from 'react';
import ChatMessage from '../components/ChatMessage';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import './ChatPage.css';

const agents = [
    { id: 'jarvis', name: 'Jarvis', role: 'Main Assistant', color: '#6366f1' },
    { id: 'atlas', name: 'Atlas', role: 'RAG Specialist', color: '#10b981' },
    { id: 'emma', name: 'Emma', role: 'Paraplanner', color: '#ec4899' },
    { id: 'colin', name: 'Colin', role: 'Compliance', color: '#f59e0b' }
];

// Determine the WebSocket URL based on the API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

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

    // Voice State
    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const nextPlayTimeRef = useRef(0);
    const [voiceAgentMessageId, setVoiceAgentMessageId] = useState(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Cleanup resources on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (audioContextRef.current) audioContextRef.current.close();
        };
    }, []);

    const playAudioChunk = async (audioData) => {
        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 24000
                });
            }
            if (audioContextRef.current.state === 'suspended') {
                await audioContextRef.current.resume();
            }

            const ctx = audioContextRef.current;
            const floatData = new Float32Array(new Int16Array(audioData).map(v => v / 32768.0));
            const buffer = ctx.createBuffer(1, floatData.length, 24000);
            buffer.getChannelData(0).set(floatData);

            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);

            const currentTime = ctx.currentTime;
            const playTime = Math.max(currentTime, nextPlayTimeRef.current);
            source.start(playTime);
            nextPlayTimeRef.current = playTime + buffer.duration;
        } catch (error) {
            console.error('Error playing audio chunk:', error);
        }
    };

    const handleWebsocketMessage = async (event) => {
        if (event.data instanceof Blob) {
            // It's audio data (tts_chunk)
            const arrayBuffer = await event.data.arrayBuffer();
            playAudioChunk(arrayBuffer);
        } else {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'stt_output') {
                    // Add user message to UI
                    setMessages(prev => [...prev, {
                        id: Date.now(),
                        sender: 'user',
                        content: data.text,
                        timestamp: new Date()
                    }]);
                    setIsTyping(true);
                    const aiMsgId = Date.now() + 1;
                    setVoiceAgentMessageId(aiMsgId);
                    setMessages(prev => [...prev, {
                        id: aiMsgId,
                        sender: 'agent',
                        agent: selectedAgent.id,
                        content: "",
                        timestamp: new Date()
                    }]);
                } else if (data.type === 'agent_chunk') {
                    setIsTyping(false);
                    setMessages(prev => prev.map(msg =>
                        msg.id === voiceAgentMessageId
                            ? { ...msg, content: msg.content + data.text }
                            : msg
                    ));
                } else if (data.type === 'error') {
                    setIsTyping(false);
                    console.error("Voice Pipeline Error:", data.message);
                }
            } catch (e) {
                console.error("WS Parse error", e);
            }
        }
    };

    const handleAudioData = useCallback((blob) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(blob);
        }
    }, []);

    const { isRecording, startRecording, stopRecording } = useAudioRecorder(handleAudioData);

    const toggleRecording = () => {
        if (isRecording) {
            stopRecording();
            // Close websocket to signal end of stream
            if (wsRef.current) {
                // We don't close immediately here because we still want to receive TTS
                // A better approach is usually to send an EOF marker, but OpenAI Whisper endpoint 
                // in our pipeline processes chunks directly. For this demo, we'll wait for the silent
                // accumulation threshold (3 sek) in the backend to trigger Whisper, 
                // or you could add a specific WS message to trigger flush.
            }
        } else {
            // Establish new WebSocket
            const wsUrl = `${WS_BASE}/ws/voice?agent=${selectedAgent.id}`;
            const ws = new WebSocket(wsUrl);
            ws.onmessage = handleWebsocketMessage;
            ws.onclose = () => console.log("Voice WS closed");
            ws.onerror = (err) => console.error("Voice WS error:", err);
            wsRef.current = ws;

            // Reset audio context play time
            nextPlayTimeRef.current = 0;
            if (audioContextRef.current) {
                audioContextRef.current.close();
                audioContextRef.current = null;
            }

            ws.onopen = () => {
                startRecording();
            };
        }
    };


    const handleAgentChange = (e) => {
        const agent = agents.find(a => a.id === e.target.value);
        setSelectedAgent(agent);
        setThreadId(null);

        const greeting = {
            id: Date.now(),
            sender: 'agent',
            agent: agent.id,
            content: `Hi there! I'm ${agent.name}, the ${agent.role}. How can I assist you?`,
            timestamp: new Date()
        };
        setMessages([greeting]);
    };

    const handleSend = async () => {
        if (!inputValue.trim()) return;

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

            if (!response.ok) throw new Error('Chat request failed');

            const data = await response.json();
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
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                sender: 'agent',
                agent: selectedAgent.id,
                content: "I'm sorry, I encountered an error. Please ensure the backend is running.",
                timestamp: new Date()
            }]);
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
                        <button
                            className={`btn ${isRecording ? 'btn-danger recording-pulse' : 'btn-secondary'} voice-button`}
                            onClick={toggleRecording}
                            title={isRecording ? "Stop Recording" : "Start Voice Recording"}
                            style={{
                                padding: 'var(--spacing-md)',
                                minWidth: '48px',
                                border: isRecording ? '2px solid #ef4444' : '1px solid var(--glass-border)'
                            }}
                        >
                            <svg viewBox="0 0 24 24" fill="none" style={{ width: 20, height: 20 }}>
                                {isRecording ? (
                                    <path d="M6 6h12v12H6z" fill="currentColor" />
                                ) : (
                                    <>
                                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <line x1="12" y1="19" x2="12" y2="22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <line x1="8" y1="22" x2="16" y2="22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </>
                                )}
                            </svg>
                        </button>
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
