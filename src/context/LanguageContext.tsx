import React, { createContext, useContext, useState, useEffect } from 'react';
import { Language, translations, spokenMessages, Translations } from '../i18n/translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: keyof Translations) => string;
  speak: (msgKeyOrText: string, fallbackText?: string) => void;
  voiceEnabled: boolean;
  setVoiceEnabled: (enabled: boolean) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('cropguard_language') as Language;
    return (saved && ['en', 'si', 'ta'].includes(saved)) ? saved : 'en';
  });

  const [voiceEnabled, setVoiceEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem('cropguard_voice');
    return saved !== null ? saved === 'true' : true;
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('cropguard_language', lang);
  };

  const setVoice = (enabled: boolean) => {
    setVoiceEnabled(enabled);
    localStorage.setItem('cropguard_voice', String(enabled));
  };

  const t = (key: keyof Translations): string => {
    const dict = translations[language] || translations.en;
    return dict[key] || translations.en[key] || String(key);
  };

  const speak = (msgKeyOrText: string, fallbackText?: string) => {
    if (!voiceEnabled || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    
    // Defer asynchronously to prevent blocking the UI main thread on click
    setTimeout(() => {
      try {
        window.speechSynthesis.cancel();
        
        // Determine actual text to speak
        let textToSpeak = spokenMessages[language]?.[msgKeyOrText] || fallbackText || msgKeyOrText;
        
        const utterance = new SpeechSynthesisUtterance(textToSpeak);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        // Select locale code matching language
        if (language === 'si') {
          utterance.lang = 'si-LK';
        } else if (language === 'ta') {
          utterance.lang = 'ta-LK';
        } else {
          utterance.lang = 'en-US';
        }

        // Try to assign matching browser voice if available
        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = voices.find(v => v.lang.startsWith(language === 'si' ? 'si' : language === 'ta' ? 'ta' : 'en'));
        if (matchedVoice) {
          utterance.voice = matchedVoice;
        }

        utterance.onerror = () => {
          // Gracefully ignore speech synthesis errors
        };

        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.warn('[SpeechSynth] Non-critical speech synth error:', e);
      }
    }, 0);
  };

  useEffect(() => {
    // Warm up voices on mount
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
    }
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, speak, voiceEnabled, setVoiceEnabled: setVoice }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
