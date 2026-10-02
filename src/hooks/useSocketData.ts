/**
 * @file useSocketData.ts
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

import { BACKEND_URL } from '../backendUrl';
import { useEffect, useRef, useCallback, Dispatch, SetStateAction } from 'react';
import { io, Socket } from 'socket.io-client';
import { SensorData, DiseaseItem, Recommendation, LogEntry } from '../App';

export interface WeatherCurrent {
  temperature: number;
  feels_like: number;
  humidity: number;
  pressure: number;
  rain_probability: number;
  precipitation: number;
  wind_speed: number;
  wind_direction: number;
  wind_direction_cardinal: string;
  uv_index: number;
  cloud_cover: number;
  visibility: number;
  weather_code: number;
  weather_condition: string;
  weather_icon: string;
  sunrise: string;
  sunset: string;
  is_day: boolean;
  timestamp: string;
}

export interface HourlyForecastItem {
  time: string;
  full_time: string;
  temperature: number;
  feels_like: number;
  humidity: number;
  rain_probability: number;
  precipitation: number;
  wind_speed: number;
  uv_index: number;
  weather_condition: string;
  weather_icon: string;
  weather_code: number;
}

export interface DailyForecastItem {
  date: string;
  day_name: string;
  temp_max: number;
  temp_min: number;
  rain_probability: number;
  precipitation_sum: number;
  humidity_avg: number;
  wind_speed_max: number;
  wind_direction: string;
  uv_index_max: number;
  weather_condition: string;
  weather_icon: string;
  weather_code: number;
  sunrise: string;
  sunset: string;
}

export interface WeatherPayload {
  latitude: number;
  longitude: number;
  location_name: string;
  provider: string;
  is_cached?: boolean;
  is_offline_fallback?: boolean;
  current: WeatherCurrent;
  hourly: HourlyForecastItem[];
  daily: DailyForecastItem[];
  fetched_at: string;
}

export interface WeatherAlertItem {
  id: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  type: string;
  icon: string;
  title: string;
  description: string;
  recommendation: string;
}

export interface DiseaseRiskData {
  crop: string;
  fungal_risk_pct: number;
  bacterial_risk_pct: number;
  overall_environmental_risk: string;
  specific_pathogen_risks: Array<{
    name: string;
    type: string;
    risk_pct: number;
    level: string;
  }>;
  smart_irrigation: {
    status: 'GREEN' | 'YELLOW' | 'RED';
    headline: string;
    advice: string;
    soil_moisture_pct: number;
    avg_rain_chance_3d: number;
    total_rain_7d_mm: number;
  };
  disclaimer: string;
}

export interface GPSStatusData {
  latitude: number;
  longitude: number;
  altitude: number;
  speed: number;
  heading: number;
  accuracy: number;
  is_fixed: boolean;
  last_updated: string;
}

export interface ObstacleStatus {
  detected: boolean;
  action: 'FORWARD' | 'STEER_LEFT' | 'STEER_RIGHT' | 'STOP';
  clearance: {
    left: number;
    center: number;
    right: number;
  };
  warning: string;
  timestamp?: number;
}

export interface AIAnalysisReport {
  disease: string;
  confidence: number;
  reason?: string;
  reason_sinhala?: string;
  recovery_plan: string[];
  severity: string;
  treatment_duration_sec: number;
}

export function useSocketData(
  setSensorData: Dispatch<SetStateAction<SensorData>>,
  setDiseases: (diseases: DiseaseItem[]) => void,
  setRecommendation: (rec: Recommendation | null) => void,
  setConnected: (connected: boolean) => void,
  setEfficiency: (eff: number) => void,
  addLog: (msg: string, type: LogEntry['type']) => void,
  selectedCrop: string,
  setModeState?: (mode: 'auto' | 'manual') => void,
  setBrainState?: (state: string) => void,
  setAiReportState?: (report: AIAnalysisReport | null) => void,
  setOllamaStatusState?: (status: { online: boolean; vl_ready: boolean; coder_ready: boolean }) => void,
  setWeatherDataState?: (data: WeatherPayload) => void,
  setWeatherAlertsState?: (alerts: WeatherAlertItem[]) => void,
  setDiseaseRiskState?: (risk: DiseaseRiskData) => void,
  setGpsStatusState?: (gps: GPSStatusData) => void,
  setEsp32ConnectedState?: (connected: boolean) => void,
  setObstacleStatusState?: (status: ObstacleStatus) => void,
  setEmergencyStopState?: (latched: boolean) => void
) {
  const socketRef = useRef<Socket | null>(null);
  const selectedCropRef = useRef(selectedCrop);
  selectedCropRef.current = selectedCrop;
  const hardwareConnectedRef = useRef<boolean | null>(null);
  const latestTelemetryRef = useRef<any>(null);
  const rafIdRef = useRef<number | null>(null);

  // High-performance RAF throttle for smooth 60fps rendering without event flooding
  const scheduleTelemetryFlush = useCallback(() => {
    if (rafIdRef.current !== null) return;
    rafIdRef.current = requestAnimationFrame(() => {
      rafIdRef.current = null;
      const data = latestTelemetryRef.current;
      if (!data) return;

      setSensorData((prev: SensorData) => ({
        ...prev,
        ...data,
        temperature: data.temperature ?? data.temperature_c ?? prev?.temperature ?? 0,
        humidity: data.humidity ?? data.humidity_pct ?? prev?.humidity ?? 0,
        pressure: data.pressure ?? data.pressure_hpa ?? prev?.pressure ?? 1013,
        light: data.light ?? data.lux ?? prev?.light ?? 0,
        uvVoltage: data.uvVoltage ?? data.uv_voltage ?? prev?.uvVoltage ?? 0,
        soilMoisture: data.soilMoisture ?? data.soil1_raw ?? prev?.soilMoisture ?? 0,
        soilMoisture2: data.soilMoisture2 ?? data.soil2_raw ?? prev?.soilMoisture2,
        latitude: data.latitude ?? data.lat ?? prev?.latitude,
        longitude: data.longitude ?? data.lng ?? prev?.longitude,
        fused_latitude: data.fused_latitude ?? prev?.fused_latitude,
        fused_longitude: data.fused_longitude ?? prev?.fused_longitude,
        pos_uncertainty_m: data.pos_uncertainty_m ?? prev?.pos_uncertainty_m,
        fusion_mode: data.fusion_mode ?? prev?.fusion_mode,
        baseline: data.baseline ?? prev?.baseline,
        laptop_gps: data.laptop_gps ?? prev?.laptop_gps,
        rover_gps: data.rover_gps ?? prev?.rover_gps,
        uvIndex: data.uvIndex ?? prev?.uvIndex,
        altitude: data.altitude ?? prev?.altitude,
        speed: data.speed ?? prev?.speed,
        heading: data.heading ?? prev?.heading,
        cardinal: data.cardinal ?? prev?.cardinal,
        satellites: data.satellites ?? prev?.satellites,
        hdop: data.hdop ?? prev?.hdop,
        fix: data.fix ?? prev?.fix,
        pump_on: (data.pump_on !== undefined ? data.pump_on : (data.pump !== undefined ? data.pump : (data.relay1 !== undefined ? data.relay1 : prev?.pump_on))),
        sol1_on: (data.sol1_on !== undefined ? data.sol1_on : (data.sol1 !== undefined ? data.sol1 : (data.relay2 !== undefined ? data.relay2 : prev?.sol1_on))),
        sol2_on: (data.sol2_on !== undefined ? data.sol2_on : (data.sol2 !== undefined ? data.sol2 : (data.relay3 !== undefined ? data.relay3 : prev?.sol2_on))),
        spare_on: (data.spare_on !== undefined ? data.spare_on : (data.spare !== undefined ? data.spare : (data.relay4 !== undefined ? data.relay4 : prev?.spare_on))),
        ultrasonic: data.ultrasonic ?? prev?.ultrasonic,
        ultrasonic_back: data.ultrasonic_back ?? prev?.ultrasonic_back
      }));
    });
  }, [setSensorData]);

  // Initialize socket once on mount
  useEffect(() => {
    socketRef.current = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: Infinity,
    });

    socketRef.current.on('connect', () => {
      console.log('✅ Connected to backend');
      setConnected(true);
      addLog('Connected to DEM3T3R V1 backend', 'success');
      
      // Emit the currently selected crop on connection
      socketRef.current?.emit('crop_selected', { crop: selectedCropRef.current });
    });

    socketRef.current.on('disconnect', () => {
      console.log('❌ Disconnected');
      setConnected(false);
      setDiseases([]);
      latestTelemetryRef.current = null;
      if (rafIdRef.current !== null) { cancelAnimationFrame(rafIdRef.current); rafIdRef.current = null; }
      if (setEsp32ConnectedState) setEsp32ConnectedState(false);
      hardwareConnectedRef.current = null;
      addLog('Disconnected from server', 'error');
    });

    socketRef.current.on('esp32_status', (data: { connected: boolean; ip?: string }) => {
      if (setEsp32ConnectedState) {
        setEsp32ConnectedState(data.connected);
      }
      if (hardwareConnectedRef.current === data.connected) return;
      hardwareConnectedRef.current = data.connected;
      addLog(
        `Robot Hardware: ${data.connected ? 'Connected (' + (data.ip || 'Port 5000') + ')' : 'Disconnected'}`,
        data.connected ? 'success' : 'warning'
      );
    });

    socketRef.current.on('telemetry', (data: any) => {
      if (setEsp32ConnectedState) setEsp32ConnectedState(data.hardware_connected === true);
      latestTelemetryRef.current = data;
      scheduleTelemetryFlush();
    });

    socketRef.current.on('detection_list', (data: { crop?: string; detections: DiseaseItem[] }) => {
      if (data.crop !== selectedCropRef.current) return;
      if (data.detections && data.detections.length > 0) {
        setDiseases(data.detections);
      } else {
        setDiseases([]);
      }
    });

    socketRef.current.on('ai_recommendations', (data: any) => {
      const rec: Recommendation = {
        disease: data.disease,
        confidence: data.confidence,
        reason: data.reason ?? extractSection(data.recommendations, 'REASON'),
        recovery: data.recovery ?? extractSection(data.recommendations, 'RECOVERY PLAN'),
        prediction: data.prediction ?? extractSection(data.recommendations, 'PREDICTION'),
        fertilizer: data.fertilizer ?? extractSection(data.recommendations, 'FERTILIZER'),
      };
      setRecommendation(rec);
      addLog(`AI recommendation received for ${data.disease}`, 'success');
    });

    // Handle new state and diagnostic outputs for autonomous control
    socketRef.current.on('mode_status', (data: { mode: 'auto' | 'manual' }) => {
      if (setModeState && data.mode) {
        setModeState(data.mode);
      }
    });

    socketRef.current.on('state_changed', (data: { state: string; reason?: string }) => {
      if (setBrainState && data.state) {
        setBrainState(data.state);
        addLog(`System state transitioned to: ${data.state}${data.reason ? ' (' + data.reason + ')' : ''}`, 'info');
      }
    });

    socketRef.current.on('ai_analysis_report', (data: AIAnalysisReport) => {
      if (setAiReportState) {
        setAiReportState(data);
      }
      // Set standard recommendation fallback so existing displays work
      setRecommendation({
        disease: data.disease,
        confidence: data.confidence,
        reason: data.reason || data.reason_sinhala || "Pathogen anomaly identified.",
        recovery: data.recovery_plan.join(". "),
        prediction: `Severity: ${data.severity}`,
        fertilizer: `Spray Duration: ${data.treatment_duration_sec}s`
      });
      addLog(`Vision analysis completed for ${data.disease}.`, 'success');
    });

    socketRef.current.on('obstacle_telemetry', (data: ObstacleStatus) => {
      if (setObstacleStatusState && data && data.clearance) {
        setObstacleStatusState(data);
      }
    });

    socketRef.current.on('log_entry', (data: any) => {
      addLog(data.msg, data.type);
    });

    socketRef.current.on('ollama_status', (data: any) => {
      if (setOllamaStatusState) {
        setOllamaStatusState(data);
      }
    });

    socketRef.current.on('weather_update', (data: WeatherPayload) => {
      if (setWeatherDataState && data) {
        setWeatherDataState(data);
      }
    });

    socketRef.current.on('weather_alert', (alerts: WeatherAlertItem[]) => {
      if (setWeatherAlertsState && alerts) {
        setWeatherAlertsState(alerts);
      }
    });

    socketRef.current.on('disease_risk_update', (risk: DiseaseRiskData) => {
      if (setDiseaseRiskState && risk) {
        setDiseaseRiskState(risk);
      }
    });

    socketRef.current.on('gps_update', (gps: GPSStatusData) => {
      if (setGpsStatusState && gps) {
        setGpsStatusState(gps);
      }
      if (gps && typeof gps.latitude === 'number' && typeof gps.longitude === 'number' && (gps.latitude !== 0 || gps.longitude !== 0)) {
        setSensorData((prev: SensorData) => ({
          ...prev,
          latitude: gps.latitude,
          longitude: gps.longitude
        }));
      }
    });

    socketRef.current.on('hardware_command_result', (result: any) => {
      if (!result.sent) addLog(result.message, 'error');
    });
    socketRef.current.on('emergency_stop_status', (status: { latched: boolean }) => {
      setEmergencyStopState?.(status.latched);
    });

    // Cleanup on unmount
    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
      socketRef.current?.disconnect();
    };
  }, [scheduleTelemetryFlush, setConnected, addLog, setDiseases, setEsp32ConnectedState, setSensorData, setEmergencyStopState]);

  // Separate effect for crop change to emit crop_selected without reconnecting
  useEffect(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('crop_selected', { crop: selectedCrop });
      addLog(`Crop selection updated: ${selectedCrop.toUpperCase()}`, 'info');
    }
  }, [selectedCrop, addLog]);

  const extractSection = (text: string, section: string): string => {
    if (!text) return '';
    const regex = new RegExp(`${section}:\\s*([\\s\\S]*?)(?=\\n\\n|🔍|💊|🔮|🌱|$)`, 'i');
    const match = text.match(regex);
    return match ? match[1].trim() : '';
  };

  const selectCrop = (crop: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('crop_selected', { crop });
    }
  };

  const selectModel = (modelFile: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('model_selected', { model: modelFile });
      addLog(`YOLO11m Model Node Load: ${modelFile}`, 'info');
    } else {
      addLog('Failed to change AI model: Offline', 'error');
    }
  };

  const sendRobotControl = (
    direction: 'forward' | 'backward' | 'left' | 'right' | 'stop',
    speed: number = 255,
    source: 'manual' | 'auto' = 'manual',
    differential?: { leftPWM?: number; rightPWM?: number }
  ) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('robot_move', {
        direction,
        speed,
        source,
        autonomous: source === 'auto',
        motor_left: differential?.leftPWM,
        motor_right: differential?.rightPWM
      });
    } else {
      addLog('Robot command unavailable: backend disconnected', 'error');
    }
  };

  const sendPumpControl = (state: boolean) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('toggle_pump', { state });
      addLog(`Water pump command sent: ${state ? 'ON' : 'OFF'}`, 'info');
    } else {
      addLog('Failed to send pump command: Offline', 'error');
    }
  };

  const sendSolenoidControl = (solenoidId: number, action: 'push' | 'pull') => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('control_solenoid', { id: solenoidId, action });
      addLog(`Solenoid ${solenoidId} command sent: ${action.toUpperCase()}`, 'info');
    } else {
      addLog(`Failed to send Solenoid ${solenoidId} command: Offline`, 'error');
    }
  };

  const sendRelayToggle = (target: string, state: boolean) => {
    const targetMap: Record<string, string> = {
      'PUMP': 'R1',
      'SOL1': 'R2',
      'SOL2': 'R3',
      'SPARE': 'R4',
      'R1': 'R1',
      'R2': 'R2',
      'R3': 'R3',
      'R4': 'R4'
    };
    const rTarget = targetMap[target.toUpperCase()] || target;
    const actionStr = state ? 'on' : 'off';

    // 1. Emit over WebSocket to Python backend for single authoritative dispatch
    if (socketRef.current?.connected) {
      socketRef.current.emit('toggle_relay', { target, state });
      addLog(`Relay [${target} / ${rTarget}] command requested: ${state ? 'ON' : 'OFF'}`, 'info');
    } else {
      addLog('Relay command unavailable: backend disconnected', 'error');
    }
  };

  const sendChatMessage = (message: string, callback?: (reply: string) => void, language = 'en', detections: DiseaseItem[] = []) => {
    const socket = socketRef.current;
    if (!socket?.connected) { callback?.('The dashboard service is offline. Reconnect and try again.'); return () => {}; }
    const request_id = String(Date.now()) + Math.random().toString(36).slice(2);
    let timer: ReturnType<typeof setTimeout>;
    const cleanup = () => { clearTimeout(timer); socket.off('chat_reply', receive); };
    const receive = (data: any) => { if (data.request_id !== request_id) return; cleanup(); callback?.(data.message || data.reply || 'No reply was returned. Please try again.'); };
    socket.on('chat_reply', receive);
    timer = setTimeout(() => { cleanup(); callback?.('The AI service did not respond in time. Please try again.'); }, 60000);
    socket.emit('chat_message', { message, language, request_id, crop: selectedCropRef.current, detections: detections.slice(0, 8).map(d => ({ class: d.class, confidence: d.confidence })) });
    return cleanup;
  };

  const toggleMode = (mode: 'auto' | 'manual') => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('toggle_mode', { mode });
    }
  };

  const requestDiseaseDetail = (disease: string, confidence: number, crop: string, callback: (detail: any) => void) => {
    const socket = socketRef.current;
    const request_id = String(Date.now()) + Math.random().toString(36).slice(2);
    const unavailable = { unavailable: true, disease_name_en: disease, fertilizer_list: [], recovery_plan: [], prevention_tips: [] };
    if (!socket?.connected) { callback(unavailable); return () => {}; }
    let timer: ReturnType<typeof setTimeout>;
    const cleanup = () => { clearTimeout(timer); socket.off('disease_detail_response', receive); };
    const receive = (data: any) => {
      if (data.request_id !== request_id) return;
      cleanup(); callback(data);
    };
    socket.on('disease_detail_response', receive);
    timer = setTimeout(() => { cleanup(); callback(unavailable); }, 60000);
    socket.emit('disease_detail_request', { disease, confidence, crop, request_id });
    return cleanup;
  };

  const requestWeatherRefresh = (lat?: number, lon?: number, force: boolean = true) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('weather_refresh_request', { lat, lon, force });
    }
  };

  const requestWeatherAISummary = (crop: string, callback?: (summary: any) => void) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('weather_ai_summary_request', { crop, force: true });
      if (callback) {
        socketRef.current.once('weather_ai_summary_response', (data: any) => {
          callback(data);
        });
      }
    }
  };

  const refreshAll = () => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('weather_refresh_request', { force: true });
      socketRef.current.emit('crop_selected', { crop: selectedCrop });
      addLog('Uplink refreshed: Requested immediate sensor, GPS & weather sync.', 'success');
    } else {
      socketRef.current?.connect();
      addLog('Reconnecting socket uplink...', 'info');
    }
  };

  const sendLaptopLocation = (coords: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('laptop_location_stream', coords);
    }
  };

  const sendFusionMode = (mode: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('set_location_fusion_mode', { mode });
    }
  };

  return {
    emergencyStop: () => socketRef.current?.emit('emergency_stop'),
    resetEmergencyStop: () => socketRef.current?.emit('reset_emergency_stop'),
    socketRef,
    socket: socketRef.current,
    sendLaptopLocation,
    sendFusionMode,
    selectCrop,
    selectModel,
    sendRobotControl,
    sendPumpControl,
    sendSolenoidControl,
    sendRelayToggle,
    sendChatMessage,
    toggleMode,
    requestDiseaseDetail,
    requestWeatherRefresh,
    requestWeatherAISummary,
    refreshAll
  };
}
