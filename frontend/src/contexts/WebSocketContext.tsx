import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  lastMessage: any | null;
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider = ({ children }: { children: ReactNode }) => {
  const [lastMessage, setLastMessage] = useState<any | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    let ws: WebSocket | null = null;

    if (isAuthenticated) {
      ws = new WebSocket('ws://localhost:8000/api/v1/ws/dashboard');

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          console.error("Error parsing websocket message", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
      };
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [isAuthenticated]);

  return (
    <WebSocketContext.Provider value={{ lastMessage, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
