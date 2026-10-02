/**
 * @file App.tsx
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

import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import SystemEngagement from './pages/SystemEngagement';
import CropSelection from './pages/CropSelection';
import CommandConsole from './pages/CommandConsole';
import Dashboard from './pages/Dashboard';

export type LogEntry = {
  id: number;
  time: string;
  icon: string;
  msg: string;
  type: 'success' | 'error' | 'warning' | 'info';
};

export type DiseaseItem = {
  class: string;
  confidence: number;
  count: number;
  box?: [number, number, number, number]; // [xmin, ymin, xmax, ymax]
  xmin?: number;
  ymin?: number;
  xmax?: number;
  ymax?: number;
};

export type SensorData = {
  hardware_connected?: boolean;
  source?: string;
  battery?: number;
  soil1Pct?: number;
  soil2Pct?: number;
  motor_left?: number;
  motor_right?: number;
  temperature: number;
  humidity: number;
  pressure: number;
  light: number;
  uvVoltage: number;
  uvIndex?: number;
  soilMoisture: number;
  soilMoisture2?: number;
  ultrasonic?: number;
  ultrasonic_back?: number;
  latitude?: number;
  longitude?: number;
  fused_latitude?: number;
  fused_longitude?: number;
  pos_uncertainty_m?: number;
  fusion_mode?: string;
  baseline?: {
    distance_m: number;
    bearing_deg: number;
    laptop_to_rover_vector: string;
  };
  laptop_gps?: any;
  rover_gps?: any;
  altitude?: number;
  speed?: number;
  heading?: number;
  cardinal?: string;
  satellites?: number;
  hdop?: number;
  fix?: boolean;
  pump_on?: boolean;
  sol1_on?: boolean;
  sol2_on?: boolean;
  spare_on?: boolean;
};

export type Recommendation = {
  disease: string;
  confidence: number;
  reason: string;
  recovery: string;
  prediction: string;
  fertilizer: string;
};

export default function App() {
  const [selectedCrop, setSelectedCrop] = useState('tomato');
  const [mode, setMode] = useState<'auto' | 'manual'>('manual');

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          <Dashboard selectedCrop={selectedCrop} mode={mode} />
        } />
        <Route path="/console" element={
          <Dashboard selectedCrop={selectedCrop} mode={mode} />
        } />
        <Route path="/advanced" element={<CommandConsole selectedCrop={selectedCrop} mode={mode} />} />
        <Route path="/engagement" element={
          <SystemEngagement onModeSelect={setMode} />
        } />
        <Route path="/crop-selection" element={
          <CropSelection selectedCrop={selectedCrop} onCropSelect={setSelectedCrop} />
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
