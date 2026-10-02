/**
 * @file CropSelection.tsx
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

﻿import { useNavigate } from 'react-router-dom';

type CropSelectionProps = {
  selectedCrop: string;
  onCropSelect: (crop: string) => void;
};

const crops = [
  { name: 'Anthurium',   icon: 'local_florist' },
  { name: 'Brinjal',     icon: 'egg' },
  { name: 'Cabbage',     icon: 'grass' },
  { name: 'Capsicum',    icon: 'grocery' },
  { name: 'Carrot',      icon: 'nutrition' },
  { name: 'Cauliflower', icon: 'filter_vintage' },
  { name: 'Chilli',      icon: 'local_fire_department' },
  { name: 'Corn',        icon: 'grain' },
  { name: 'Lettuce',     icon: 'yard' },
  { name: 'Mushroom',    icon: 'forest' },
  { name: 'Potato',      icon: 'egg_alt' },
  { name: 'Radish',      icon: 'scatter_plot' },
  { name: 'Rice',        icon: 'rice_bowl' },
  { name: 'Rose',        icon: 'emoji_nature' },
  { name: 'Tea',         icon: 'local_cafe' },
  { name: 'Tomato',      icon: 'brightness_1' },
];

export default function CropSelection({ selectedCrop, onCropSelect }: CropSelectionProps) {
  const navigate = useNavigate();

  const handleCropClick = (cropName: string) => {
    onCropSelect(cropName.toLowerCase());
    navigate('/console');
  };

  return (
    <div style={{
      minHeight: '100vh',
      fontFamily: "'DM Sans', sans-serif",
      position: 'relative',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        backgroundImage: `url('https://lh3.googleusercontent.com/aida-public/AB6AXuAZAlIteZVsciAPaKD7zqxXSocZFymfZHq4jJzvXtBiOB8AVqI8OlOGHpWDnkG64dqDBTZh30-4C857tq-ppNXMcSDl_1Ckvgcj32gmSOVRGOp4QqDDqrj4Vk-IKE_eloPCA1xjRAxU-ZslF0b_Km1HnJJKNpYvyq3myLXG4EoQC8GekhBoEJVOpUEF-JFzacGz9nG5kxz-BdluuPTdKkBSoUZS3jCur9PF6o25BlOw9WqtWdDkeoogRa7yiXS5e2oK-cI')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }} />
      <div style={{
        position: 'fixed', inset: 0, zIndex: 1,
        background: 'rgba(254,247,255,0.78)',
        backdropFilter: 'blur(2px)',
      }} />
      <div style={{
        position: 'fixed', inset: 0, zIndex: 2,
        backgroundImage: 'radial-gradient(circle at 20% 20%, rgba(255,214,238,0.7) 0%, transparent 40%), radial-gradient(circle at 80% 80%, rgba(238,220,255,0.7) 0%, transparent 40%)',
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <header style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0.85rem 1.5rem',
        background: 'rgba(254,247,255,0.92)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(220,200,224,0.4)',
        boxShadow: '0 4px 20px rgba(224,64,160,0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="material-symbols-outlined" style={{ color: '#e040a0', fontSize: '1.5rem', fontVariationSettings: "'FILL' 1" }}>grass</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '900', color: '#e040a0', letterSpacing: '-0.02em' }}>DEMET3R</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {['#e040a0','#0096cc','#7c52aa'].map((c, i) => (
            <div key={i} style={{
              width: 10, height: 10, borderRadius: '50%', background: c,
              boxShadow: `0 0 8px ${c}99`,
              animation: `demet3r-pulse 1.5s ease-in-out ${i * 0.2}s infinite`,
            }} />
          ))}
        </div>
        <button
          onClick={() => navigate('/')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'rgba(224,64,160,0.08)', border: 'none',
            borderRadius: 9999, padding: '7px 16px', cursor: 'pointer',
            color: '#e040a0', fontWeight: '700', fontSize: '0.8rem',
            fontFamily: "'DM Sans', sans-serif",
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '1rem' }}>arrow_back</span>
          Back
        </button>
      </header>

      {/* Radial Wheel */}
      <main style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        paddingTop: '5rem', paddingBottom: '2rem',
        position: 'relative', zIndex: 10,
        minHeight: '100vh',
      }}>
        <h2 style={{
          fontSize: '1rem', fontWeight: '700', color: '#7c52aa',
          letterSpacing: '0.2em', textTransform: 'uppercase',
          marginBottom: '1.5rem',
        }}>Choose Your Crop</h2>

        <div style={{
          position: 'relative',
          width: 'min(82vw, 600px)',
          height: 'min(82vw, 600px)',
        }}>
          {/* Decorative rings */}
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            border: '1px dashed rgba(224,64,160,0.15)',
          }} />
          <div style={{
            position: 'absolute', inset: '10%', borderRadius: '50%',
            border: '1px dashed rgba(124,82,170,0.1)',
          }} />

          {/* Center Hub */}
          <div style={{
            position: 'absolute',
            top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 148, height: 148,
            borderRadius: '50%',
            background: 'rgba(254,247,255,0.92)',
            backdropFilter: 'blur(16px)',
            border: '2px solid rgba(240,160,204,0.6)',
            boxShadow: '0 8px 40px rgba(224,64,160,0.18), inset 0 0 24px rgba(255,255,255,0.9)',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            zIndex: 20, cursor: 'default',
          }}>
            <span className="material-symbols-outlined" style={{
              fontSize: '2.8rem', color: '#e040a0', marginBottom: 4,
              fontVariationSettings: "'FILL' 1",
            }}>eco</span>
            <span style={{ fontWeight: '800', fontSize: '0.8rem', letterSpacing: '0.12em', color: '#2e1a28', textAlign: 'center', lineHeight: 1.3 }}>
              SELECT<br />CROP
            </span>
            {selectedCrop && (
              <div style={{
                marginTop: 6, fontSize: '0.6rem', fontWeight: '700',
                background: '#e040a0', color: '#fff',
                padding: '2px 10px', borderRadius: 9999,
                textTransform: 'uppercase', letterSpacing: '0.06em',
              }}>
                {selectedCrop}
              </div>
            )}
          </div>

          {/* Crop Items */}
          {crops.map((crop, idx) => {
            const angle = (idx / 16) * 360;
            const rad = angle * (Math.PI / 180);
            const r = 'min(34vw, 248px)';
            // Use CSS custom property approach
            const isActive = selectedCrop === crop.name.toLowerCase();
            return (
              <div
                key={crop.name}
                onClick={() => handleCropClick(crop.name)}
                style={{
                  position: 'absolute',
                  top: '50%', left: '50%',
                  width: 74, height: 74,
                  marginTop: -37, marginLeft: -37,
                  transform: `rotate(${angle}deg) translate(min(34vw,248px)) rotate(-${angle}deg)`,
                  cursor: 'pointer',
                  zIndex: isActive ? 15 : 10,
                  transition: 'transform 0.3s cubic-bezier(0.34,1.56,0.64,1)',
                }}
              >
                <div style={{
                  width: '100%', height: '100%',
                  background: isActive ? '#ffd6ee' : '#ffffff',
                  borderRadius: '50%',
                  border: isActive ? '2.5px solid #e040a0' : '2px solid #dcc8e0',
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  boxShadow: isActive
                    ? '0 0 0 4px rgba(224,64,160,0.2), 0 8px 24px rgba(224,64,160,0.2)'
                    : '0 4px 16px rgba(124,82,170,0.08)',
                  transition: 'all 0.25s ease',
                }}>
                  <span className="material-symbols-outlined" style={{
                    fontSize: '1.4rem',
                    color: isActive ? '#e040a0' : '#7c52aa',
                    fontVariationSettings: "'FILL' 1",
                  }}>{crop.icon}</span>
                  <span style={{
                    fontSize: '0.55rem', fontWeight: '700',
                    color: isActive ? '#a02070' : '#604868',
                    marginTop: 2, textAlign: 'center', lineHeight: 1.2,
                  }}>{crop.name}</span>
                </div>
              </div>
            );
          })}
        </div>

        <p style={{ color: '#907898', fontSize: '0.8rem', marginTop: '1.5rem', fontWeight: '600' }}>
          Click a crop to open the Command Console
        </p>
      </main>
    </div>
  );
}
