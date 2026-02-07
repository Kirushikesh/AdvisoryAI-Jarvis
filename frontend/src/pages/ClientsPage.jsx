import { useState, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import './ClientsPage.css';

const API_BASE = 'http://localhost:8000';

const ClientsPage = () => {
    const [clients, setClients] = useState([]);
    const [selectedClient, setSelectedClient] = useState('');
    const [uploadType, setUploadType] = useState('transcript');
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    // Fetch clients from API
    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/clients`);
            if (response.ok) {
                const data = await response.json();
                setClients(data);
            }
        } catch (error) {
            console.error('Failed to fetch clients:', error);
            // Fallback to hardcoded list if API is not available
            setClients([
                { name: 'Alan Partridge', folder: 'alan_partridge', file_count: 0 },
                { name: 'Brian Potter', folder: 'brian_potter', file_count: 0 },
                { name: 'David Chen', folder: 'david_chen', file_count: 0 },
                { name: 'Emma Thompson', folder: 'emma_thompson', file_count: 0 },
                { name: 'Lisa Rahman', folder: 'lisa_rahman', file_count: 0 },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = async (files) => {
        const file = files[0];
        if (!file) return;

        // Validate .md extension
        if (!file.name.endsWith('.md')) {
            setUploadStatus({ type: 'error', message: 'Only .md files are allowed' });
            setTimeout(() => setUploadStatus(null), 3000);
            return;
        }

        const newFile = {
            id: Date.now(),
            name: file.name,
            size: file.size,
            type: uploadType,
            client: selectedClient,
            status: 'uploading',
            progress: 0
        };

        setUploadedFiles(prev => [...prev, newFile]);

        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('client', selectedClient);
        formData.append('upload_type', uploadType);

        try {
            // Start progress animation
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                if (progress < 90) {
                    setUploadedFiles(prev =>
                        prev.map(f => f.id === newFile.id ? { ...f, progress } : f)
                    );
                }
            }, 100);

            const response = await fetch(`${API_BASE}/api/upload`, {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);

            if (response.ok) {
                const data = await response.json();
                setUploadedFiles(prev =>
                    prev.map(f => f.id === newFile.id ? { ...f, status: 'complete', progress: 100 } : f)
                );
                setUploadStatus({ type: 'success', message: data.message });
                // Refresh client list to update file counts
                fetchClients();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setUploadedFiles(prev =>
                prev.map(f => f.id === newFile.id ? { ...f, status: 'error', progress: 0 } : f)
            );
            setUploadStatus({ type: 'error', message: 'Upload failed. Make sure the backend is running.' });
        }

        setTimeout(() => setUploadStatus(null), 4000);
    };

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const removeFile = (id) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== id));
    };

    return (
        <div className="clients-page animate-fade-in">
            <div className="page-header">
                <h1 className="page-title">Client Files</h1>
                <p className="page-subtitle">Upload markdown files to your clients' workspace folders</p>
            </div>

            <div className="clients-content">
                <div className="upload-section glass-card">
                    <h3>Upload Documents</h3>

                    <div className="upload-form">
                        <div className="form-group">
                            <label htmlFor="client-select">Select Client</label>
                            <select
                                id="client-select"
                                className="select"
                                value={selectedClient}
                                onChange={(e) => setSelectedClient(e.target.value)}
                                disabled={loading}
                            >
                                <option value="">Choose a client...</option>
                                {clients.map(client => (
                                    <option key={client.folder} value={client.name}>
                                        {client.name} ({client.file_count} files)
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Document Type</label>
                            <div className="type-selector">
                                <button
                                    className={`type-btn ${uploadType === 'transcript' ? 'active' : ''}`}
                                    onClick={() => setUploadType('transcript')}
                                >
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2z" stroke="currentColor" strokeWidth="2" />
                                        <path d="M8 7h8M8 11h8M8 15h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    </svg>
                                    Meeting Transcript
                                </button>
                                <button
                                    className={`type-btn ${uploadType === 'email' ? 'active' : ''}`}
                                    onClick={() => setUploadType('email')}
                                >
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="2" />
                                        <path d="M22 6l-10 7L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    </svg>
                                    Email Archive
                                </button>
                            </div>
                        </div>

                        <FileUpload
                            onFileSelect={handleFileSelect}
                            disabled={!selectedClient}
                        />

                        {uploadStatus && (
                            <div className={`upload-status ${uploadStatus.type}`}>
                                {uploadStatus.type === 'success' ? (
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke="currentColor" strokeWidth="2" />
                                        <path d="M22 4L12 14.01l-3-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                ) : (
                                    <svg viewBox="0 0 24 24" fill="none">
                                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                                        <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    </svg>
                                )}
                                {uploadStatus.message}
                            </div>
                        )}
                    </div>
                </div>

                <div className="files-section glass-card">
                    <h3>Uploaded Files</h3>

                    {uploadedFiles.length === 0 ? (
                        <div className="empty-state">
                            <svg viewBox="0 0 24 24" fill="none">
                                <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z" stroke="currentColor" strokeWidth="2" />
                                <path d="M13 2v7h7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                            <p>No files uploaded yet</p>
                            <span>Select a client and upload documents to get started</span>
                        </div>
                    ) : (
                        <div className="files-list">
                            {uploadedFiles.map(file => (
                                <div key={file.id} className={`file-item ${file.status === 'error' ? 'error' : ''}`}>
                                    <div className="file-icon">
                                        {file.type === 'transcript' ? (
                                            <svg viewBox="0 0 24 24" fill="none">
                                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" strokeWidth="2" />
                                                <path d="M14 2v6h6M8 13h8M8 17h8M8 9h2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                            </svg>
                                        ) : (
                                            <svg viewBox="0 0 24 24" fill="none">
                                                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" strokeWidth="2" />
                                                <path d="M22 6l-10 7L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                            </svg>
                                        )}
                                    </div>
                                    <div className="file-info">
                                        <span className="file-name">{file.name}</span>
                                        <div className="file-meta">
                                            <span>{file.client}</span>
                                            <span>•</span>
                                            <span>{file.type === 'transcript' ? 'Transcript' : 'Email'}</span>
                                            <span>•</span>
                                            <span>{formatFileSize(file.size)}</span>
                                        </div>
                                        {file.status === 'uploading' && (
                                            <div className="progress-bar">
                                                <div
                                                    className="progress-fill"
                                                    style={{ width: `${file.progress}%` }}
                                                ></div>
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        className="remove-btn"
                                        onClick={() => removeFile(file.id)}
                                    >
                                        <svg viewBox="0 0 24 24" fill="none">
                                            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                        </svg>
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ClientsPage;
