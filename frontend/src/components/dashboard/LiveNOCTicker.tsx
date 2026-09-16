import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { AlertCircle, CheckCircle2, Info, Activity } from 'lucide-react';

interface TickerEvent {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
}

export const LiveNOCTicker: React.FC = () => {
  const { lastMessage, isConnected } = useWebSocket();
  const [events, setEvents] = useState<TickerEvent[]>([]);

  useEffect(() => {
    setEvents([
      { id: '1', type: 'INFO', message: 'System baseline health check: Operational', timestamp: new Date() },
      { id: '2', type: 'SUCCESS', message: 'Deployment CHG9022 completed successfully on Core Database', timestamp: new Date(Date.now() - 300000) },
      { id: '3', type: 'WARNING', message: 'Latency advisory: Payment Gateway service response at 210ms', timestamp: new Date(Date.now() - 900000) },
    ]);
  }, []);

  useEffect(() => {
    if (lastMessage) {
      const newEvent: TickerEvent = {
        id: Date.now().toString(),
        type: lastMessage.type === 'NEW_INCIDENT' ? 'CRITICAL' : 'INFO',
        message: lastMessage.message || `New event: ${lastMessage.incident_id || 'System Update'} on ${lastMessage.service || 'Platform'}`,
        timestamp: new Date()
      };
      setEvents(prev => [newEvent, ...prev].slice(0, 10));
    }
  }, [lastMessage]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'CRITICAL': return <AlertCircle size={13} color="var(--status-critical)" />;
      case 'WARNING': return <Activity size={13} color="var(--status-warning)" />;
      case 'SUCCESS': return <CheckCircle2 size={13} color="var(--status-healthy)" />;
      default: return <Info size={13} color="var(--cg-blue-primary)" />;
    }
  };

  const getTextColor = (type: string) => {
    switch (type) {
      case 'CRITICAL': return 'var(--status-critical)';
      case 'WARNING': return 'var(--status-warning)';
      case 'SUCCESS': return 'var(--status-healthy)';
      default: return 'var(--cg-blue-primary)';
    }
  };

  return (
    <div style={{
      width: '100%',
      backgroundColor: 'var(--cg-surface-card)',
      borderBottom: '1px solid var(--cg-border)',
      display: 'flex',
      alignItems: 'center',
      height: '36px',
      padding: '0 1.25rem',
      gap: '0.85rem',
      boxSizing: 'border-box'
    }}>
      {/* Live NOC Badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem',
        fontWeight: 700,
        fontSize: '0.675rem',
        textTransform: 'uppercase',
        letterSpacing: '0.75px',
        color: 'var(--cg-blue-primary)',
        flexShrink: 0,
        borderRight: '1px solid var(--cg-border)',
        paddingRight: '0.85rem'
      }}>
        <Activity size={13} className={isConnected ? "animate-pulse" : ""} color="var(--cg-blue-primary)" />
        <span>NOC Live Feed</span>
      </div>
      
      {/* Feed Stream */}
      <div style={{
        flex: 1,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        whiteSpace: 'nowrap'
      }}>
        <div style={{
          display: 'flex',
          gap: '1.75rem',
          overflowX: 'auto',
          alignItems: 'center'
        }}>
          {events.map((ev, idx) => (
            <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.775rem', color: 'var(--text-primary)' }}>
              {getIcon(ev.type)}
              <span style={{ fontWeight: 700, color: getTextColor(ev.type) }}>{ev.type}:</span>
              <span>{ev.message}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                ({ev.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })})
              </span>
              {idx < events.length - 1 && <span style={{ color: 'var(--cg-border)', margin: '0 0.25rem' }}>•</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
