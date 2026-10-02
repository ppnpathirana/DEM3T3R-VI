import { useNavigate } from 'react-router-dom';

type SystemEngagementProps = {
  onModeSelect: (mode: 'auto' | 'manual') => void;
};

export default function SystemEngagement({ onModeSelect }: SystemEngagementProps) {
  const navigate = useNavigate();

  const handleSelect = (mode: 'auto' | 'manual') => {
    onModeSelect(mode);
    navigate('/crop-selection');
  };

  return (
    <div style={{
      minHeight: '100vh',
      fontFamily: "'DM Sans', sans-serif",
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      background: '#fef7ff',
    }}>
      {/* Background image with overlay */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0,
        backgroundImage: `url('https://lh3.googleusercontent.com/aida-public/AB6AXuDMGcCj9yd1mM5fJRN20TbbggCGgxiTmoB4FJOSqWs8I-yGMs9JO6UpQjvjrfoZXqrUgbhLB65umRTszz3PMw7bAwd-KowrAJFYqTKj3cS9mRTgygokwF3F0Peu5zrv-yoIgV9aw_wYk9jcDlr5fGzKCj56TkGfwRe2cn9hEwKtdRepAlIFydm0XP7SJ-U8Ghh8D-nJ4ieUWcog5ySbjHlbdlwdviRlpIpMi1TiKdi1h6nQvuKLTFbxfHUzjhRSHSc6IH0')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
      }} />
      <div style={{
        position: 'fixed', inset: 0, zIndex: 1,
        background: 'rgba(254,247,255,0.82)',
        backdropFilter: 'blur(4px)',
      }} />
      <div style={{
        position: 'fixed', inset: 0, zIndex: 2,
        backgroundImage: 'radial-gradient(circle at top right, rgba(255,214,238,0.6) 0%, transparent 45%), radial-gradient(circle at bottom left, rgba(238,220,255,0.6) 0%, transparent 45%)',
        pointerEvents: 'none',
      }} />

      {/* Main Content */}
      <main style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '3rem 2rem', position: 'relative', zIndex: 10,
        minHeight: '100vh',
      }}>
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '0.5rem' }}>
          <span className="material-symbols-outlined" style={{
            fontSize: '3rem', color: '#e040a0',
            fontVariationSettings: "'FILL' 1",
          }}>grass</span>
        </div>

        <header style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
          <h1 style={{
            fontSize: 'clamp(2.5rem, 7vw, 5rem)',
            fontWeight: '900',
            color: '#e040a0',
            letterSpacing: '-0.02em',
            lineHeight: 1.1,
            marginBottom: '1rem',
          }}>
            SYSTEM ENGAGEMENT
          </h1>
          <p style={{
            fontSize: '0.95rem',
            fontWeight: '700',
            color: '#7c52aa',
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
          }}>
            Select Operational Mode for DEMET3R Swarm
          </p>
        </header>

        {/* Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem',
          width: '100%',
          maxWidth: '860px',
        }}>
          {/* AUTO MODE */}
          <button
            onClick={() => handleSelect('auto')}
            style={{
              background: '#ffffff',
              border: '2px solid transparent',
              borderRadius: '3rem',
              padding: '3rem 2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s cubic-bezier(0.175,0.885,0.32,1.275)',
              boxShadow: '0 10px 40px rgba(224,64,160,0.1)',
              fontFamily: "'DM Sans', sans-serif",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-8px)';
              e.currentTarget.style.borderColor = '#f080c0';
              e.currentTarget.style.boxShadow = '0 24px 60px rgba(224,64,160,0.2)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.boxShadow = '0 10px 40px rgba(224,64,160,0.1)';
            }}
          >
            <div style={{
              width: 96, height: 96, borderRadius: '50%',
              background: 'rgba(224,64,160,0.1)', color: '#e040a0',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: '1.5rem', transition: 'all 0.3s ease',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '3.5rem', fontVariationSettings: "'FILL' 1" }}>hub</span>
            </div>
            <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#e040a0', marginBottom: '0.75rem' }}>AUTO MODE</h2>
            <div style={{
              background: '#e040a0', color: '#fff',
              padding: '5px 20px', borderRadius: '9999px',
              fontSize: '0.7rem', fontWeight: '700',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              marginBottom: '1.25rem',
            }}>AI FULL CONTROL</div>
            <p style={{ color: '#604868', fontSize: '0.95rem', lineHeight: '1.65', maxWidth: '240px' }}>
              Engage autonomous neural network operations. Drones execute predictive pathing,
              automated pest analysis, and precision application protocols.
            </p>
            <div style={{
              marginTop: '2rem', width: '100%',
              display: 'flex', justifyContent: 'space-between',
              fontSize: '0.72rem', fontWeight: '700', color: '#907898',
              borderTop: '2px solid #ece2ec', paddingTop: '1rem',
            }}>
              <span>SYS: NOMINAL</span><span>AI: ACTIVE</span>
            </div>
          </button>

          {/* MANUAL MODE */}
          <button
            onClick={() => handleSelect('manual')}
            style={{
              background: '#ffffff',
              border: '2px solid transparent',
              borderRadius: '3rem',
              padding: '3rem 2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s cubic-bezier(0.175,0.885,0.32,1.275)',
              boxShadow: '0 10px 40px rgba(0,150,204,0.08)',
              fontFamily: "'DM Sans', sans-serif",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-8px)';
              e.currentTarget.style.borderColor = '#40c0ee';
              e.currentTarget.style.boxShadow = '0 24px 60px rgba(0,150,204,0.18)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.boxShadow = '0 10px 40px rgba(0,150,204,0.08)';
            }}
          >
            <div style={{
              width: 96, height: 96, borderRadius: '50%',
              background: 'rgba(0,150,204,0.1)', color: '#0096cc',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: '1.5rem',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '3.5rem', fontVariationSettings: "'FILL' 1" }}>joystick</span>
            </div>
            <h2 style={{ fontSize: '2rem', fontWeight: '800', color: '#0096cc', marginBottom: '0.75rem' }}>MANUAL MODE</h2>
            <div style={{
              background: '#0096cc', color: '#fff',
              padding: '5px 20px', borderRadius: '9999px',
              fontSize: '0.7rem', fontWeight: '700',
              letterSpacing: '0.1em', textTransform: 'uppercase',
              marginBottom: '1.25rem',
            }}>FARMER DIRECT CONTROL</div>
            <p style={{ color: '#604868', fontSize: '0.95rem', lineHeight: '1.65', maxWidth: '240px' }}>
              Take direct remote control of individual or cluster drones. Enable manual navigation
              telemetry and triggered micro-spraying operations.
            </p>
            <div style={{
              marginTop: '2rem', width: '100%',
              display: 'flex', justifyContent: 'space-between',
              fontSize: '0.72rem', fontWeight: '700', color: '#907898',
              borderTop: '2px solid #ece2ec', paddingTop: '1rem',
            }}>
              <span>UPLINK: READY</span><span>CTRL: STBY</span>
            </div>
          </button>
        </div>

        <p style={{ marginTop: '3rem', color: '#907898', fontSize: '0.8rem', fontWeight: '600', position: 'relative', zIndex: 10 }}>
          DEMET3R Agricultural Swarm Control System — v4.2.0
        </p>
      </main>
    </div>
  );
}
