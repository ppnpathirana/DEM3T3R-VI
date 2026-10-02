// Set VITE_BACKEND_URL to the laptop's LAN URL for packaged Android builds.
const configured = (import.meta as any).env.VITE_BACKEND_URL as string | undefined;
export const BACKEND_URL = (configured || (
  window.location.port === '5173'
    ? `${window.location.protocol}//${window.location.hostname}:5001`
    : window.location.origin
)).replace(/\/$/, '');
