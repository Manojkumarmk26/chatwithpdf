import React, { useState, useRef, useEffect } from 'react';
import FileUpload from './FileUpload';
import ChatMessage from './ChatMessage';
import ExportButton from './ExportButton';
import SummaryPanel from './SummaryPanel';
import './Chat.css';

const Chat = ({
  sessionId,
  selectedFiles,
  messages,
  uploads,
  onSendMessage,
  onExport,
  onUpload,
  sidebarOpen,
  setSidebarOpen
}) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || selectedFiles.length === 0 || loading) return;

    setLoading(true);
    setInput('');
    
    try {
      await onSendMessage(input);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button 
          className="menu-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          ☰
        </button>
        <h1>Document Analysis Chat</h1>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-section">
            <div className="welcome-content">
              <h2>🚀 Welcome to DocChat</h2>
              <p>Upload documents and ask questions about their content</p>
              
              <div className="welcome-suggestions">
                <div className="suggestion-card">
                  <h4>📄 Upload Documents</h4>
                  <p>Add PDFs, Word docs, or images</p>
                </div>
                <div className="suggestion-card">
                  <h4>✅ Select Files</h4>
                  <p>Choose which documents to analyze</p>
                </div>
                <div className="suggestion-card">
                  <h4>💬 Ask Questions</h4>
                  <p>Get instant answers from your documents</p>
                </div>
                <div className="suggestion-card">
                  <h4>📥 Export Results</h4>
                  <p>Save chat as PDF, Word, or Text</p>
                </div>
              </div>
            </div>

            <FileUpload sessionId={sessionId} onUploadSuccess={onUpload} />
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <ChatMessage 
                key={idx} 
                message={msg}
                uploads={uploads}
              />
            ))}
            {loading && (
              <div className="loading-message">
                <div className="spinner-small"></div>
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {messages.length > 0 && (
        <div className="chat-actions">
          <ExportButton sessionId={sessionId} onExport={onExport} />
        </div>
      )}

      {selectedFiles.length > 0 && (
        <SummaryPanel
          sessionId={sessionId}
          userId="default_user"
          selectedFiles={selectedFiles}
        />
      )}

      <div className="input-section">
        {uploads.length === 0 ? (
          <div className="upload-prompt">
            <p>👆 Upload documents to get started</p>
            <FileUpload sessionId={sessionId} onUploadSuccess={onUpload} />
          </div>
        ) : selectedFiles.length === 0 ? (
          <div className="selection-prompt">
            <p>⚠️ Select at least one document to ask questions</p>
          </div>
        ) : (
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents... (Shift+Enter for new line)"
              className="message-input"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading || selectedFiles.length === 0}
              className="send-btn"
              title="Send message (Enter)"
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;