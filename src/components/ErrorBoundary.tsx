import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary caught exception]:', error, errorInfo);
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '24px',
          margin: '16px 0',
          borderRadius: '16px',
          background: 'rgba(30, 20, 38, 0.95)',
          border: '1.5px solid rgba(224, 64, 160, 0.4)',
          color: '#ffffff',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>⚠️</div>
          <h3 style={{ margin: '0 0 8px 0', color: '#e040a0', fontWeight: '800' }}>
            {this.props.fallbackTitle || 'Widget Temporarily Unavailable'}
          </h3>
          <p style={{ margin: '0 0 12px 0', fontSize: '0.85rem', color: '#a088a5' }}>
            {this.props.fallbackMessage || 'An unexpected rendering error occurred. The rest of the dashboard remains fully operational.'}
          </p>
          {this.state.error && (
            <div style={{
              margin: '0 auto 16px auto',
              maxWidth: '600px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid rgba(224, 64, 160, 0.2)',
              fontSize: '0.75rem',
              color: '#ff90c0',
              fontFamily: 'monospace',
              textAlign: 'left',
              wordBreak: 'break-word'
            }}>
              {this.state.error.message || String(this.state.error)}
            </div>
          )}
          <button
            onClick={() => {
              this.handleReset();
              if (window.location.pathname !== '/console') {
                window.location.href = '/console';
              }
            }}
            style={{
              background: 'linear-gradient(135deg, #e040a0, #7928ca)',
              border: 'none',
              borderRadius: '8px',
              color: '#ffffff',
              padding: '10px 22px',
              fontWeight: '700',
              cursor: 'pointer',
              fontSize: '0.85rem',
              boxShadow: '0 4px 14px rgba(224, 64, 160, 0.4)'
            }}
          >
            🔄 Recover Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}