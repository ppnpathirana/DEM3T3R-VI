import { LogEntry } from '../App';

type ActivityLogProps = {
  logs: LogEntry[];
};

export default function ActivityLog({ logs }: ActivityLogProps) {
  return (
    <div className="glass-card">
      <div className="card-header">
        <div className="card-header-dot" />
        Activity Log
      </div>
      
      <div className="log-area">
        {logs.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
            No activity yet
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="log-entry">
              <span className="log-time">{log.time}</span>
              <span className="log-icon">{log.icon}</span>
              <span className="log-msg">{log.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
