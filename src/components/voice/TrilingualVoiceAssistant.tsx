/**
 * @file TrilingualVoiceAssistant.tsx
 * @description Core component for DEM3T3R V1 architecture.
 * 
 * @project DEM3T3R V1
 * @author Pasindu Pathirana
 * @contact https://github.com/ppnpathirana/DEM3T3R-VI
 * @version 1.0.0
 * @date 2026
 * 
 * All rights reserved.
 */

import { BACKEND_URL } from '../../backendUrl';
import React, { useState, useEffect, useRef } from 'react';

interface VoiceActionResponse {
  query: string;
  intent: string;
  confidence: number;
  language: string;
  executed: boolean;
  action: any;
  response_text: string;
  timestamp: number;
}

interface TrilingualVoiceAssistantProps {
  darkMode?: boolean;
  onCommandDispatched?: (intent: string, action: any) => void;
}

type SupportedLang = 'en';

const LANG_CONFIG: Record<SupportedLang, { name: string; flag: string; speechLocale: string; placeholder: string; chips: string[] }> = {
  en: {
    name: 'English',
    flag: '🇬🇧',
    speechLocale: 'en-US',
    placeholder: 'Speak command (e.g. "Move forward", "Emergency stop", "Precision spray")...',
    chips: [
      'Move forward',
      'Emergency stop',
      'Precision spray',
      'Check soil probe',
      'Robot status',
      'Auto mode',
      'Turn left',
      'Turn right',
      'Reverse',
      'Manual mode'
    ]
  }
};

export const TrilingualVoiceAssistant: React.FC<TrilingualVoiceAssistantProps> = ({
  darkMode = true,
  onCommandDispatched
}) => {
  const [activeLang, setActiveLang] = useState<SupportedLang>('en');
  const [isListening, setIsListening] = useState(false);
  const [inputText, setInputText] = useState('');
  const [lastResult, setLastResult] = useState<VoiceActionResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check Speech Recognition support in browser
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = LANG_CONFIG[activeLang].speechLocale;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          setInputText(transcript);
          handleExecuteVoice(transcript, activeLang);
        }
      };

      recognition.onerror = (err: any) => {
        console.warn('Speech Recognition Error:', err);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } else {
      setSpeechSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (_) {}
      }
    };
  }, [activeLang]);

  const speakResponse = (text: string, lang: SupportedLang) => {
    if (!('speechSynthesis' in window) || !text) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = LANG_CONFIG[lang].speechLocale;
      utterance.rate = 0.95;
      utterance.pitch = 1.0;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('TTS vocalization error:', e);
    }
  };

  const toggleListening = () => {
    if (!speechSupported) {
      alert('Speech recognition is not supported in this browser. You can type commands below.');
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch (_) {}
      setIsListening(false);
    } else {
      try {
        if (recognitionRef.current) {
          recognitionRef.current.lang = LANG_CONFIG[activeLang].speechLocale;
          recognitionRef.current.start();
        }
      } catch (err) {
        console.error('Failed to start speech recognition', err);
      }
    }
  };

  const handleExecuteVoice = async (textToExecute?: string, langOverride?: SupportedLang) => {
    const query = textToExecute || inputText;
    if (!query.trim()) return;

    const lang = langOverride || activeLang;
    setIsProcessing(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/voice/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query, language: lang })
      });

      if (res.ok) {
        const data: VoiceActionResponse = await res.json();
        setLastResult(data);
        if (onCommandDispatched && data.executed) {
          onCommandDispatched(data.intent, data.action);
        }
        if (data.response_text) {
          speakResponse(data.response_text, lang);
        }
      }
    } catch (err) {
      console.error('Voice command execution failed:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const cardBg = darkMode ? '#180f20' : '#ffffff';
  const borderColor = darkMode ? 'rgba(224, 64, 160, 0.3)' : 'rgba(220, 200, 224, 0.7)';
  const textColor = darkMode ? '#ffffff' : '#2e1a28';
  const subTextColor = darkMode ? '#a088a5' : '#705878';

  return (
    <div style={{
      background: cardBg,
      border: `1px solid ${borderColor}`,
      borderRadius: 14,
      padding: '16px',
      marginTop: '14px',
      boxShadow: '0 8px 24px rgba(0,0,0,0.18)'
    }}>
      {/* Top Header: Title & Language Tabs */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #e040a0, #7928ca)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>record_voice_over</span>
          </div>
          <div>
            <div style={{ fontWeight: '900', fontSize: '0.92rem', color: textColor }}>
              TRILINGUAL EDGE VOICE ASSISTANT
            </div>
            <div style={{ fontSize: '0.68rem', color: subTextColor }}>
              Natural Speech Recognition • Offline TTS Vocalization • Zero-Latency Actuation
            </div>
          </div>
        </div>

        {/* Active Language Badge */}
        <div style={{ display: 'flex', background: darkMode ? '#261730' : '#f0e6f2', padding: '4px 10px', borderRadius: 8, gap: 6, alignItems: 'center', fontSize: '0.74rem', fontWeight: '800', color: textColor }}>
          <span>🇬🇧</span>
          <span>English (Global)</span>
        </div>
      </div>

      {/* Voice Input Controls */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12 }}>
        {/* Pulsing Mic Button */}
        <button
          onClick={toggleListening}
          title={isListening ? 'Click to stop listening' : 'Click to speak command'}
          style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: isListening
              ? 'linear-gradient(135deg, #ef4444, #dc2626)'
              : 'linear-gradient(135deg, #e040a0, #7928ca)',
            border: isListening ? '3px solid #fecaca' : 'none',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: isListening ? '0 0 16px rgba(239, 68, 68, 0.7)' : '0 4px 12px rgba(224, 64, 160, 0.4)',
            transition: 'all 0.2s ease',
            flexShrink: 0
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '1.4rem' }}>
            {isListening ? 'mic_off' : 'mic'}
          </span>
        </button>

        {/* Text Input Fallback */}
        <div style={{ flex: 1, position: 'relative' }}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecuteVoice()}
            placeholder={LANG_CONFIG[activeLang].placeholder}
            style={{
              width: '100%',
              padding: '10px 42px 10px 14px',
              borderRadius: 8,
              border: `1px solid ${borderColor}`,
              background: darkMode ? '#261730' : '#ffffff',
              color: textColor,
              fontSize: '0.82rem',
              outline: 'none'
            }}
          />
          <button
            onClick={() => handleExecuteVoice()}
            disabled={isProcessing}
            style={{
              position: 'absolute',
              right: 6,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'transparent',
              border: 'none',
              color: '#e040a0',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>
              send
            </span>
          </button>
        </div>
      </div>

      {/* Audio Waveform Animation when Listening */}
      {isListening && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 4,
          padding: '8px',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: 8,
          marginBottom: 10
        }}>
          <span style={{ fontSize: '0.72rem', color: '#ef4444', fontWeight: '800', marginRight: 8 }}>
            🎙️ LISTENING ({LANG_CONFIG[activeLang].name})...
          </span>
          {[14, 24, 32, 18, 28, 12, 30, 20].map((h, i) => (
            <div
              key={i}
              style={{
                width: 3,
                height: `${h}px`,
                background: '#ef4444',
                borderRadius: 2,
                animation: `pulse 0.6s infinite alternate ${i * 0.1}s`
              }}
            />
          ))}
        </div>
      )}

      {/* Quick Action Chips */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
        {LANG_CONFIG[activeLang].chips.map((chip) => (
          <button
            key={chip}
            onClick={() => {
              setInputText(chip);
              handleExecuteVoice(chip, activeLang);
            }}
            style={{
              background: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
              border: `1px solid ${darkMode ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.08)'}`,
              color: textColor,
              borderRadius: 6,
              padding: '3px 8px',
              fontSize: '0.68rem',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Voice Execution Result & TTS Playback */}
      {lastResult && (
        <div style={{
          background: lastResult.executed ? (darkMode ? 'rgba(22, 163, 74, 0.12)' : 'rgba(22, 163, 74, 0.08)') : (darkMode ? 'rgba(239, 68, 68, 0.12)' : 'rgba(239, 68, 68, 0.08)'),
          border: `1px solid ${lastResult.executed ? '#16a34a' : '#ef4444'}`,
          borderRadius: 8,
          padding: '10px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: 4
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: '900', color: lastResult.executed ? '#4ade80' : '#f87171', fontSize: '0.76rem' }}>
              INTENT: {lastResult.intent} ({(lastResult.confidence * 100).toFixed(0)}%)
            </span>
            <button
              onClick={() => speakResponse(lastResult.response_text, activeLang)}
              title="Repeat Vocal Feedback"
              style={{
                background: 'transparent',
                border: 'none',
                color: isSpeaking ? '#e040a0' : subTextColor,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: '0.68rem'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1.05rem' }}>volume_up</span>
              {isSpeaking ? 'SPEAKING...' : 'PLAY'}
            </button>
          </div>
          <div style={{ fontSize: '0.74rem', color: textColor, fontWeight: '600' }}>
            🗣️ {lastResult.response_text}
          </div>
          {lastResult.action && Object.keys(lastResult.action).length > 0 && (
            <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#a78bfa', marginTop: 2 }}>
              ACTION: {JSON.stringify(lastResult.action)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
