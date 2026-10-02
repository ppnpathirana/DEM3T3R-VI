export type Language = 'en' | 'si' | 'ta';

export interface Translations {
  // App & Header
  appTitle: string;
  commandDashboard: string;
  sectorAlpha: string;
  connected: string;
  disconnected: string;
  autonomousMode: string;
  manualMode: string;
  cropSelection: string;
  changeCrop: string;
  weatherLive: string;
  weatherAI: string;

  // Sensor Metrics
  airTemperature: string;
  airHumidity: string;
  atmosphericPressure: string;
  lightIntensity: string;
  uvRadiation: string;
  soilMoisture1: string;
  soilMoisture2: string;
  ultrasonicDistance: string;
  gpsCoordinates: string;
  altitude: string;
  speed: string;
  heading: string;
  satellites: string;
  hdop: string;
  fixStatus: string;
  fixLocked: string;
  searchingFix: string;

  // Relay Controls
  manualRelayControls: string;
  waterPumpRelay: string;
  soilProbe1Relay: string;
  soilProbe2Relay: string;
  spareRelay: string;
  relayOn: string;
  relayOff: string;
  zoneAAux: string;
  zoneBAux: string;
  auxiliarySwitch: string;

  // Map & Navigation
  mapTitle: string;
  terrain3D: string;
  topoTerrain: string;
  satelliteMap: string;
  standardMap: string;
  googleHybrid: string;
  googleTerrain: string;
  googleSatellite: string;

  // Waypoint Autonomous Mission & 2-Minute Staging
  waypointMission: string;
  waypointMarkingMode: string;
  markingActive: string;
  startMission: string;
  pauseMission: string;
  resumeMission: string;
  skipWaypoint: string;
  clearWaypoints: string;
  simulateArrival: string;
  stagingCountdownActive: string;
  inspectingCrop: string;
  soilProbesActive: string;
  exportMissionData: string;
  missionReport: string;
  missionProgress: string;
  targetWaypoint: string;
  totalDistance: string;
  waypointMarkingActive: string;
  inspectionReport: string;
  statusInspecting: string;
  soilProbeLowered: string;
  totalWaypoints: string;
  distanceRemaining: string;

  // AI & Pathogen Diagnostics
  pathogenScanner: string;
  detectingDiseases: string;
  healthyCrop: string;
  diseaseDetected: string;
  confidenceRate: string;
  recoveryPlan: string;
  fertilizerDose: string;
  environmentalRisk: string;
  viewDiseaseDetail: string;

  // Hardware Status & Controls
  driveSpeed: string;
  steerTrim: string;
  emergencyStop: string;
  safetyCoverActive: string;
  batteryVoltage: string;
  cpuTemp: string;
  ramUsage: string;
  fpsRate: string;

  // AI Voice & Natural Language
  aiAssistant: string;
  askAssistant: string;
  speakingVoiceOn: string;
  speakingVoiceOff: string;
  digitalTwin: string;
  affordanceControls: string;

  refreshData: string;
  clearLogs: string;
  systemReboot: string;
  selectLanguage: string;
}

const en: Translations = {
  appTitle: 'DEM3T3R V1 — Autonomous Agro-Bot',
  commandDashboard: 'Autonomous Robotic Command & Precision Agronomy Console',
  sectorAlpha: 'Sector Alpha — Active Mission Zone',
  connected: 'ONLINE / LINKED',
  disconnected: 'OFFLINE / DISCONNECTED',
  autonomousMode: 'AUTONOMOUS MISSION',
  manualMode: 'MANUAL RC DRIVE',
  cropSelection: 'Active Monitored Crop',
  changeCrop: 'Change Target Crop',
  weatherLive: 'Live Agro-Meteorology',
  weatherAI: 'AI Agronomic Microclimate Forecast',

  airTemperature: 'Ambient Temperature',
  airHumidity: 'Relative Humidity',
  atmosphericPressure: 'Barometric Pressure',
  lightIntensity: 'Solar Radiation / Lux',
  uvRadiation: 'UV Index / Index Voltage',
  soilMoisture1: 'Soil Moisture (Zone A)',
  soilMoisture2: 'Soil Moisture (Zone B)',
  ultrasonicDistance: 'Ultrasonic Obstacle Proximity',
  gpsCoordinates: 'GPS Coordinates (Lat / Lon)',
  altitude: 'Altitude MSL',
  speed: 'Ground Velocity',
  heading: 'Compass Heading',
  satellites: 'Satellites Locked',
  hdop: 'Horizontal Dilution (HDOP)',
  fixStatus: 'GPS Fix Status',
  fixLocked: '3D RTK / GPS Locked',
  searchingFix: 'Acquiring Satellites...',

  manualRelayControls: 'Precision Actuator & Relay Bus (Numpad 1-4)',
  waterPumpRelay: 'Relay 1: Water / Pesticide Pump (GPIO 10)',
  soilProbe1Relay: 'Relay 2: Zone A Moisture Probe Actuator (GPIO 11)',
  soilProbe2Relay: 'Relay 3: Zone B Moisture Probe Actuator (GPIO 12)',
  spareRelay: 'Relay 4: Auxiliary Swarm Actuator (GPIO 13)',
  relayOn: 'ACTIVE (ON)',
  relayOff: 'STANDBY (OFF)',
  zoneAAux: 'Zone A Aux Solenoid',
  zoneBAux: 'Zone B Aux Solenoid',
  auxiliarySwitch: 'Auxiliary Actuator',

  mapTitle: 'Multi-Spectral Geospatial & Waypoint Mission Planner',
  terrain3D: '3D Topological Surface',
  topoTerrain: 'Topographic Relief Map',
  satelliteMap: 'High-Res Satellite Imagery',
  standardMap: 'OpenStreetMap Standard',
  googleHybrid: 'Google Hybrid Satellite',
  googleTerrain: 'Google Physical Terrain',
  googleSatellite: 'Google Satellite Pure',

  waypointMission: 'Autonomous Waypoint Mission Engine',
  waypointMarkingMode: 'Waypoint Marking Mode',
  markingActive: 'Marking Active — Click on Map',
  startMission: 'Execute Autonomous Mission',
  pauseMission: 'Pause Mission',
  resumeMission: 'Resume Mission',
  skipWaypoint: 'Skip Current Waypoint',
  clearWaypoints: 'Clear All Waypoints',
  simulateArrival: 'Simulate WP Arrival (Test Staging)',
  stagingCountdownActive: '2-Minute Waypoint Staging Active',
  inspectingCrop: 'Inspecting Crop Canopy & Logging Soil Probes...',
  soilProbesActive: 'Relays 2 & 3 ON — Deep Soil & Camera Inspection Active',
  exportMissionData: 'Export Mission Telemetry (CSV)',
  missionReport: 'Agronomic Field Mission Report',
  missionProgress: 'Mission Execution Progress',
  targetWaypoint: 'Navigating to Waypoint',
  totalDistance: 'Total distance',
  waypointMarkingActive: 'Waypoint marking active',
  inspectionReport: 'Inspection report',
  statusInspecting: 'Inspecting',
  soilProbeLowered: 'Soil probe lowered',
  totalWaypoints: 'Total Placed Waypoints',
  distanceRemaining: 'Distance to Next Target',

  pathogenScanner: 'AI Multi-Spectral Foliar Pathogen Scanner',
  detectingDiseases: 'Scanning foliage in real-time...',
  healthyCrop: 'Healthy Canopy — No Pathogens Detected',
  diseaseDetected: 'Pathogen Detected!',
  confidenceRate: 'Classification Confidence',
  recoveryPlan: 'Agronomic Treatment & Recovery Plan',
  fertilizerDose: 'Recommended Fungicide & Nutrient Dosages',
  environmentalRisk: 'Fungal Sporulation Risk Factor',
  viewDiseaseDetail: 'Inspect Disease Recovery Encyclopedia',

  driveSpeed: 'Rover Throttle / Velocity PWM',
  steerTrim: 'Steering Differential Offset',
  emergencyStop: 'EMERGENCY HARDWARE STOP (SPACEBAR)',
  safetyCoverActive: 'Safety Cover Active',
  batteryVoltage: 'LiFePO4 Power Bus Voltage',
  cpuTemp: 'MCU Core Temperature',
  ramUsage: 'Telemetry Heap Usage',
  fpsRate: 'Vision Inference Pipeline FPS',

  aiAssistant: 'DEM3T3R V1 Autonomous Agronomy Advisor',
  askAssistant: 'Ask DEM3T3R V1 about crop pathology, sensor trends, or automation commands...',
  speakingVoiceOn: '🔊 Voice Feedback ON',
  speakingVoiceOff: '🔇 Voice Feedback OFF',
  digitalTwin: 'Robotic Digital Twin & Kinematics',
  affordanceControls: 'Physical AI Affordance Control',

  refreshData: '🔄 Refresh Data',
  clearLogs: 'Clear Logs',
  systemReboot: 'System Reboot',
  selectLanguage: 'Language'
};

export const translations: Record<Language, Translations> = {
  en,
  si: { ...en },
  ta: { ...en }
};

export const spokenMessages: Record<Language, Record<string, string>> = {
  en: {
    welcome: 'DEM3T3R V1 Autonomous Agro-Bot online and operational.',
    connected: 'Telemetry and hardware control linked.',
    disconnected: 'Telemetry connection lost.',
    autoModeOn: 'Autonomous navigation mission activated.',
    manualModeOn: 'Manual joystick control enabled.',
    obstacleDetected: 'Warning! Obstacle detected in forward path.',
    sprayStarted: 'Precision spot-spraying initiated.',
    sprayStopped: 'Spraying completed.',
    stagingStarted: 'Arrived at waypoint. Staging sensors active.',
    stagingFinished: 'Staging completed. Resuming route.',
    safeStop: 'Emergency safety stop engaged.'
  },
  si: {
    welcome: 'DEM3T3R V1 Autonomous Agro-Bot online and operational.',
    connected: 'Telemetry and hardware control linked.',
    disconnected: 'Telemetry connection lost.',
    autoModeOn: 'Autonomous navigation mission activated.',
    manualModeOn: 'Manual joystick control enabled.',
    obstacleDetected: 'Warning! Obstacle detected in forward path.',
    sprayStarted: 'Precision spot-spraying initiated.',
    sprayStopped: 'Spraying completed.',
    stagingStarted: 'Arrived at waypoint. Staging sensors active.',
    stagingFinished: 'Staging completed. Resuming route.',
    safeStop: 'Emergency safety stop engaged.'
  },
  ta: {
    welcome: 'DEM3T3R V1 Autonomous Agro-Bot online and operational.',
    connected: 'Telemetry and hardware control linked.',
    disconnected: 'Telemetry connection lost.',
    autoModeOn: 'Autonomous navigation mission activated.',
    manualModeOn: 'Manual joystick control enabled.',
    obstacleDetected: 'Warning! Obstacle detected in forward path.',
    sprayStarted: 'Precision spot-spraying initiated.',
    sprayStopped: 'Spraying completed.',
    stagingStarted: 'Arrived at waypoint. Staging sensors active.',
    stagingFinished: 'Staging completed. Resuming route.',
    safeStop: 'Emergency safety stop engaged.'
  }
};
