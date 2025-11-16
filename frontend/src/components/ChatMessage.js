import React, { useState } from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message, uploads }) => {
  const [expandedSources, setExpandedSources] = useState(false);
  const [expandedSource, setExpandedSource] = useState(null);
  
  const getSources = () => {
    if (!message.sources || message.sources.length === 0) {
      return [];
    }
    return message.sources.map((source, idx) => ({
      ...source,
      id: idx
    }));
  };

  const sources = getSources();

  if (message.role === 'system') {
    return (
      <div className="system-message">
        <span className="system-icon">ℹ️</span>
        <span className="system-content">{message.content}</span>
      </div>
    );
  }

  const isUser = message.role === 'user';

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message ${isUser ? 'user-msg' : 'assistant-msg'}`}>
        <div className="message-avatar">
          {isUser ? '👤' : '🤖'}
        </div>
        
        <div className="message-body">
          <div className="message-header">
            <span className="message-role">
              {isUser ? 'You' : 'Assistant'}
            </span>
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          </div>
          
          <div className="message-content">
            {message.content}
          </div>

          {sources.length > 0 && !isUser && (
            <div className="message-sources-enhanced">
              <button 
                className="sources-toggle-enhanced"
                onClick={() => setExpandedSources(!expandedSources)}
              >
                <span className="sources-icon">🔍</span>
                <span className="sources-label">Vector Search Results: {sources.length}</span>
                <span className="toggle-arrow">{expandedSources ? '▼' : '▶'}</span>
              </button>
              
              {expandedSources && (
                <div className="sources-list-enhanced">
                  {sources.map((source) => (
                    <div key={source.id} className="source-item-enhanced">
                      <div className="source-header-enhanced">
                        <div className="source-info">
                          <span className="source-rank">#{source.rank}</span>
                          <span className="source-filename">📄 {source.filename}</span>
                          <span className="source-relevance">
                            Relevance: <strong>{source.relevance_score?.toFixed(1) || (source.similarity * 100).toFixed(1)}%</strong>
                          </span>
                        </div>
                        <button
                          className="source-expand-btn"
                          onClick={() => setExpandedSource(expandedSource === source.id ? null : source.id)}
                        >
                          {expandedSource === source.id ? '−' : '+'}
                        </button>
                      </div>
                      
                      {expandedSource === source.id && (
                        <div className="source-preview-enhanced">
                          <div className="preview-label">Content Preview:</div>
                          <div className="preview-text">
                            {source.preview || source.content?.substring(0, 200) || 'No preview available'}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
