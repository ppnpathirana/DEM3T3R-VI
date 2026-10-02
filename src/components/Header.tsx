import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Language } from '../i18n/translations';

type HeaderProps = {
  connected: boolean;
  modelStatus: string;
};

export default function Header({ connected, modelStatus }: HeaderProps) {
  const { language, setLanguage, t, voiceEnabled, setVoiceEnabled } = useLanguage();

  return (
    <header className="header-bar">
      <div style={{ 
        padding: '12px 20px', 
        maxWidth: '1600px', 
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.5rem' }}>🌱</span>
          <h1 className="gradient-text" style={{ fontSize: '1.3rem', fontWeight: '700' }}>
            {t('appTitle')}
          </h1>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Language Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(224,64,160,0.08)', padding: '4px 10px', borderRadius: 8, border: '1px solid rgba(224,64,160,0.2)', fontSize: '0.8rem', fontWeight: '750' }}>
            <span style={{ fontSize: '0.9rem' }}>🌐</span>
            <span>🇬🇧 English (Global)</span>
          </div>

          {/* Voice Toggle */}
          <button
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            title={voiceEnabled ? t('speakingVoiceOn') : t('speakingVoiceOff')}
            style={{
              background: voiceEnabled ? 'rgba(224,64,160,0.15)' : 'rgba(100,100,100,0.1)',
              border: '1px solid rgba(224,64,160,0.3)',
              borderRadius: 8,
              padding: '6px 10px',
              fontSize: '0.75rem',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}
          >
            {voiceEnabled ? '🔊 Voice' : '🔇 Mute'}
          </button>

          <span className={`status-badge ${connected ? 'status-connected' : 'status-disconnected'}`}>
            <span className="status-dot" />
            {connected ? t('connected') : t('disconnected')}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Model: {modelStatus}
          </span>
        </div>
      </div>
    </header>
  );
}
