import React, { useState, useRef } from 'react';

interface VoiceRecorderProps {
  onAudio: (audioBlob: Blob) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onAudio }) => {
  const [recording, setRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const handleStart = async () => {
    setError(null);
    setRecording(true);
    audioChunks.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new window.MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        setAudioUrl(URL.createObjectURL(audioBlob));
        setLoading(true);
        try {
          onAudio(audioBlob);
        } catch (err) {
          setError('Failed to process audio.');
        } finally {
          setLoading(false);
        }
      };
      mediaRecorder.start();
    } catch (err) {
      setError('Microphone access denied.');
      setRecording(false);
    }
  };

  const handleStop = () => {
    setRecording(false);
    mediaRecorderRef.current?.stop();
  };

  return (
    <div className="voice-recorder">
      <button
        className={`mic-btn${recording ? ' recording' : ''}`}
        onMouseDown={handleStart}
        onMouseUp={handleStop}
        onTouchStart={handleStart}
        onTouchEnd={handleStop}
        aria-label={recording ? 'Stop recording' : 'Start recording'}
        disabled={loading}
      >
        <span className="mic-icon">🎤</span>
      </button>
      <div className="waveform">
        {loading ? 'Processing...' : recording ? 'Listening...' : 'Press and hold to talk'}
      </div>
      {audioUrl && (
        <audio controls src={audioUrl} />
      )}
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  );
};

export default VoiceRecorder; 