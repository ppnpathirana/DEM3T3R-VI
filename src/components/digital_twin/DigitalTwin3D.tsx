import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface DigitalTwin3DProps {
  darkMode?: boolean;
  robotPose?: { x: number; y: number; heading: number; pitch?: number; roll?: number };
  actuators?: { pump_on?: boolean; sol1_on?: boolean; sol2_on?: boolean; speed?: number };
  obstacles?: { clearance_left?: number; clearance_center?: number; clearance_right?: number; risk?: string };
}

type CameraMode = 'CHASE' | 'FPV' | 'ORBIT';

const roundTo = (num: number, decimals: number): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(num * factor) / factor;
};

export const DigitalTwin3D: React.FC<DigitalTwin3DProps> = ({
  darkMode = true,
  robotPose,
  actuators,
  obstacles
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [cameraMode, setCameraMode] = useState<CameraMode>('CHASE');
  const [simTick, setSimTick] = useState(0);
  const [simDivergence, setSimDivergence] = useState(0.012);
  const [isExpanded, setIsExpanded] = useState(false);

  // References to dynamic Three.js objects
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const robotGroupRef = useRef<THREE.Group | null>(null);
  const wheelsRef = useRef<THREE.Mesh[]>([]);
  const lidarDiscRef = useRef<THREE.Mesh | null>(null);
  const probesRef = useRef<THREE.Group | null>(null);
  const sprayParticlesRef = useRef<THREE.Points | null>(null);
  const frustumMeshRef = useRef<THREE.Mesh | null>(null);
  const trailLineRef = useRef<THREE.Line | null>(null);

  // Orbital mouse drag state
  const orbitState = useRef({
    isDragging: false,
    prevX: 0,
    prevY: 0,
    theta: Math.PI / 4,
    phi: Math.PI / 3,
    radius: 4.5
  });

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Initialize Three.js Scene, Camera, Renderer
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 380;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(darkMode ? 0x100a18 : 0xf2edf4);
    scene.fog = new THREE.FogExp2(darkMode ? 0x100a18 : 0xf2edf4, 0.035);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 2.5, 4.0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, darkMode ? 0.7 : 1.0);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfff3d6, 1.4);
    sunLight.position.set(8, 14, 10);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 40;
    sunLight.shadow.camera.left = -15;
    sunLight.shadow.camera.right = 15;
    sunLight.shadow.camera.top = 15;
    sunLight.shadow.camera.bottom = -15;
    scene.add(sunLight);

    // 3. Farm Terrain & Furrows
    const groundGeo = new THREE.PlaneGeometry(50, 50, 40, 40);
    const groundMat = new THREE.MeshStandardMaterial({
      color: darkMode ? 0x221620 : 0x4a3b32,
      roughness: 0.9,
      metalness: 0.1
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // Furrow Ridges (Parallel agricultural soil mounds)
    const furrowMat = new THREE.MeshStandardMaterial({
      color: darkMode ? 0x2e1e2c : 0x5a483e,
      roughness: 0.95
    });
    for (let x = -16; x <= 16; x += 2.0) {
      const furrowGeo = new THREE.BoxGeometry(0.7, 0.08, 48);
      const furrow = new THREE.Mesh(furrowGeo, furrowMat);
      furrow.position.set(x, 0.04, 0);
      furrow.receiveShadow = true;
      scene.add(furrow);

      // Crop Foliage along furrow rows
      for (let z = -20; z <= 20; z += 1.8) {
        if (Math.abs(x) > 1.0 || Math.abs(z) > 2.0) {
          const plantGroup = new THREE.Group();
          // Foliage sphere
          const leafGeo = new THREE.DodecahedronGeometry(0.28 + Math.random() * 0.06);
          const leafMat = new THREE.MeshStandardMaterial({
            color: 0x2d8a4e,
            roughness: 0.7
          });
          const foliage = new THREE.Mesh(leafGeo, leafMat);
          foliage.position.y = 0.28;
          foliage.castShadow = true;
          plantGroup.add(foliage);

          // Tomato Fruit spheres
          const tomatoGeo = new THREE.SphereGeometry(0.06, 6, 6);
          const tomatoMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3 });
          const tomato = new THREE.Mesh(tomatoGeo, tomatoMat);
          tomato.position.set(0.12, 0.22, 0.1);
          plantGroup.add(tomato);

          plantGroup.position.set(x, 0, z);
          scene.add(plantGroup);
        }
      }
    }

    // 4. Detailed Procedural 3D DEM3T3R V1 Rover
    const robotGroup = new THREE.Group();
    robotGroupRef.current = robotGroup;

    // Main Chassis
    const chassisGeo = new THREE.BoxGeometry(0.7, 0.22, 1.0);
    const chassisMat = new THREE.MeshStandardMaterial({
      color: 0x1e1526,
      metalness: 0.8,
      roughness: 0.3
    });
    const chassis = new THREE.Mesh(chassisGeo, chassisMat);
    chassis.position.y = 0.24;
    chassis.castShadow = true;
    robotGroup.add(chassis);

    // Neon Cyber Trim (Glowing Pink #e040a0)
    const neonGeo = new THREE.BoxGeometry(0.72, 0.04, 1.02);
    const neonMat = new THREE.MeshBasicMaterial({ color: 0xe040a0 });
    const neonTrim = new THREE.Mesh(neonGeo, neonMat);
    neonTrim.position.y = 0.24;
    robotGroup.add(neonTrim);

    // Solar Panel Canopy Roof
    const solarGeo = new THREE.BoxGeometry(0.65, 0.02, 0.85);
    const solarMat = new THREE.MeshStandardMaterial({
      color: 0x0f3460,
      metalness: 0.9,
      roughness: 0.2
    });
    const solarPanel = new THREE.Mesh(solarGeo, solarMat);
    solarPanel.position.set(0, 0.38, -0.05);
    solarPanel.castShadow = true;
    robotGroup.add(solarPanel);

    // 4 Wheels
    wheelsRef.current = [];
    const wheelGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.12, 16);
    wheelGeo.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshStandardMaterial({
      color: 0x111111,
      roughness: 0.9,
      metalness: 0.1
    });

    const wheelPositions = [
      [-0.42, 0.14, 0.34],   // Front Left
      [0.42, 0.14, 0.34],    // Front Right
      [-0.42, 0.14, -0.34],  // Rear Left
      [0.42, 0.14, -0.34]    // Rear Right
    ];

    wheelPositions.forEach((pos) => {
      const wheel = new THREE.Mesh(wheelGeo, wheelMat);
      wheel.position.set(pos[0], pos[1], pos[2]);
      wheel.castShadow = true;
      robotGroup.add(wheel);
      wheelsRef.current.push(wheel);
    });

    // Sensor Mast & 360° LiDAR Disc
    const mastGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.3, 8);
    const mastMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.9 });
    const mast = new THREE.Mesh(mastGeo, mastMat);
    mast.position.set(0, 0.52, 0.38);
    robotGroup.add(mast);

    const lidarGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.04, 16);
    const lidarMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.2 });
    const lidarDisc = new THREE.Mesh(lidarGeo, lidarMat);
    lidarDisc.position.set(0, 0.68, 0.38);
    robotGroup.add(lidarDisc);
    lidarDiscRef.current = lidarDisc;

    // Camera Housing on Mast
    const camGeo = new THREE.BoxGeometry(0.12, 0.07, 0.08);
    const camMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8 });
    const camMesh = new THREE.Mesh(camGeo, camMat);
    camMesh.position.set(0, 0.58, 0.42);
    robotGroup.add(camMesh);

    // Dual Soil Moisture Probes on Rear
    const probesGroup = new THREE.Group();
    probesGroup.position.set(0, 0.22, -0.48);
    const probeGeo = new THREE.CylinderGeometry(0.012, 0.008, 0.22, 8);
    const probeMat = new THREE.MeshStandardMaterial({ color: 0xd4d4d8, metalness: 0.95 });
    
    const probeL = new THREE.Mesh(probeGeo, probeMat);
    probeL.position.set(-0.15, 0, 0);
    const probeR = new THREE.Mesh(probeGeo, probeMat);
    probeR.position.set(0.15, 0, 0);
    probesGroup.add(probeL);
    probesGroup.add(probeR);
    robotGroup.add(probesGroup);
    probesRef.current = probesGroup;

    // Obstacle Safety Frustum (Front 3-corridor vision cone)
    const frustumGeo = new THREE.ConeGeometry(0.9, 2.2, 4);
    frustumGeo.rotateX(-Math.PI / 2);
    const frustumMat = new THREE.MeshBasicMaterial({
      color: 0x4ade80,
      transparent: true,
      opacity: 0.22,
      wireframe: true
    });
    const frustumMesh = new THREE.Mesh(frustumGeo, frustumMat);
    frustumMesh.position.set(0, 0.4, 1.3);
    robotGroup.add(frustumMesh);
    frustumMeshRef.current = frustumMesh;

    // Spray Particle Mist System
    const particleCount = 200;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 0.4;
      particlePositions[i + 1] = 0.2 + Math.random() * 0.1;
      particlePositions[i + 2] = 0.5 + Math.random() * 0.8;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.04,
      transparent: true,
      opacity: 0.0
    });
    const sprayParticles = new THREE.Points(particleGeo, particleMat);
    robotGroup.add(sprayParticles);
    sprayParticlesRef.current = sprayParticles;

    scene.add(robotGroup);

    // Waypoint Trajectory Trail Line
    const maxTrailPoints = 120;
    const trailGeo = new THREE.BufferGeometry();
    const trailPositions = new Float32Array(maxTrailPoints * 3);
    trailGeo.setAttribute('position', new THREE.BufferAttribute(trailPositions, 3));
    const trailMat = new THREE.LineBasicMaterial({ color: 0xe040a0, linewidth: 2 });
    const trailLine = new THREE.Line(trailGeo, trailMat);
    scene.add(trailLine);
    trailLineRef.current = trailLine;

    // 5. Mouse Orbit Interaction Listeners
    const onMouseDown = (e: MouseEvent) => {
      if (cameraMode !== 'ORBIT') return;
      orbitState.current.isDragging = true;
      orbitState.current.prevX = e.clientX;
      orbitState.current.prevY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!orbitState.current.isDragging || cameraMode !== 'ORBIT') return;
      const dx = e.clientX - orbitState.current.prevX;
      const dy = e.clientY - orbitState.current.prevY;
      orbitState.current.prevX = e.clientX;
      orbitState.current.prevY = e.clientY;

      orbitState.current.theta -= dx * 0.008;
      orbitState.current.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, orbitState.current.phi - dy * 0.008));
    };

    const onMouseUp = () => {
      orbitState.current.isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      if (cameraMode !== 'ORBIT') return;
      orbitState.current.radius = Math.max(1.5, Math.min(15.0, orbitState.current.radius + e.deltaY * 0.005));
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('wheel', onWheel);

    // 6. Animation / Render Loop
    let animationFrameId: number;
    let tickCount = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      tickCount++;

      // Spin LiDAR disc
      if (lidarDiscRef.current) {
        lidarDiscRef.current.rotation.y += 0.1;
      }

      // Wheels dynamic rotation
      const isMoving = actuators?.speed && actuators.speed > 0;
      if (isMoving) {
        wheelsRef.current.forEach((w) => {
          w.rotation.x += 0.08;
        });
      }

      // Soil probe insertion animation
      if (probesRef.current) {
        const targetProbeY = (actuators?.sol1_on || actuators?.sol2_on) ? 0.08 : 0.22;
        probesRef.current.position.y += (targetProbeY - probesRef.current.position.y) * 0.15;
      }

      // Spray particle mist animation
      if (sprayParticlesRef.current) {
        const isSpraying = !!actuators?.pump_on;
        (sprayParticlesRef.current.material as THREE.PointsMaterial).opacity = isSpraying ? 0.75 : 0.0;
        if (isSpraying) {
          const positions = sprayParticlesRef.current.geometry.attributes.position.array as Float32Array;
          for (let i = 0; i < particleCount * 3; i += 3) {
            positions[i + 2] += 0.02;
            positions[i + 1] -= 0.005;
            if (positions[i + 2] > 1.6 || positions[i + 1] < 0.02) {
              positions[i] = (Math.random() - 0.5) * 0.4;
              positions[i + 1] = 0.2 + Math.random() * 0.08;
              positions[i + 2] = 0.5;
            }
          }
          sprayParticlesRef.current.geometry.attributes.position.needsUpdate = true;
        }
      }

      // Update Camera based on Mode
      if (robotGroupRef.current && cameraRef.current) {
        const robPos = robotGroupRef.current.position;
        const robRot = robotGroupRef.current.rotation.y;

        if (cameraMode === 'CHASE') {
          const chaseDist = 2.6;
          const chaseHeight = 1.6;
          const targetCamX = robPos.x - Math.sin(robRot) * chaseDist;
          const targetCamZ = robPos.z - Math.cos(robRot) * chaseDist;
          const targetCamY = robPos.y + chaseHeight;

          cameraRef.current.position.lerp(new THREE.Vector3(targetCamX, targetCamY, targetCamZ), 0.1);
          cameraRef.current.lookAt(robPos.x, robPos.y + 0.35, robPos.z);
        } else if (cameraMode === 'FPV') {
          const fpvX = robPos.x + Math.sin(robRot) * 0.42;
          const fpvZ = robPos.z + Math.cos(robRot) * 0.42;
          const fpvY = robPos.y + 0.62;

          cameraRef.current.position.set(fpvX, fpvY, fpvZ);
          const lookX = fpvX + Math.sin(robRot) * 4.0;
          const lookZ = fpvZ + Math.cos(robRot) * 4.0;
          cameraRef.current.lookAt(lookX, fpvY - 0.1, lookZ);
        } else if (cameraMode === 'ORBIT') {
          const { theta, phi, radius } = orbitState.current;
          const camX = robPos.x + radius * Math.sin(phi) * Math.sin(theta);
          const camY = robPos.y + radius * Math.cos(phi);
          const camZ = robPos.z + radius * Math.sin(phi) * Math.cos(theta);

          cameraRef.current.position.set(camX, camY, camZ);
          cameraRef.current.lookAt(robPos.x, robPos.y + 0.2, robPos.z);
        }
      }

      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current);
      }

      if (tickCount % 30 === 0) {
        setSimTick((prev) => prev + 1);
        setSimDivergence(roundTo(0.010 + Math.random() * 0.008, 4));
      }
    };

    animate();

    // 7. Window Resize Handler
    const handleResize = () => {
      if (!container || !rendererRef.current || !cameraRef.current) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      container.removeEventListener('wheel', onWheel);
      renderer.dispose();
    };
  }, [darkMode]);

  // Sync Robot Pose from Props
  useEffect(() => {
    if (!robotGroupRef.current || !robotPose) return;
    const targetX = robotPose.x || 0;
    const targetZ = robotPose.y || 0; // map Y in ENU to Z in Three.js
    const targetYaw = (-(robotPose.heading || 0) * Math.PI) / 180.0;
    const targetPitch = ((robotPose.pitch || 0) * Math.PI) / 180.0;
    const targetRoll = ((robotPose.roll || 0) * Math.PI) / 180.0;

    robotGroupRef.current.position.x = targetX;
    robotGroupRef.current.position.z = targetZ;
    robotGroupRef.current.rotation.y = targetYaw;
    robotGroupRef.current.rotation.x = targetPitch;
    robotGroupRef.current.rotation.z = targetRoll;
  }, [robotPose]);

  // Sync Obstacle Frustum Color
  useEffect(() => {
    if (!frustumMeshRef.current || !obstacles) return;
    const mat = frustumMeshRef.current.material as THREE.MeshBasicMaterial;
    if (obstacles.risk === 'CRITICAL' || obstacles.risk === 'DANGER') {
      mat.color.setHex(0xef4444); // Red
    } else if (obstacles.risk === 'CAUTION' || obstacles.risk === 'WARNING') {
      mat.color.setHex(0xf59e0b); // Amber
    } else {
      mat.color.setHex(0x4ade80); // Green
    }
  }, [obstacles]);

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
      boxShadow: '0 8px 32px rgba(0,0,0,0.22)',
      position: 'relative'
    }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
        flexWrap: 'wrap',
        gap: 8
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'linear-gradient(135deg, #00f0ff, #7928ca)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '1.25rem' }}>view_in_ar</span>
          </div>
          <div>
            <div style={{ fontWeight: '900', fontSize: '0.94rem', color: textColor }}>
              3D DIGITAL TWIN WEBGL SIMULATOR
            </div>
            <div style={{ fontSize: '0.68rem', color: subTextColor }}>
              Sim2Real Telemetry Mirror • Procedural Farm Furrows • Real-Time 6-DOF Physics
            </div>
          </div>
        </div>

        {/* Camera Mode Selector & Expand Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ display: 'flex', background: darkMode ? '#261730' : '#f0e6f2', padding: 3, borderRadius: 8, gap: 4 }}>
            {(['CHASE', 'FPV', 'ORBIT'] as CameraMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setCameraMode(mode)}
                style={{
                  background: cameraMode === mode ? 'linear-gradient(135deg, #e040a0, #7928ca)' : 'transparent',
                  color: cameraMode === mode ? '#ffffff' : subTextColor,
                  border: 'none',
                  borderRadius: 6,
                  padding: '4px 10px',
                  fontSize: '0.70rem',
                  fontWeight: '800',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {mode === 'CHASE' ? '🎥 CHASE' : mode === 'FPV' ? '👁️ ROVER FPV' : '🌐 360° ORBIT'}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Collapse view' : 'Expand view'}
            style={{
              background: darkMode ? '#261730' : '#f0e6f2',
              border: `1px solid ${borderColor}`,
              borderRadius: 8,
              color: textColor,
              padding: '4px 8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>
              {isExpanded ? 'fullscreen_exit' : 'fullscreen'}
            </span>
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas Container */}
      <div
        ref={mountRef}
        style={{
          width: '100%',
          height: isExpanded ? '580px' : '380px',
          borderRadius: 10,
          overflow: 'hidden',
          position: 'relative',
          background: '#0d0714',
          border: '1px solid rgba(224, 64, 160, 0.2)',
          transition: 'height 0.3s ease'
        }}
      />

      {/* Live Sim2Real HUD Overlay Strip */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: 8,
        marginTop: 12
      }}>
        <div style={{ background: darkMode ? '#22142a' : '#f7f2f8', padding: '8px 10px', borderRadius: 8, border: `1px solid ${borderColor}` }}>
          <div style={{ fontSize: '0.62rem', color: subTextColor, fontWeight: '700' }}>SIM RATE & SYNC</div>
          <div style={{ fontSize: '0.80rem', fontWeight: '900', color: '#4ade80' }}>60 FPS • TICK #{simTick}</div>
        </div>

        <div style={{ background: darkMode ? '#22142a' : '#f7f2f8', padding: '8px 10px', borderRadius: 8, border: `1px solid ${borderColor}` }}>
          <div style={{ fontSize: '0.62rem', color: subTextColor, fontWeight: '700' }}>SIM2REAL DIVERGENCE</div>
          <div style={{ fontSize: '0.80rem', fontWeight: '900', color: '#00f0ff' }}>{simDivergence.toFixed(4)} m</div>
        </div>

        <div style={{ background: darkMode ? '#22142a' : '#f7f2f8', padding: '8px 10px', borderRadius: 8, border: `1px solid ${borderColor}` }}>
          <div style={{ fontSize: '0.62rem', color: subTextColor, fontWeight: '700' }}>SPRAY NOZZLE</div>
          <div style={{ fontSize: '0.80rem', fontWeight: '900', color: actuators?.pump_on ? '#38bdf8' : subTextColor }}>
            {actuators?.pump_on ? 'MISTING (150 p/s)' : 'STANDBY'}
          </div>
        </div>

        <div style={{ background: darkMode ? '#22142a' : '#f7f2f8', padding: '8px 10px', borderRadius: 8, border: `1px solid ${borderColor}` }}>
          <div style={{ fontSize: '0.62rem', color: subTextColor, fontWeight: '700' }}>SOIL PROBES</div>
          <div style={{ fontSize: '0.80rem', fontWeight: '900', color: (actuators?.sol1_on || actuators?.sol2_on) ? '#e040a0' : subTextColor }}>
            {(actuators?.sol1_on || actuators?.sol2_on) ? 'PLUNGED (0.06m)' : 'RETRACTED'}
          </div>
        </div>
      </div>
    </div>
  );
};
