import React, { useState, useRef } from 'react';
import VoiceRecorder from './components/VoiceRecorder';
import Orb from './components/Orb';

const API_CONVERSE = 'http://localhost:8000/api/converse';

type ConversationState = {
  location: string | null;
  consumption: string | null;
  cost: string | null;
  preferences: string | null;
  step: string;
};

const App: React.FC = () => {
  const [transcription, setTranscription] = useState('');
  const [agentResponse, setAgentResponse] = useState('');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [orbState, setOrbState] = useState<'waiting' | 'talking' | null>(null);
  const [conversationState, setConversationState] = useState<ConversationState | null>(null);
  const [done, setDone] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleVoice = async (audioBlob: Blob) => {
    setTranscription('');
    setAgentResponse('');
    setAudioUrl(null);
    setOrbState('waiting');
    setDone(false);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');
      if (conversationState) {
        formData.append('state', JSON.stringify(conversationState));
      }
      const res = await fetch(API_CONVERSE, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setTranscription(data.transcription);
      setAgentResponse(data.agent_response);
      setAudioUrl(data.audio_url.startsWith('http') ? data.audio_url : `http://localhost:8000${data.audio_url}`);
      setConversationState(data.state);
      setDone(data.done);
      setOrbState('talking');
    } catch (err) {
      setTranscription('Error processing audio.');
      setOrbState(null);
    }
  };

  const handleAudioEnd = () => {
    setOrbState(null);
  };

  return (
    <div className="app-container">
      <header>
        <h1>AI Energy Switcher</h1>
        <p>Switch your energy provider effortlessly with your voice.</p>
      </header>
      <main>
        <VoiceRecorder onAudio={handleVoice} />
        {orbState && <Orb state={orbState} />}
        {transcription && <div style={{marginBottom: '1rem'}}><strong>Transcription:</strong> {transcription}</div>}
        {agentResponse && <div style={{marginBottom: '1rem'}}><strong>Agent:</strong> {agentResponse}</div>}
        {audioUrl && (
          <audio ref={audioRef} src={audioUrl} autoPlay onEnded={handleAudioEnd} />
        )}
        {done && <div style={{marginTop: '2rem', color: 'green'}}><strong>All information collected! Ready to find the best provider.</strong></div>}
      </main>
    </div>
  );
};

export default App; 