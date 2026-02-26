import { useState, useRef, useCallback } from 'react';
import AudioRecorder from 'audio-recorder-polyfill';

export const useAudioRecorder = (onAudioData) => {
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const streamRef = useRef(null);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });
            streamRef.current = stream;

            // We use the polyfill to ensure consistent PCM output if needed, or rely on MediaRecorder
            // The polyfill provides WAV/PCM which is easier back at the backend
            window.MediaRecorder = AudioRecorder;
            const mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.addEventListener('dataavailable', e => {
                if (e.data.size > 0 && onAudioData) {
                    onAudioData(e.data);
                }
            });

            mediaRecorder.start(250); // Emit chunks every 250ms
            mediaRecorderRef.current = mediaRecorder;
            setIsRecording(true);
        } catch (err) {
            console.error('Error starting audio recording:', err);
        }
    }, [onAudioData]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current = null;
            setIsRecording(false);
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
    }, [isRecording]);

    return {
        isRecording,
        startRecording,
        stopRecording
    };
};
