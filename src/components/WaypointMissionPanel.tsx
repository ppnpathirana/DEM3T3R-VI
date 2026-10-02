import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';

export interface MissionWaypoint {
  id: string;
  idx: number;
  lat: number;
  lng: number;
  status: 'pending' | 'navigating' | 'inspecting' | 'completed';
  stagingRemaining?: number;
  inspectionReport?: {
    soilMoisture1: number;
    soilMoisture2: number;
    temperature: number;
    humidity: number;
    uvVoltage: number;
    light: number;
    diseases: string[];
    timestamp: string;
  };
}

interface WaypointMissionPanelProps {
  waypoints: MissionWaypoint[];
  activeWpIndex: number | null;
  missionActive: boolean;
  missionPaused: boolean;
  stagingCountdown: number;
  markingMode: boolean;
  onToggleMarkingMode: () => void;
  onStartMission: () => void;
  onPauseMission: () => void;
  onResumeMission: () => void;
  onSkipWaypoint: () => void;
  onClearWaypoints: () => void;
  onDeleteWaypoint: (id: string) => void;
  onSimulateArrival: () => void;
  totalDistanceMeters: number;
  darkMode: boolean;
  liveSoilMoisture1: number;
  liveSoilMoisture2: number;
  liveTemperature: number;
  liveHumidity: number;
  currentDiseases: string[];
}

export const WaypointMissionPanel: React.FC<WaypointMissionPanelProps> = ({
  waypoints,
  activeWpIndex,
  missionActive,
  missionPaused,
  stagingCountdown,
  markingMode,
  onToggleMarkingMode,
  onStartMission,
  onPauseMission,
  onResumeMission,
  onSkipWaypoint,
  onClearWaypoints,
  onDeleteWaypoint,
  onSimulateArrival,
  totalDistanceMeters,
  darkMode,
  liveSoilMoisture1,
  liveSoilMoisture2,
  liveTemperature,
  liveHumidity,
  currentDiseases
}) => {
  const { t, language } = useLanguage();
  const [showReportModal, setShowReportModal] = useState(false);

  const completedCount = waypoints.filter(w => w.status === 'completed').length;
  const isInspecting = missionActive && stagingCountdown > 0;
  const currentWp = activeWpIndex !== null && activeWpIndex >= 0 && activeWpIndex < waypoints.length
    ? waypoints[activeWpIndex]
    : null;

  const formatDist = (meters: number) => {
    if (meters < 1000) return `${meters.toFixed(1)} m`;
    return `${(meters / 1000).toFixed(2)} km`;
  };

  const handleExportCSV = () => {
    const headers = ["Waypoint", "Latitude", "Longitude", "Status", "Soil_Moisture_ZoneA", "Soil_Moisture_ZoneB", "Temperature_C", "Humidity_Pct", "Diseases_Detected", "Timestamp"];
    const rows = waypoints.map(wp => [
      `WP ${wp.idx}`,
      wp.lat.toFixed(6),
      wp.lng.toFixed(6),
      wp.status,
      wp.inspectionReport?.soilMoisture1 ?? "N/A",
      wp.inspectionReport?.soilMoisture2 ?? "N/A",
      wp.inspectionReport?.temperature ?? "N/A",
      wp.inspectionReport?.humidity ?? "N/A",
      `"${(wp.inspectionReport?.diseases || []).join('; ') || 'Healthy / None'}"`,
      wp.inspectionReport?.timestamp ?? "N/A"
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `cropguard_mission_report_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{
      background: darkMode ? '#1c1324' : '#ffffff',
      border: `1px solid ${darkMode ? 'rgba(224,64,160,0.25)' : 'rgba(220,200,224,0.6)'}`,
      borderRadius: 16,
      overflow: 'hidden',
      boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Top Header */}
      <div style={{
        padding: '14px 18px',
        background: darkMode ? 'rgba(224,64,160,0.08)' : 'rgba(224,64,160,0.04)',
        borderBottom: `1px solid ${darkMode ? 'rgba(224,64,160,0.2)' : 'rgba(220,200,224,0.5)'}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="material-symbols-outlined" style={{ color: '#e040a0', fontSize: '1.4rem' }}>
            route
          </span>
          <div>
            <div style={{ fontWeight: '850', fontSize: '1rem', color: darkMode ? '#fff' : '#2e1a28' }}>
              {t('waypointMission')}
            </div>
            <div style={{ fontSize: '0.75rem', color: darkMode ? '#a088a5' : '#7e6884' }}>
              {waypoints.length} {t('totalWaypoints')} · {formatDist(totalDistanceMeters)} {t('totalDistance')} · {completedCount} Done
            </div>
          </div>
        </div>

        {/* Action Button Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {/* Waypoint Marking Mode Toggle Button */}
          <button
            onClick={onToggleMarkingMode}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 13px',
              borderRadius: 8,
              border: markingMode ? '1.5px solid #00e5ff' : '1px solid rgba(224,64,160,0.3)',
              background: markingMode ? 'rgba(0,229,255,0.18)' : (darkMode ? '#2a1a33' : '#f8f4f9'),
              color: markingMode ? '#00e5ff' : (darkMode ? '#fff' : '#2e1a28'),
              fontWeight: '750',
              fontSize: '0.78rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: markingMode ? '0 0 12px rgba(0,229,255,0.4)' : 'none'
            }}
            title="Click anywhere on the map to add waypoint pins"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>
              {markingMode ? 'pin_drop' : 'add_location_alt'}
            </span>
            {markingMode ? t('waypointMarkingActive') : t('waypointMarkingMode')}
          </button>

          {/* Mission Start / Pause Button */}
          {!missionActive ? (
            <button
              onClick={onStartMission}
              disabled={waypoints.length === 0}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 15px',
                borderRadius: 8,
                border: 'none',
                background: waypoints.length > 0 ? 'linear-gradient(135deg, #10b981, #059669)' : '#666',
                color: '#fff',
                fontWeight: '800',
                fontSize: '0.8rem',
                cursor: waypoints.length > 0 ? 'pointer' : 'not-allowed',
                opacity: waypoints.length > 0 ? 1 : 0.6,
                boxShadow: waypoints.length > 0 ? '0 4px 14px rgba(16,185,129,0.4)' : 'none'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>play_arrow</span>
              {t('startMission')}
            </button>
          ) : missionPaused ? (
            <button
              onClick={onResumeMission}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 15px',
                borderRadius: 8,
                border: 'none',
                background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                color: '#fff',
                fontWeight: '800',
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(59,130,246,0.4)'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>play_arrow</span>
              {t('resumeMission')}
            </button>
          ) : (
            <button
              onClick={onPauseMission}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 15px',
                borderRadius: 8,
                border: 'none',
                background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                color: '#fff',
                fontWeight: '800',
                fontSize: '0.8rem',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(245,158,11,0.4)'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>pause</span>
              {t('pauseMission')}
            </button>
          )}

          {/* Skip Waypoint */}
          {missionActive && (
            <button
              onClick={onSkipWaypoint}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '7px 11px',
                borderRadius: 8,
                border: `1px solid ${darkMode ? 'rgba(255,255,255,0.2)' : '#ccc'}`,
                background: darkMode ? '#22162b' : '#f2edf5',
                color: darkMode ? '#fff' : '#333',
                fontSize: '0.76rem',
                fontWeight: '650',
                cursor: 'pointer'
              }}
              title="Skip active point and proceed to next"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>skip_next</span>
              {t('skipWaypoint')}
            </button>
          )}

          {/* Benchtop Simulation Arrival Button */}
          {missionActive && !isInspecting && (
            <button
              onClick={onSimulateArrival}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '7px 11px',
                borderRadius: 8,
                border: '1px dashed #e040a0',
                background: 'rgba(224,64,160,0.12)',
                color: '#e040a0',
                fontSize: '0.76rem',
                fontWeight: '700',
                cursor: 'pointer'
              }}
              title="Trigger arrival at current target waypoint immediately (Desk/Lab test)"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>near_me</span>
              {t('simulateArrival')}
            </button>
          )}

          {/* View Reports Button */}
          {completedCount > 0 && (
            <button
              onClick={() => setShowReportModal(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4,
                padding: '7px 11px',
                borderRadius: 8,
                border: '1px solid #10b981',
                background: 'rgba(16,185,129,0.12)',
                color: '#10b981',
                fontSize: '0.76rem',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>assessment</span>
              {t('inspectionReport')} ({completedCount})
            </button>
          )}

          {/* Clear Waypoints */}
          <button
            onClick={onClearWaypoints}
            disabled={waypoints.length === 0}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '7px 11px',
              borderRadius: 8,
              border: `1px solid ${darkMode ? 'rgba(239,68,68,0.3)' : 'rgba(239,68,68,0.2)'}`,
              background: 'rgba(239,68,68,0.08)',
              color: '#ef4444',
              fontSize: '0.76rem',
              fontWeight: '650',
              cursor: waypoints.length > 0 ? 'pointer' : 'not-allowed',
              opacity: waypoints.length > 0 ? 1 : 0.5
            }}
            title="Clear all marked waypoints"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>delete_sweep</span>
            {t('clearWaypoints')}
          </button>
        </div>
      </div>

      {/* 2-MINUTE STAGING INSPECTION ACTIVE BANNER */}
      {isInspecting && currentWp && (
        <div style={{
          padding: '16px 20px',
          background: 'linear-gradient(90deg, rgba(224,64,160,0.18), rgba(16,185,129,0.18))',
          borderBottom: '2px solid #e040a0',
          display: 'flex',
          flexDirection: 'column',
          gap: 12
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {/* Circular Staging Countdown Timer */}
              <div style={{
                position: 'relative',
                width: 54,
                height: 54,
                borderRadius: '50%',
                background: darkMode ? '#150f1c' : '#ffffff',
                border: '3px solid #e040a0',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 15px rgba(224,64,160,0.5)'
              }}>
                <div style={{ fontSize: '1.1rem', fontWeight: '900', color: '#e040a0', lineHeight: 1 }}>
                  {stagingCountdown}
                </div>
                <div style={{ fontSize: '0.55rem', fontWeight: '700', color: darkMode ? '#ccc' : '#666' }}>SEC</div>
              </div>

              <div>
                <div style={{ fontWeight: '850', fontSize: '1.05rem', color: darkMode ? '#fff' : '#2e1a28', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="material-symbols-outlined" style={{ color: '#10b981' }}>
                    sync
                  </span>
                  WP {currentWp.idx} {t('statusInspecting')}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: '700', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>sensors</span>
                  {t('soilProbeLowered')} · Relay 2 (GPIO 11) & Relay 3 (GPIO 12) ACTIVE
                </div>
              </div>
            </div>

            {/* Live sampled metrics preview */}
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <div style={{
                background: darkMode ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.7)',
                padding: '6px 12px',
                borderRadius: 8,
                border: '1px solid rgba(16,185,129,0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.68rem', color: '#10b981', fontWeight: '700' }}>SOIL MOISTURE A</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '900', color: darkMode ? '#fff' : '#2e1a28' }}>
                  {liveSoilMoisture1.toFixed(1)}%
                </div>
              </div>
              <div style={{
                background: darkMode ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.7)',
                padding: '6px 12px',
                borderRadius: 8,
                border: '1px solid rgba(16,185,129,0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.68rem', color: '#10b981', fontWeight: '700' }}>SOIL MOISTURE B</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '900', color: darkMode ? '#fff' : '#2e1a28' }}>
                  {liveSoilMoisture2.toFixed(1)}%
                </div>
              </div>
              <div style={{
                background: darkMode ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.7)',
                padding: '6px 12px',
                borderRadius: 8,
                border: '1px solid rgba(224,64,160,0.3)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.68rem', color: '#e040a0', fontWeight: '700' }}>AI PATHOGEN DETECT</div>
                <div style={{ fontSize: '0.9rem', fontWeight: '800', color: darkMode ? '#fff' : '#2e1a28', marginTop: 2 }}>
                  {currentDiseases.length > 0 ? (
                    <span style={{ color: '#ef4444' }}>{currentDiseases[0]}</span>
                  ) : (
                    <span style={{ color: '#10b981' }}>Healthy Crop</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Staging Progress Bar (120s down to 0) */}
          <div style={{
            width: '100%',
            height: 8,
            background: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
            borderRadius: 9999,
            overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              width: `${((120 - stagingCountdown) / 120) * 100}%`,
              background: 'linear-gradient(90deg, #e040a0, #10b981)',
              borderRadius: 9999,
              transition: 'width 1s linear',
              boxShadow: '0 0 10px #e040a0'
            }} />
          </div>
        </div>
      )}

      {/* Marking Instructions Bar if marking mode is active */}
      {markingMode && (
        <div style={{
          padding: '8px 18px',
          background: 'rgba(0,229,255,0.12)',
          borderBottom: '1px solid rgba(0,229,255,0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: '0.8rem',
          color: darkMode ? '#00e5ff' : '#0284c7',
          fontWeight: '650'
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>touch_app</span>
          <span>
            'Click anywhere on the map to place inspection waypoints. The rover will autonomously navigate each point in order.'
          </span>
        </div>
      )}

      {/* Waypoints Queue Table / List */}
      <div style={{ padding: '12px 18px', maxHeight: 220, overflowY: 'auto' }}>
        {waypoints.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '24px 10px',
            color: darkMode ? '#8e7994' : '#99849e',
            fontSize: '0.86rem'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '2rem', display: 'block', marginBottom: 6, opacity: 0.7 }}>
              wrong_location
            </span>
            'No waypoints placed yet. Enable "Waypoint Marking Mode" and click on the map to define inspection targets.'
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
            {waypoints.map((wp, i) => {
              const isTarget = activeWpIndex === i && missionActive;
              let statusColor = '#94a3b8';
              let statusBg = 'rgba(148,163,184,0.1)';
              let statusLabel = 'PENDING';

              if (wp.status === 'completed') {
                statusColor = '#10b981';
                statusBg = 'rgba(16,185,129,0.15)';
                statusLabel = 'COMPLETED';
              } else if (wp.status === 'inspecting') {
                statusColor = '#e040a0';
                statusBg = 'rgba(224,64,160,0.2)';
                statusLabel = `INSPECTING (${stagingCountdown}s)`;
              } else if (wp.status === 'navigating') {
                statusColor = '#00e5ff';
                statusBg = 'rgba(0,229,255,0.15)';
                statusLabel = 'NAVIGATING';
              }

              return (
                <div
                  key={wp.id}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 10,
                    background: isTarget
                      ? (darkMode ? 'rgba(224,64,160,0.15)' : 'rgba(224,64,160,0.06)')
                      : (darkMode ? '#140c1b' : '#f9f6fa'),
                    border: `1.5px solid ${isTarget ? '#e040a0' : (darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)')}`,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    boxShadow: isTarget ? '0 0 12px rgba(224,64,160,0.3)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {/* Number Badge */}
                    <div style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: isTarget ? '#e040a0' : (wp.status === 'completed' ? '#10b981' : (darkMode ? '#2b1b36' : '#e8dce9')),
                      color: '#fff',
                      fontWeight: '800',
                      fontSize: '0.8rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {wp.idx}
                    </div>

                    <div>
                      <div style={{ fontWeight: '800', fontSize: '0.85rem', color: darkMode ? '#fff' : '#2e1a28' }}>
                        Waypoint #{wp.idx}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: darkMode ? '#99849e' : '#77657b', fontFamily: 'monospace' }}>
                        {wp.lat.toFixed(5)}, {wp.lng.toFixed(5)}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{
                      padding: '3px 7px',
                      borderRadius: 6,
                      background: statusBg,
                      color: statusColor,
                      fontSize: '0.68rem',
                      fontWeight: '800'
                    }}>
                      {statusLabel}
                    </span>

                    {!missionActive && (
                      <button
                        onClick={() => onDeleteWaypoint(wp.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          padding: 2,
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        title="Delete Waypoint"
                      >
                        <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>close</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* COMPLETED INSPECTION REPORT MODAL */}
      {showReportModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20
        }}>
          <div style={{
            background: darkMode ? '#1c1324' : '#ffffff',
            borderRadius: 16,
            maxWidth: 800,
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '2px solid #e040a0',
            boxShadow: '0 10px 40px rgba(0,0,0,0.5)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '16px 20px',
              borderBottom: `1px solid ${darkMode ? 'rgba(255,255,255,0.1)' : '#eee'}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="material-symbols-outlined" style={{ color: '#10b981', fontSize: '1.6rem' }}>
                  task_alt
                </span>
                <div>
                  <div style={{ fontWeight: '850', fontSize: '1.1rem', color: darkMode ? '#fff' : '#2e1a28' }}>
                    {t('inspectionReport')}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: darkMode ? '#a088a5' : '#77657b' }}>
                    Staged Soil Moisture & AI Pathogen Detections
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={handleExportCSV}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 8,
                    background: '#10b981',
                    color: '#fff',
                    border: 'none',
                    fontWeight: '750',
                    fontSize: '0.78rem',
                    cursor: 'pointer'
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>download</span>
                  Export CSV
                </button>
                <button
                  onClick={() => setShowReportModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: darkMode ? '#fff' : '#333',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '1.5rem' }}>close</span>
                </button>
              </div>
            </div>

            {/* Modal Content Table */}
            <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{
                    borderBottom: `2px solid ${darkMode ? 'rgba(255,255,255,0.15)' : '#ddd'}`,
                    textAlign: 'left',
                    color: darkMode ? '#c8b8cd' : '#666'
                  }}>
                    <th style={{ padding: '8px 10px' }}>WP #</th>
                    <th style={{ padding: '8px 10px' }}>Coordinates</th>
                    <th style={{ padding: '8px 10px' }}>Moisture A (R2)</th>
                    <th style={{ padding: '8px 10px' }}>Moisture B (R3)</th>
                    <th style={{ padding: '8px 10px' }}>Air Temp / Humid</th>
                    <th style={{ padding: '8px 10px' }}>Detected Pathogens</th>
                    <th style={{ padding: '8px 10px' }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {waypoints.filter(w => w.status === 'completed').map(wp => (
                    <tr key={wp.id} style={{ borderBottom: `1px solid ${darkMode ? 'rgba(255,255,255,0.06)' : '#eee'}` }}>
                      <td style={{ padding: '10px', fontWeight: '800', color: '#e040a0' }}>WP {wp.idx}</td>
                      <td style={{ padding: '10px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {wp.lat.toFixed(5)}, {wp.lng.toFixed(5)}
                      </td>
                      <td style={{ padding: '10px', fontWeight: '750', color: '#10b981' }}>
                        {wp.inspectionReport?.soilMoisture1?.toFixed(1) ?? '--'}%
                      </td>
                      <td style={{ padding: '10px', fontWeight: '750', color: '#10b981' }}>
                        {wp.inspectionReport?.soilMoisture2?.toFixed(1) ?? '--'}%
                      </td>
                      <td style={{ padding: '10px' }}>
                        {wp.inspectionReport?.temperature?.toFixed(1) ?? '--'}°C · {wp.inspectionReport?.humidity?.toFixed(0) ?? '--'}%
                      </td>
                      <td style={{ padding: '10px' }}>
                        {wp.inspectionReport?.diseases && wp.inspectionReport.diseases.length > 0 ? (
                          <span style={{ color: '#ef4444', fontWeight: '700' }}>
                            {wp.inspectionReport.diseases.join(', ')}
                          </span>
                        ) : (
                          <span style={{ color: '#10b981', fontWeight: '650' }}>Healthy / No Pathogens</span>
                        )}
                      </td>
                      <td style={{ padding: '10px', fontSize: '0.74rem', color: darkMode ? '#a088a5' : '#888' }}>
                        {wp.inspectionReport?.timestamp || '--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
