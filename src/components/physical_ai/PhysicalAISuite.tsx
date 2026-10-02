/**
 * @file PhysicalAISuite.tsx
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
import React, { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { DigitalTwin3D } from '../digital_twin/DigitalTwin3D';
import { TrilingualVoiceAssistant } from '../voice/TrilingualVoiceAssistant';

interface PhysicalAIData {
  traversability: {
    physical_ai_status: string;
    traction_state: string;
    traction_coefficient: number;
    terrain_tilt_deg: number;
    stability_rating: string;
    collision_risk: string;
    safe_to_advance: boolean;
    recommended_max_pwm: number;
  };
  spray_drift_physics: {
    wind_speed_ms: number;
    lateral_drift_offset_cm: number;
    longitudinal_drift_offset_cm: number;
    safe_to_spray: boolean;
    spray_drift_risk: string;
  };
}

interface VLAActionResult {
  action_type: string;
  confidence: number;
  reasoning_chain: string[];
  actuator_commands: any;
  target_coordinates: { latitude: number; longitude: number };
  status: string;
}

interface PhysicalAISuiteProps {
  darkMode?: boolean;
  robotPose?: { x: number; y: number; heading: number; pitch?: number; roll?: number };
  actuators?: { pump_on?: boolean; sol1_on?: boolean; sol2_on?: boolean; speed?: number };
  obstacles?: { clearance_left?: number; clearance_center?: number; clearance_right?: number; risk?: string };
  onCommandDispatched?: (intent: string, action: any) => void;
}

export const PhysicalAISuite: React.FC<PhysicalAISuiteProps> = ({
  darkMode = true,
  robotPose,
  actuators,
  obstacles,
  onCommandDispatched
}) => {
  const { t, language } = useLanguage();
  const [prompt, setPrompt] = useState('');
  const [loadingVLA, setLoadingVLA] = useState(false);
  const [vlaResult, setVlaResult] = useState<VLAActionResult | null>(null);
  const [physicalData, setPhysicalData] = useState<PhysicalAIData | null>(null);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | '3D_SIM' | 'VOICE'>('OVERVIEW');

  // Poll physical AI physics data every 4s
  useEffect(() => {
    const fetchPhysicalAI = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/physical_ai/evaluate`);
        if (res.ok) {
          const data = await res.json();
          setPhysicalData(data);
        }
      } catch (err) {
        console.error('Failed to fetch Physical AI data', err);
      }
    };
    fetchPhysicalAI();
    const interval = setInterval(fetchPhysicalAI, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleExecuteVLA = async (customPrompt?: string) => {
    const activePrompt = customPrompt || prompt;
    if (!activePrompt.trim()) return;

    setLoadingVLA(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/vla/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: activePrompt })
      });
      if (res.ok) {
        const data = await res.json();
        setVlaResult(data);
      }
    } catch (err) {
      console.error('VLA execution error', err);
    } finally {
      setLoadingVLA(false);
    }
  };

  const trav = physicalData?.traversability;
  const drift = physicalData?.spray_drift_physics;

  const cardBg = darkMode ? 'rgba(30, 20, 38, 0.85)' : 'rgba(255, 255, 255, 0.95)';
  const borderColor = darkMode ? 'rgba(224, 64, 160, 0.25)' : 'rgba(220, 200, 224, 0.6)';
  const textColor = darkMode ? '#ffffff' : '#2e1a28';
  const subTextColor = darkMode ? '#a088a5' : '#705878';

  return (
    <div style={{
      background: cardBg,
      border: `1px solid ${borderColor}`,
      borderRadius: 16,
      padding: '20px',
      marginTop: '16px',
      marginBottom: '16px',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.25)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: `1px solid ${borderColor}`, paddingBottom: 12, marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="material-symbols-outlined" style={{ color: '#e040a0', fontSize: '1.6rem' }}>smart_toy</span>
          <div>
            <div style={{ fontWeight: '900', fontSize: '1.05rem', color: textColor, letterSpacing: '0.5px' }}>
              PHYSICAL AI, 3D DIGITAL TWIN & AI VOICE SUITE
            </div>
            <div style={{ fontSize: '0.72rem', color: subTextColor }}>
              Google Antigravity Robotics • Three.js WebGL Sim2Real • Offline Neural Intent Recognition
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: 'flex', background: darkMode ? '#1d1222' : '#f0e6f2', padding: 4, borderRadius: 10, gap: 4 }}>
          <button
            onClick={() => setActiveTab('OVERVIEW')}
            style={{
              background: activeTab === 'OVERVIEW' ? 'linear-gradient(135deg, #e040a0, #7928ca)' : 'transparent',
              color: activeTab === 'OVERVIEW' ? '#ffffff' : subTextColor,
              border: 'none',
              borderRadius: 8,
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: '800',
              cursor: 'pointer'
            }}
          >
            📊 OVERVIEW
          </button>
          <button
            onClick={() => setActiveTab('3D_SIM')}
            style={{
              background: activeTab === '3D_SIM' ? 'linear-gradient(135deg, #00f0ff, #7928ca)' : 'transparent',
              color: activeTab === '3D_SIM' ? '#ffffff' : subTextColor,
              border: 'none',
              borderRadius: 8,
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: '800',
              cursor: 'pointer'
            }}
          >
            🌐 3D DIGITAL TWIN
          </button>
          <button
            onClick={() => setActiveTab('VOICE')}
            style={{
              background: activeTab === 'VOICE' ? 'linear-gradient(135deg, #e040a0, #7928ca)' : 'transparent',
              color: activeTab === 'VOICE' ? '#ffffff' : subTextColor,
              border: 'none',
              borderRadius: 8,
              padding: '6px 12px',
              fontSize: '0.75rem',
              fontWeight: '800',
              cursor: 'pointer'
            }}
          >
            🎙️ VOICE ASSISTANT
          </button>
        </div>
      </div>

      {/* TAB 1: OVERVIEW (VLA Natural Language + Physical Gauges) */}
      {activeTab === 'OVERVIEW' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
            {/* Left: VLA Natural Language Commander */}
            <div style={{ background: darkMode ? '#180f20' : '#f7f2f8', padding: 16, borderRadius: 12, border: `1px solid ${borderColor}` }}>
              <div style={{ fontWeight: '800', fontSize: '0.85rem', color: '#e040a0', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>mic</span>
                Natural Language VLA Commander (Vision-to-Action)
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g. 'Inspect row 3 and apply spot spray on early blight'"
                  onKeyDown={(e) => e.key === 'Enter' && handleExecuteVLA()}
                  style={{
                    flex: 1,
                    padding: '10px 14px',
                    borderRadius: 8,
                    border: `1px solid ${borderColor}`,
                    background: darkMode ? '#261730' : '#fff',
                    color: textColor,
                    fontSize: '0.82rem',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={() => handleExecuteVLA()}
                  disabled={loadingVLA}
                  style={{
                    background: 'linear-gradient(135deg, #e040a0, #7928ca)',
                    border: 'none',
                    borderRadius: 8,
                    padding: '0 18px',
                    color: '#fff',
                    fontWeight: '800',
                    fontSize: '0.80rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}
                >
                  {loadingVLA ? 'INFERRING...' : 'DISPATCH'}
                </button>
              </div>

              {/* Quick Prompt Chips */}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
                {[
                  '🎯 Spot spray severe blight (5s)',
                  '🔍 Inspect row 3 and scan canopy',
                  '🌱 Soil moisture probe check',
                  '🛑 Emergency halt all motors'
                ].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => { setPrompt(chip); handleExecuteVLA(chip); }}
                    style={{
                      background: darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)',
                      border: `1px solid ${darkMode ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'}`,
                      color: textColor,
                      borderRadius: 6,
                      padding: '4px 8px',
                      fontSize: '0.68rem',
                      cursor: 'pointer'
                    }}
                  >
                    {chip}
                  </button>
                ))}
              </div>

              {/* Live Action Vector Decoded */}
              {vlaResult && (
                <div style={{ background: darkMode ? 'rgba(224,64,160,0.1)' : 'rgba(224,64,160,0.05)', border: '1px solid #e040a0', borderRadius: 8, padding: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontWeight: '900', color: '#e040a0', fontSize: '0.78rem' }}>ACTION TOKEN: {vlaResult.action_type}</span>
                    <span style={{ fontSize: '0.70rem', color: '#4ade80', fontWeight: '800' }}>CONFIDENCE: {(vlaResult.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div style={{ fontSize: '0.70rem', color: subTextColor, marginBottom: 8 }}>
                    {vlaResult.reasoning_chain.map((step, idx) => (
                      <div key={idx} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <span style={{ color: '#e040a0' }}>•</span> {step}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#a78bfa', background: darkMode ? '#120818' : '#eee', padding: '6px 8px', borderRadius: 4 }}>
                    {JSON.stringify(vlaResult.actuator_commands)}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Physical AI Embodied Gauges */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {/* Mud Slippage & Traction */}
              <div style={{ background: darkMode ? '#180f20' : '#f7f2f8', padding: 12, borderRadius: 10, border: `1px solid ${borderColor}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: '800', color: textColor }}>🚜 Mud Traction & Traversability</span>
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: '900',
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: trav?.traction_coefficient && trav.traction_coefficient > 0.6 ? '#16a34a' : '#d97706',
                    color: '#fff'
                  }}>
                    {trav?.traction_state || 'OPTIMAL_TRACTION'}
                  </span>
                </div>
                <div style={{ fontSize: '0.68rem', color: subTextColor }}>
                  Traction Coeff: <b>{trav?.traction_coefficient ?? 0.85}</b> | Max Safe PWM: <b>{trav?.recommended_max_pwm ?? 220}</b>
                </div>
              </div>

              {/* Terrain Slope & Anti-Tip Stability */}
              <div style={{ background: darkMode ? '#180f20' : '#f7f2f8', padding: 12, borderRadius: 10, border: `1px solid ${borderColor}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: '800', color: textColor }}>📐 3-Axis IMU Slope Stability</span>
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: '900',
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: trav?.stability_rating === 'STABLE_FLAT' ? '#16a34a' : '#2563eb',
                    color: '#fff'
                  }}>
                    {trav?.stability_rating || 'STABLE_FLAT'}
                  </span>
                </div>
                <div style={{ fontSize: '0.68rem', color: subTextColor }}>
                  Tilt Pitch/Roll: <b>{trav?.terrain_tilt_deg ?? 2.5}°</b> | Collision Risk: <b>{trav?.collision_risk || 'CLEAR_PATH'}</b>
                </div>
              </div>

              {/* Aerodynamic Spray Drift Physics */}
              <div style={{ background: darkMode ? '#180f20' : '#f7f2f8', padding: 12, borderRadius: 10, border: `1px solid ${borderColor}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: '800', color: textColor }}>💨 Spray Drift Physics Compensation</span>
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: '900',
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: drift?.safe_to_spray ? '#16a34a' : '#e53e3e',
                    color: '#fff'
                  }}>
                    {drift?.spray_drift_risk || 'SAFE_LOW_DRIFT'}
                  </span>
                </div>
                <div style={{ fontSize: '0.68rem', color: subTextColor }}>
                  Wind: <b>{drift?.wind_speed_ms ?? 3.3} m/s</b> | Lateral Drift: <b>{drift?.lateral_drift_offset_cm ?? 0.0} cm</b>
                </div>
              </div>
            </div>
          </div>

          {/* Quick inline preview of 3D Digital Twin & Voice */}
          <DigitalTwin3D
            darkMode={darkMode}
            robotPose={robotPose}
            actuators={actuators}
            obstacles={obstacles}
          />
          <TrilingualVoiceAssistant
            darkMode={darkMode}
            onCommandDispatched={onCommandDispatched}
          />
        </>
      )}

      {/* TAB 2: FULL 3D DIGITAL TWIN */}
      {activeTab === '3D_SIM' && (
        <DigitalTwin3D
          darkMode={darkMode}
          robotPose={robotPose}
          actuators={actuators}
          obstacles={obstacles}
        />
      )}

      {/* TAB 3: AI VOICE ASSISTANT */}
      {activeTab === 'VOICE' && (
        <TrilingualVoiceAssistant
          darkMode={darkMode}
          onCommandDispatched={onCommandDispatched}
        />
      )}
    </div>
  );
};
