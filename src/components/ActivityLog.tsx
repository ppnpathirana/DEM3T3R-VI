/**
 * @file ActivityLog.tsx
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

﻿import { LogEntry } from '../App';

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
