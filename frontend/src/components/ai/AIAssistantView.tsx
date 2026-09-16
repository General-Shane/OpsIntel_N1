import React, { useState } from 'react';
import apiClient from '../../api/client';
import {
  Bot,
  Send,
  Plus,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
}

export const AIAssistantView: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'user',
      text: 'Why did incident volume increase this week?',
      timestamp: '10:30 AM'
    },
    {
      id: '2',
      sender: 'ai',
      text: `Incident volume increased by **18%** this week compared to last week.

Here are the key contributing factors identified by canonical cross-domain analysis:

1. **Authentication Service issues**
   Incidents related to login failures increased by 45% due to the new MFA rollout.

2. **Payment Gateway timeouts**
   Timeout errors increased by 32% during peak hours following CHG9001 deployment.

3. **Database performance degradation**
   Slower query response times were observed from Jul 25 onwards on SVC_DB.

**Recommendations:**
- Consider database query optimization & connection pooling.
- Roll back or patch Payment Gateway configuration CHG9001.
- Review MFA authentication rate-limiting thresholds.`,
      timestamp: '10:31 AM'
    }
  ]);

  const quickPrompts = [
    "Which service is most at risk?",
    "What changed compared to last week?",
    "Show me SLA compliance trends",
    "Summarize this month's operational health"
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await apiClient.post('/ai/chat', { message: userMsg.text });
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error("AI Chat failed", err);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: "I was unable to complete the query. Please verify that the Gemini API Key is configured in your `.env` file.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    setMessages([
      {
        id: Date.now().toString(),
        sender: 'ai',
        text: "New conversation initiated. Ask me anything regarding ITSM operational metrics, root-cause correlations, or recommended runbooks.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: 'calc(100vh - 7rem)' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Bot color="var(--cg-blue-primary)" size={24} />
            AI Operational Assistant
          </h1>
          <p className="page-subtitle">
            Ask questions and get AI-powered insights grounded in live telemetry
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleNewConversation}
            className="btn-cg-secondary"
          >
            <Plus size={15} />
            <span>New Conversation</span>
          </button>
        </div>
      </div>

      {/* Main Workspace Layout (Chat Panel Left + Sidebar Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.25rem', flex: 1, minHeight: 0 }}>
        {/* Left Chat Window Container */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          {/* Messages Stream */}
          <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {messages.map(msg => (
              <div
                key={msg.id}
                style={{
                  alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  gap: '0.75rem'
                }}
              >
                {msg.sender === 'ai' && (
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--cg-blue-soft)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--cg-blue-primary)',
                    flexShrink: 0
                  }}>
                    <Bot size={17} />
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
                  <div style={{
                    padding: '0.85rem 1.15rem',
                    borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                    backgroundColor: msg.sender === 'user' ? 'var(--cg-blue-primary)' : 'var(--cg-surface-secondary)',
                    color: msg.sender === 'user' ? '#FFFFFF' : 'var(--text-primary)',
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    whiteSpace: 'pre-line',
                    border: msg.sender === 'user' ? 'none' : '1px solid var(--cg-border)'
                  }}>
                    {msg.text}
                  </div>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{msg.timestamp}</span>
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--cg-blue-primary)', fontSize: '0.85rem' }}>
                <RefreshCw size={15} className="animate-spin" />
                Querying Google Gemini AI Analyst engine...
              </div>
            )}
          </div>

          {/* Quick Action Prompt Chips */}
          <div style={{ padding: '0.65rem 1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', borderTop: '1px solid var(--cg-border)', backgroundColor: 'var(--cg-surface-secondary)' }}>
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                style={{
                  padding: '0.4rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--cg-border)',
                  backgroundColor: 'var(--cg-surface-card)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <div style={{ padding: '0.85rem 1.25rem', backgroundColor: 'var(--cg-surface-secondary)', borderTop: '1px solid var(--cg-border)', display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              placeholder="Ask a follow-up question..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              style={{
                flex: 1,
                padding: '0.65rem 0.95rem',
                borderRadius: '7px',
                border: '1px solid var(--cg-border)',
                backgroundColor: 'var(--cg-surface-card)',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                outline: 'none'
              }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || loading}
              className="btn-cg-primary"
              style={{
                padding: '0.65rem 1rem',
                opacity: !input.trim() || loading ? 0.6 : 1
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>

        {/* Right Insights Sidebar Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', overflowY: 'auto' }}>
          {/* Key Insights Card */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Key Insights
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Incidents</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--status-critical)' }}>248 ▲ 18%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>SLA Compliance</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--status-healthy)' }}>95.6% ▲ 3.2%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>MTTR</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>11.4 hrs ▬ 0%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Change Success</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--cg-blue-primary)' }}>82.1% ▲ 2.7%</span>
              </div>
            </div>
          </div>

          {/* Affected Services Card */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Affected Services (Top 3)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ padding: '0.65rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>1. Authentication Service</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--status-critical)', fontWeight: 700 }}>68 (▲ 45%)</span>
              </div>
              <div style={{ padding: '0.65rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>2. Payment Gateway</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--status-warning)', fontWeight: 700 }}>52 (▲ 28%)</span>
              </div>
              <div style={{ padding: '0.65rem', borderRadius: '6px', backgroundColor: 'var(--cg-surface-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>3. E-Commerce Platform</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--cg-blue-primary)', fontWeight: 700 }}>36 (▲ 15%)</span>
              </div>
            </div>
          </div>

          {/* Data Sources Used Checklist */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Data Sources Used
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['Incidents', 'Problems', 'Changes', 'SLA / Performance', 'Service Health'].map((src, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--status-healthy)' }}>
                  <CheckCircle2 size={16} />
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{src}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
