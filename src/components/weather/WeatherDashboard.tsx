import React, { useState, useEffect } from 'react';
import { WeatherPayload, WeatherAlertItem, DiseaseRiskData, GPSStatusData } from '../../hooks/useSocketData';

interface WeatherDashboardProps {
  weatherData: WeatherPayload | null;
  weatherAlerts: WeatherAlertItem[];
  diseaseRisk: DiseaseRiskData | null;
  gpsStatus: GPSStatusData | null;
  selectedCrop: string;
  darkMode: boolean;
  onRefresh: () => void;
  onRequestAISummary: (crop: string, callback?: (summary: any) => void) => void;
}

export default function WeatherDashboard({
  weatherData,
  weatherAlerts,
  diseaseRisk,
  gpsStatus,
  selectedCrop,
  darkMode,
  onRefresh,
  onRequestAISummary
}: WeatherDashboardProps) {
  const [activeTab, setActiveTab] = useState<'forecast' | 'charts' | 'agri'>('forecast');
  const [chartMetric, setChartMetric] = useState<'temp' | 'rain' | 'humidity' | 'wind'>('temp');
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState<boolean>(false);
  const [secondsAgo, setSecondsAgo] = useState<number>(0);

  useEffect(() => {
    setSecondsAgo(0);
    const interval = setInterval(() => {
      setSecondsAgo(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [weatherData?.fetched_at]);

  const handleFetchAISummary = () => {
    setAiLoading(true);
    onRequestAISummary(selectedCrop, (data) => {
      setAiLoading(false);
      if (data && data.summary) {
        setAiSummary(data.summary);
      }
    });
  };

  const curr = weatherData?.current;
  const daily = weatherData?.daily || [];
  const hourly = weatherData?.hourly || [];

  const bgCard = darkMode ? '#1c1223' : '#ffffff';
  const borderCard = darkMode ? 'rgba(224,64,160,0.2)' : 'rgba(220,200,224,0.4)';
  const textPrimary = darkMode ? '#ffffff' : '#2e1a28';
  const textSecondary = darkMode ? '#b1a2b7' : '#85708c';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, width: '100%' }}>
      {/* 1. Header Bar: Location, GPS Coordinates, & Sync Status */}
      <div style={{
        background: bgCard,
        border: '1.5px solid ' + borderCard,
        borderRadius: 16,
        padding: '16px 20px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 12,
        boxShadow: darkMode ? '0 4px 20px rgba(0,0,0,0.3)' : '0 4px 20px rgba(224,64,160,0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #0096cc 0%, #e040a0 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 4px 12px rgba(0,150,204,0.3)'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '1.6rem' }}>partly_cloudy_day</span>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '900', color: textPrimary }}>
                {weatherData?.location_name || 'Farm Meteorological Station'}
              </h2>
              {weatherData?.is_offline_fallback && (
                <span style={{
                  background: 'rgba(255,183,3,0.15)',
                  border: '1px solid #ffb703',
                  color: '#ffb703',
                  padding: '2px 8px',
                  borderRadius: 6,
                  fontSize: '0.65rem',
                  fontWeight: '800'
                }}>
                  OFFLINE CACHE
                </span>
              )}
            </div>
            <div style={{ fontSize: '0.72rem', color: textSecondary, marginTop: 2, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📍 {weatherData?.latitude?.toFixed(4)}°N, {weatherData?.longitude?.toFixed(4)}°E</span>
              <span>•</span>
              <span>🛰 GPS: {gpsStatus?.is_fixed ? 'FIXED (±' + (gpsStatus?.accuracy || 2.1) + 'm)' : 'SIMULATED'}</span>
              <span>•</span>
              <span>⚡ Provider: {weatherData?.provider || 'Open-Meteo'}</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ textAlign: 'right', marginRight: 4 }}>
            <div style={{ fontSize: '0.65rem', color: textSecondary, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Data Freshness</div>
            <div style={{ fontSize: '0.8rem', fontWeight: '800', color: '#0096cc' }}>
              {secondsAgo < 60 ? secondsAgo + 's ago' : Math.floor(secondsAgo / 60) + 'm ago'}
            </div>
          </div>
          
          <button
            onClick={onRefresh}
            style={{
              background: 'rgba(0,150,204,0.12)',
              border: '1.5px solid #0096cc',
              borderRadius: 10,
              padding: '8px 14px',
              color: '#0096cc',
              fontWeight: '800',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>sync</span>
            Sync Weather
          </button>

          <button
            onClick={handleFetchAISummary}
            disabled={aiLoading}
            style={{
              background: 'linear-gradient(135deg, #e040a0 0%, #7c52aa 100%)',
              border: 'none',
              borderRadius: 10,
              padding: '8px 14px',
              color: '#fff',
              fontWeight: '800',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 2px 10px rgba(224,64,160,0.3)'
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>psychology</span>
            {aiLoading ? 'Analyzing...' : 'AI Briefing'}
          </button>
        </div>
      </div>

      {/* 2. Active Weather Alerts Banner */}
      {weatherAlerts && weatherAlerts.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {weatherAlerts.map(alert => (
            <div
              key={alert.id}
              style={{
                background: alert.severity === 'CRITICAL' ? 'rgba(255,75,75,0.12)' : (alert.severity === 'WARNING' ? 'rgba(255,183,3,0.12)' : 'rgba(0,150,204,0.12)'),
                border: '1.5px solid ' + (alert.severity === 'CRITICAL' ? '#ff4b4b' : (alert.severity === 'WARNING' ? '#ffb703' : '#0096cc')),
                borderRadius: 12,
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined" style={{
                  fontSize: '1.6rem',
                  color: alert.severity === 'CRITICAL' ? '#ff4b4b' : (alert.severity === 'WARNING' ? '#ffb703' : '#0096cc')
                }}>
                  {alert.icon}
                </span>
                <div>
                  <div style={{ fontWeight: '850', fontSize: '0.88rem', color: textPrimary }}>{alert.title}</div>
                  <div style={{ fontSize: '0.75rem', color: textSecondary, marginTop: 2 }}>{alert.description}</div>
                </div>
              </div>
              <div style={{
                background: darkMode ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.8)',
                padding: '4px 10px',
                borderRadius: 8,
                fontSize: '0.7rem',
                fontWeight: '700',
                color: alert.severity === 'CRITICAL' ? '#ff4b4b' : (alert.severity === 'WARNING' ? '#ffb703' : '#0096cc'),
                whiteSpace: 'nowrap'
              }}>
                {alert.recommendation}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 3. AI Weather Summary Callout */}
      {aiSummary && (
        <div style={{
          background: darkMode ? 'linear-gradient(135deg, #24142e 0%, #17182e 100%)' : 'linear-gradient(135deg, #fff0f9 0%, #f0f7ff 100%)',
          border: '1.5px solid #e040a0',
          borderRadius: 14,
          padding: '14px 18px',
          display: 'flex',
          gap: 14,
          alignItems: 'flex-start',
          boxShadow: '0 4px 15px rgba(224,64,160,0.1)'
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '1.8rem', color: '#e040a0', marginTop: 2 }}>smart_toy</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.7rem', fontWeight: '800', color: '#e040a0', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>
              DEMET3R AI Crop Weather Diagnostic Summary · {selectedCrop.toUpperCase()}
            </div>
            <div style={{ fontSize: '0.85rem', lineHeight: '1.45', color: textPrimary }}>
              {aiSummary}
            </div>
          </div>
        </div>
      )}

      {/* 4. Current Conditions Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 16
      }}>
        {/* Main Temperature Card */}
        <div style={{
          background: bgCard,
          border: '1.5px solid ' + borderCard,
          borderRadius: 16,
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', color: '#e040a0', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                Live Field Atmospheric Reading
              </span>
              <div style={{ fontSize: '3rem', fontWeight: '900', color: textPrimary, marginTop: 4, lineHeight: 1 }}>
                {curr ? curr.temperature + '°C' : '--'}
              </div>
              <div style={{ fontSize: '0.8rem', color: textSecondary, marginTop: 6 }}>
                Feels like <strong style={{ color: textPrimary }}>{curr ? curr.feels_like + '°C' : '--'}</strong>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '3.2rem', color: '#0096cc' }}>
                {curr?.weather_icon || 'partly_cloudy_day'}
              </span>
              <div style={{ fontWeight: '850', fontSize: '0.95rem', color: textPrimary, marginTop: 4 }}>
                {curr?.weather_condition || 'Partly Cloudy'}
              </div>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 8,
            marginTop: 18,
            paddingTop: 14,
            borderTop: '1px solid ' + (darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)')
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: textSecondary, textTransform: 'uppercase' }}>Sunrise</div>
              <div style={{ fontSize: '0.82rem', fontWeight: '800', color: textPrimary, marginTop: 2 }}>🌅 {curr?.sunrise || '06:00'}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: textSecondary, textTransform: 'uppercase' }}>Sunset</div>
              <div style={{ fontSize: '0.82rem', fontWeight: '800', color: textPrimary, marginTop: 2 }}>🌇 {curr?.sunset || '18:15'}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.62rem', color: textSecondary, textTransform: 'uppercase' }}>Day / Night</div>
              <div style={{ fontSize: '0.82rem', fontWeight: '800', color: '#0096cc', marginTop: 2 }}>{curr?.is_day ? '☀️ Daytime' : '🌙 Night'}</div>
            </div>
          </div>
        </div>

        {/* Multi-Parameter Metric Tiles */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: 12
        }}>
          {/* Humidity */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#0096cc' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>water_drop</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>Humidity</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.humidity + '%' : '--'}
            </div>
            <div style={{ fontSize: '0.65rem', color: curr && curr.humidity > 75 ? '#ffb703' : textSecondary, marginTop: 2 }}>
              {curr && curr.humidity > 75 ? '⚠️ High fungal risk' : 'Optimal range'}
            </div>
          </div>

          {/* Rain Probability */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#e040a0' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>rainy</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>Rain Chance</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.rain_probability + '%' : '--'}
            </div>
            <div style={{ fontSize: '0.65rem', color: textSecondary, marginTop: 2 }}>
              Precip: {curr ? curr.precipitation + ' mm' : '0 mm'}
            </div>
          </div>

          {/* Wind Speed & Direction */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#7c52aa' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>air</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>Wind</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.wind_speed + ' km/h' : '--'}
            </div>
            <div style={{ fontSize: '0.65rem', color: textSecondary, marginTop: 2 }}>
              🧭 {curr?.wind_direction_cardinal || 'N'} ({curr?.wind_direction || 0}°)
            </div>
          </div>

          {/* UV Index */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#ffb703' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>wb_sunny</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>UV Index</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.uv_index : '--'}
            </div>
            <div style={{
              fontSize: '0.65rem',
              fontWeight: '700',
              color: curr && curr.uv_index >= 8 ? '#ff4b4b' : (curr && curr.uv_index >= 6 ? '#ffb703' : '#0096cc'),
              marginTop: 2
            }}>
              {curr && curr.uv_index >= 8 ? 'Very High' : (curr && curr.uv_index >= 6 ? 'Moderate' : 'Low / Safe')}
            </div>
          </div>

          {/* Cloud Cover */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: textSecondary }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>cloud</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>Clouds</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.cloud_cover + '%' : '--'}
            </div>
            <div style={{ fontSize: '0.65rem', color: textSecondary, marginTop: 2 }}>
              Pressure: {curr?.pressure || 1013} hPa
            </div>
          </div>

          {/* Visibility */}
          <div style={{ background: bgCard, border: '1.5px solid ' + borderCard, borderRadius: 14, padding: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#00cc88' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>visibility</span>
              <span style={{ fontSize: '0.68rem', fontWeight: '800', textTransform: 'uppercase' }}>Visibility</span>
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: '900', color: textPrimary, marginTop: 6 }}>
              {curr ? curr.visibility + ' km' : '--'}
            </div>
            <div style={{ fontSize: '0.65rem', color: '#00cc88', marginTop: 2 }}>
              Clear drone flight
            </div>
          </div>
        </div>
      </div>

      {/* 5. 24-Hour Hourly Timeline (Scrollable) */}
      <div style={{
        background: bgCard,
        border: '1.5px solid ' + borderCard,
        borderRadius: 16,
        padding: '18px 20px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '800', color: '#0096cc', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="material-symbols-outlined" style={{ fontSize: '1.2rem' }}>schedule</span>
            24-Hour Hourly Weather Forecast Timeline
          </div>
          <span style={{ fontSize: '0.68rem', color: textSecondary }}>Scroll horizontally ➔</span>
        </div>

        <div style={{
          display: 'flex',
          gap: 12,
          overflowX: 'auto',
          paddingBottom: 8
        }}>
          {hourly && hourly.length > 0 ? (
            hourly.map((h, idx) => (
              <div
                key={idx}
                style={{
                  minWidth: 80,
                  background: darkMode ? 'rgba(255,255,255,0.03)' : 'rgba(224,64,160,0.03)',
                  border: '1px solid ' + (darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(220,200,224,0.4)'),
                  borderRadius: 12,
                  padding: '10px 8px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 4
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: '750', color: textSecondary }}>{h.time}</div>
                <span className="material-symbols-outlined" style={{ fontSize: '1.5rem', color: '#0096cc', margin: '2px 0' }}>
                  {h.weather_icon}
                </span>
                <div style={{ fontSize: '0.92rem', fontWeight: '900', color: textPrimary }}>{h.temperature}°</div>
                <div style={{
                  fontSize: '0.62rem',
                  fontWeight: '800',
                  color: h.rain_probability > 50 ? '#e040a0' : textSecondary,
                  background: h.rain_probability > 50 ? 'rgba(224,64,160,0.12)' : 'transparent',
                  padding: '1px 4px',
                  borderRadius: 4
                }}>
                  💧{h.rain_probability}%
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.8rem', color: textSecondary, padding: 10 }}>Hourly data loading...</div>
          )}
        </div>
      </div>

      {/* 6. Main Feature Tabs */}
      <div style={{
        background: bgCard,
        border: '1.5px solid ' + borderCard,
        borderRadius: 16,
        padding: '20px'
      }}>
        {/* Tab Switcher */}
        <div style={{
          display: 'flex',
          gap: 10,
          borderBottom: '1px solid ' + (darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(220,200,224,0.4)'),
          paddingBottom: 12,
          marginBottom: 16
        }}>
          <button
            onClick={() => setActiveTab('forecast')}
            style={{
              background: activeTab === 'forecast' ? 'rgba(224,64,160,0.12)' : 'transparent',
              border: '1.5px solid ' + (activeTab === 'forecast' ? '#e040a0' : 'transparent'),
              borderRadius: 8,
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: '800',
              color: activeTab === 'forecast' ? '#e040a0' : textSecondary,
              cursor: 'pointer'
            }}
          >
            📅 7-Day Forecast Grid
          </button>

          <button
            onClick={() => setActiveTab('charts')}
            style={{
              background: activeTab === 'charts' ? 'rgba(0,150,204,0.12)' : 'transparent',
              border: '1.5px solid ' + (activeTab === 'charts' ? '#0096cc' : 'transparent'),
              borderRadius: 8,
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: '800',
              color: activeTab === 'charts' ? '#0096cc' : textSecondary,
              cursor: 'pointer'
            }}
          >
            📈 Weather Charts
          </button>

          <button
            onClick={() => setActiveTab('agri')}
            style={{
              background: activeTab === 'agri' ? 'rgba(0,204,136,0.12)' : 'transparent',
              border: '1.5px solid ' + (activeTab === 'agri' ? '#00cc88' : 'transparent'),
              borderRadius: 8,
              padding: '6px 14px',
              fontSize: '0.78rem',
              fontWeight: '800',
              color: activeTab === 'agri' ? '#00cc88' : textSecondary,
              cursor: 'pointer'
            }}
          >
            🌱 Crop Health & Irrigation
          </button>
        </div>

        {/* Tab 1: 7-Day Forecast Grid */}
        {activeTab === 'forecast' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: 12
          }}>
            {daily.map((d, i) => (
              <div
                key={i}
                style={{
                  background: i === 0 ? (darkMode ? 'rgba(224,64,160,0.08)' : 'rgba(224,64,160,0.05)') : (darkMode ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.02)'),
                  border: '1.5px solid ' + (i === 0 ? '#e040a0' : (darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(220,200,224,0.3)')),
                  borderRadius: 14,
                  padding: '14px 10px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 6
                }}
              >
                <div style={{ fontWeight: '900', fontSize: '0.85rem', color: i === 0 ? '#e040a0' : textPrimary }}>
                  {d.day_name}
                </div>
                <div style={{ fontSize: '0.65rem', color: textSecondary }}>{d.date.slice(5)}</div>
                
                <span className="material-symbols-outlined" style={{ fontSize: '2.2rem', color: '#0096cc', margin: '4px 0' }}>
                  {d.weather_icon}
                </span>

                <div style={{ fontSize: '0.72rem', color: textSecondary, minHeight: 28, display: 'flex', alignItems: 'center' }}>
                  {d.weather_condition}
                </div>

                <div style={{ fontSize: '1rem', fontWeight: '900', color: textPrimary }}>
                  {d.temp_max}° <span style={{ fontSize: '0.8rem', color: textSecondary, fontWeight: '600' }}>/ {d.temp_min}°</span>
                </div>

                <div style={{
                  width: '100%',
                  background: d.rain_probability > 60 ? 'rgba(224,64,160,0.15)' : 'rgba(0,150,204,0.1)',
                  borderRadius: 6,
                  padding: '4px 2px',
                  fontSize: '0.68rem',
                  fontWeight: '800',
                  color: d.rain_probability > 60 ? '#e040a0' : '#0096cc',
                  marginTop: 4
                }}>
                  🌧 {d.rain_probability}% ({d.precipitation_sum}mm)
                </div>

                <div style={{ fontSize: '0.62rem', color: textSecondary, marginTop: 2 }}>
                  💨 {d.wind_speed_max} km/h · ☀ UV {d.uv_index_max}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Interactive Weather Charts */}
        {activeTab === 'charts' && (
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {(['temp', 'rain', 'humidity', 'wind'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => setChartMetric(m)}
                  style={{
                    background: chartMetric === m ? '#0096cc' : 'transparent',
                    border: '1px solid #0096cc',
                    color: chartMetric === m ? '#fff' : '#0096cc',
                    padding: '4px 10px',
                    borderRadius: 6,
                    fontSize: '0.7rem',
                    fontWeight: '800',
                    cursor: 'pointer'
                  }}
                >
                  {m === 'temp' && '🌡 Temperature Trend'}
                  {m === 'rain' && '🌧 Rain Probability (%)'}
                  {m === 'humidity' && '💧 Humidity (%)'}
                  {m === 'wind' && '🌬 Wind Velocity (km/h)'}
                </button>
              ))}
            </div>

            {/* Visual Bar Chart Container */}
            <div style={{
              background: darkMode ? '#120b18' : '#fcfaff',
              border: '1px solid ' + borderCard,
              borderRadius: 12,
              padding: '20px 16px',
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-between',
              height: 220,
              gap: 12
            }}>
              {daily.map((d, idx) => {
                let val = 0;
                let maxVal = 100;
                let label = '';
                let barColor = '#0096cc';

                if (chartMetric === 'temp') {
                  val = d.temp_max;
                  maxVal = 45;
                  label = d.temp_max + '°C';
                  barColor = 'linear-gradient(180deg, #ff4b4b 0%, #e040a0 100%)';
                } else if (chartMetric === 'rain') {
                  val = d.rain_probability;
                  maxVal = 100;
                  label = d.rain_probability + '%';
                  barColor = 'linear-gradient(180deg, #0096cc 0%, #00cc88 100%)';
                } else if (chartMetric === 'humidity') {
                  val = d.humidity_avg;
                  maxVal = 100;
                  label = d.humidity_avg + '%';
                  barColor = 'linear-gradient(180deg, #7c52aa 0%, #0096cc 100%)';
                } else {
                  val = d.wind_speed_max;
                  maxVal = 50;
                  label = d.wind_speed_max + 'k';
                  barColor = 'linear-gradient(180deg, #ffb703 0%, #e040a0 100%)';
                }

                const heightPct = Math.min(100, Math.max(15, (val / maxVal) * 100));

                return (
                  <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: '800', color: textPrimary }}>{label}</div>
                    <div style={{
                      width: '100%',
                      maxWidth: 42,
                      height: heightPct + '%',
                      background: barColor,
                      borderRadius: '8px 8px 3px 3px',
                      transition: 'height 0.4s ease'
                    }} />
                    <div style={{ fontSize: '0.68rem', fontWeight: '800', color: textSecondary, marginTop: 4 }}>{d.day_name}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 3: Crop Health & Smart Irrigation Insight */}
        {activeTab === 'agri' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
            {/* Smart Irrigation Advisor */}
            <div style={{
              background: darkMode ? '#120b18' : '#fcfaff',
              border: '1.5px solid ' + (diseaseRisk?.smart_irrigation?.status === 'RED' ? '#ff4b4b' : (diseaseRisk?.smart_irrigation?.status === 'YELLOW' ? '#ffb703' : '#00cc88')),
              borderRadius: 14,
              padding: '18px'
            }}>
              <div style={{ fontSize: '0.68rem', fontWeight: '800', color: textSecondary, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                Smart Irrigation Decision Support
              </div>
              <div style={{ fontSize: '1.15rem', fontWeight: '900', color: textPrimary, marginTop: 4 }}>
                {diseaseRisk?.smart_irrigation?.headline || '🟢 No Irrigation Needed'}
              </div>
              <p style={{ fontSize: '0.8rem', color: textSecondary, lineHeight: '1.4', marginTop: 8 }}>
                {diseaseRisk?.smart_irrigation?.advice || 'Soil moisture is optimal and upcoming rainfall is expected.'}
              </p>
              
              <div style={{ display: 'flex', gap: 12, marginTop: 14, borderTop: '1px solid ' + (darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'), paddingTop: 10 }}>
                <div>
                  <div style={{ fontSize: '0.6rem', color: textSecondary }}>Soil Hydration</div>
                  <div style={{ fontWeight: '850', color: '#00cc88' }}>{diseaseRisk?.smart_irrigation?.soil_moisture_pct || 72}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.6rem', color: textSecondary }}>3-Day Rain Probability</div>
                  <div style={{ fontWeight: '850', color: '#0096cc' }}>{diseaseRisk?.smart_irrigation?.avg_rain_chance_3d || 45}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.6rem', color: textSecondary }}>7-Day Total Rain</div>
                  <div style={{ fontWeight: '850', color: '#e040a0' }}>{diseaseRisk?.smart_irrigation?.total_rain_7d_mm || 18.5} mm</div>
                </div>
              </div>
            </div>

            {/* Weather-Based Disease Risk Meters */}
            <div style={{
              background: darkMode ? '#120b18' : '#fcfaff',
              border: '1.5px solid ' + borderCard,
              borderRadius: 14,
              padding: '18px'
            }}>
              <div style={{ fontSize: '0.68rem', fontWeight: '800', color: '#e040a0', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                Environmental Disease Risk Indexes ({selectedCrop.toUpperCase()})
              </div>

              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {diseaseRisk?.specific_pathogen_risks?.map((risk, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: '800', color: textPrimary, marginBottom: 4 }}>
                      <span>{risk.name} ({risk.type})</span>
                      <span style={{ color: risk.risk_pct > 70 ? '#ff4b4b' : (risk.risk_pct > 40 ? '#ffb703' : '#00cc88') }}>
                        {risk.risk_pct}% · {risk.level}
                      </span>
                    </div>
                    <div style={{ width: '100%', height: 7, background: darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{
                        width: risk.risk_pct + '%',
                        height: '100%',
                        background: risk.risk_pct > 70 ? '#ff4b4b' : (risk.risk_pct > 40 ? '#ffb703' : '#00cc88'),
                        borderRadius: 4,
                        transition: 'width 0.4s'
                      }} />
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: '0.62rem', color: textSecondary, fontStyle: 'italic', marginTop: 14 }}>
                ℹ️ {diseaseRisk?.disclaimer || 'AI / Environmental Risk Estimate — Decision-support tool, not a scientific diagnostic guarantee.'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
