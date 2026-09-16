import React, { useState } from 'react';
import apiClient from '../../api/client';
import { Bot, Send, X, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  sources?: string[];
  timestamp: string;
}

export const AIChatDrawer: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'ai',
      text: 'Operations Intelligence Assistant ready. Query live metrics regarding incident volume, MTTR trends, SLA compliance, or problem backlog aging.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: input.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await apiClient.post('/ai/chat', { message: userMsg.text });
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.data.reply,
        sources: res.data.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("AI Chat failed", err);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Unable to fetch telemetry from analytics engine. Please retry.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Launcher Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: 'fixed',
            bottom: '2rem',
            right: '2rem',
            padding: '0.7rem 1.2rem',
            borderRadius: '50px',
            backgroundColor: 'var(--cg-blue-primary)',
            color: '#FFFFFF',
            border: 'none',
            boxShadow: '0 4px 16px rgba(23, 105, 170, 0.35)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            fontWeight: 600,
            fontSize: '0.85rem',
            zIndex: 1000,
            transition: 'all 0.2s ease'
          }}
        >
          <Sparkles size={16} color="#FFFFFF" />
          <span>Ask AI Analyst</span>
        </button>
      )}

      {/* Slide-over Chat Panel */}
      {isOpen && (
        <div style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          width: '420px',
          height: '580px',
          maxHeight: 'calc(100vh - 4rem)',
          backgroundColor: 'var(--cg-surface-elevated)',
          border: '1px solid var(--cg-border)',
          borderRadius: '12px',
          boxShadow: '0 12px 36px rgba(0, 0, 0, 0.12)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 1000,
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '1rem 1.25rem',
            backgroundColor: 'var(--cg-surface-secondary)',
            borderBottom: '1px solid var(--cg-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <div style={{
                padding: '0.35rem',
                borderRadius: '6px',
                backgroundColor: 'var(--cg-blue-soft)',
                color: 'var(--cg-blue-primary)'
              }}>
                <Bot size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '0.925rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>OPSINTEL AI Analyst</h3>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-healthy)', fontWeight: 500 }}>● Grounded in Real-Time Operational Telemetry</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages Body */}
          <div style={{
            flex: 1,
            padding: '1rem 1.25rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.85rem'
          }}>
            {messages.map(msg => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem'
                }}
              >
                <div style={{
                  padding: '0.75rem 1rem',
                  borderRadius: msg.sender === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                  backgroundColor: msg.sender === 'user' ? 'var(--cg-blue-primary)' : 'var(--cg-surface-secondary)',
                  color: msg.sender === 'user' ? '#FFFFFF' : 'var(--text-primary)',
                  fontSize: '0.85rem',
                  lineHeight: 1.5,
                  border: msg.sender === 'user' ? 'none' : '1px solid var(--cg-border)'
                }}>
                  {msg.text}
                </div>
                {msg.sources && (
                  <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)', display: 'flex', gap: '0.35rem' }}>
                    <span>Sources:</span>
                    {msg.sources.map((s, idx) => (
                      <span key={idx} style={{ color: 'var(--cg-blue-primary)', fontWeight: 600 }}>[{s}]</span>
                    ))}
                  </div>
                )}
                <span style={{
                  fontSize: '0.65rem',
                  color: 'var(--text-muted)',
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start'
                }}>
                  {msg.timestamp}
                </span>
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: 'flex-start', color: 'var(--text-secondary)', fontSize: '0.825rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={15} className="animate-spin" color="var(--cg-blue-primary)" />
                Analyzing operational metrics...
              </div>
            )}
          </div>

          {/* Input Footer */}
          <div style={{
            padding: '0.85rem 1rem',
            backgroundColor: 'var(--cg-surface-secondary)',
            borderTop: '1px solid var(--cg-border)',
            display: 'flex',
            gap: '0.5rem'
          }}>
            <input
              type="text"
              placeholder="Ask e.g. Why is Payment Gateway MTTR high?"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              style={{
                flex: 1,
                padding: '0.65rem 0.85rem',
                borderRadius: '7px',
                border: '1px solid var(--cg-border)',
                backgroundColor: 'var(--cg-surface-card)',
                color: 'var(--text-primary)',
                fontSize: '0.825rem',
                outline: 'none'
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="btn-cg-primary"
              style={{
                padding: '0.65rem 0.85rem',
                borderRadius: '7px',
                cursor: !input.trim() || loading ? 'not-allowed' : 'pointer',
                opacity: !input.trim() || loading ? 0.6 : 1
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
