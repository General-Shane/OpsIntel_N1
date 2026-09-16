import React, { useEffect, useState } from 'react';
import apiClient from '../../api/client';
import { Activity } from 'lucide-react';

export const HealthCheck: React.FC = () => {
  const [status, setStatus] = useState<string>('CHECKING');
  const [message, setMessage] = useState<string>('Connecting to OPSINTEL API...');

  useEffect(() => {
    apiClient.get('/system/status')
      .then((response) => {
        setStatus(response.data.status);
        setMessage(response.data.message);
      })
      .catch((error) => {
        setStatus('UNAVAILABLE');
        setMessage(error.message || 'Failed to connect to API');
      });
  }, []);

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem' }}>
      <Activity size={48} color={status === 'HEALTHY' ? 'var(--status-healthy)' : 'var(--status-critical)'} />
      <h2 style={{ marginTop: '1rem' }}>Backend Status: {status}</h2>
      <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>{message}</p>
    </div>
  );
};
