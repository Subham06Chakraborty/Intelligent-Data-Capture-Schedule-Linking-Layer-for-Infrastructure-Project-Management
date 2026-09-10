import React, { useState, useRef, useEffect } from 'react';
import { aiAPI } from '../api';

const SupervisorChatPage = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am IntelliTrack. What did you work on today at the site?',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceLoading, setIsVoiceLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const projectId = 'OIL-DULIAJAN-01'; // Defaulting to the demo project
  const supervisor = 'Sanjay (Civil Sup)';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMsg = { role: 'user', content: inputValue };
    const newHistory = [...messages, userMsg];
    
    setMessages(newHistory);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await aiAPI.chatMessage(projectId, inputValue, messages, supervisor);
      
      const assistantMsg = {
        role: 'assistant',
        content: response.data.reply,
        activity_log: response.data.activity_log,
        match_result: response.data.match_result,
      };
      
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const file = new File([audioBlob], 'voice_note.webm', { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop()); // Stop microphone access
        
        await handleVoiceFile(file);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Could not access microphone. Please ensure permissions are granted.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleVoiceFile = async (file) => {
    if (!file) return;

    setIsVoiceLoading(true);
    
    try {
      const response = await aiAPI.voiceUpload(projectId, file, messages);
      
      // The voice endpoint returns { transcription, reply, activity_log, match_result }
      const userMsg = { role: 'user', content: `🎤 Voice Note: "${response.data.transcription}"` };
      const assistantMsg = {
        role: 'assistant',
        content: response.data.reply,
        activity_log: response.data.activity_log,
        match_result: response.data.match_result,
      };
      
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
    } catch (error) {
      console.error('Voice upload error:', error);
      alert('Failed to upload voice note.');
    } finally {
      setIsVoiceLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '16px' }}>
        <h1 className="page-title">Supervisor AI Assistant</h1>
        <p className="page-subtitle">Chat in English or Hindi to log daily site progress.</p>
      </div>
      
      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: '70%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: msg.role === 'user' ? 'rgba(0, 240, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                  border: msg.role === 'user' ? '1px solid rgba(0, 240, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.1)',
                  color: 'var(--text-primary)',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                }}
              >
                {msg.content}
              </div>
              
              {/* If there is an extracted activity, show a summary card */}
              {msg.activity_log && (
                <div style={{
                  marginTop: '8px',
                  padding: '16px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(0, 255, 128, 0.1)',
                  border: '1px solid rgba(0, 255, 128, 0.3)',
                  maxWidth: '70%',
                  width: '100%'
                }}>
                  <h4 style={{ margin: '0 0 8px 0', color: '#00ff80' }}>✓ Activity Extracted</h4>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <div><strong>Description:</strong> {msg.activity_log.extracted_activity}</div>
                    <div><strong>Discipline:</strong> <span style={{ textTransform: 'capitalize' }}>{msg.activity_log.discipline}</span></div>
                    {msg.activity_log.actual_start && <div><strong>Start:</strong> {msg.activity_log.actual_start}</div>}
                    {msg.activity_log.actual_end && <div><strong>End:</strong> {msg.activity_log.actual_end}</div>}
                    
                    {msg.match_result && (
                      <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <div><strong>Schedule Match:</strong> {msg.match_result.matched_description || 'Unmatched'}</div>
                        <div style={{ color: msg.match_result.confidence > 0.8 ? '#00ff80' : '#ffaa00' }}>
                          <strong>Confidence:</strong> {(msg.match_result.confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'var(--text-muted)'
              }}>
                IntelliTrack is typing...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ 
          padding: '16px', 
          borderTop: '1px solid rgba(255, 255, 255, 0.1)', 
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
          display: 'flex',
          gap: '12px',
          alignItems: 'center'
        }}>
          <input
            type="text"
            className="input-field"
            placeholder="Type your message here... e.g. 'We finished the cable pulling for line A'"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            style={{ flex: 1, margin: 0 }}
            disabled={isLoading || isVoiceLoading || isRecording}
          />
          
          {isRecording && (
            <div style={{ color: '#ff4081', display: 'flex', alignItems: 'center', gap: '8px', padding: '0 8px' }}>
              <span className="recording-dot" style={{ width: '12px', height: '12px', backgroundColor: '#ff4081', borderRadius: '50%', display: 'inline-block', animation: 'pulse 1.5s infinite' }}></span>
              Recording...
            </div>
          )}
          
          <input 
            type="file" 
            accept="audio/*" 
            ref={fileInputRef} 
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) handleVoiceFile(file);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }} 
            style={{ display: 'none' }} 
          />

          <button 
            className="btn btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading || isVoiceLoading || isRecording}
            title="Upload Audio File"
            style={{ padding: '0 16px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            📎
          </button>
          
          <button 
            className="btn btn-secondary"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading || isVoiceLoading}
            title={isRecording ? "Stop & Send Voice Note" : "Record Voice Note"}
            style={{ 
              padding: '0 16px', 
              height: '48px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              backgroundColor: isRecording ? 'rgba(255, 64, 129, 0.2)' : undefined,
              borderColor: isRecording ? '#ff4081' : undefined,
              color: isRecording ? '#ff4081' : undefined
            }}
          >
            {isVoiceLoading ? '...' : isRecording ? '⏹️' : '🎤'}
          </button>

          <button 
            className="btn btn-primary"
            onClick={handleSend}
            disabled={isLoading || !inputValue.trim() || isVoiceLoading}
            style={{ padding: '0 24px', height: '48px' }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default SupervisorChatPage;
