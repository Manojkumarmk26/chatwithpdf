import React, { useState } from 'react';
import './Sidebar.css';

const Sidebar = ({
  sidebarOpen,
  setSidebarOpen,
  uploads,
  selectedFiles,
  onSelectionChange,
  sessionId,
  chatHistory,
  onLoadChat,
  onDeleteChat,
  onDeleteAllHistory,
  onNewChat
}) => {
  const [showHistory, setShowHistory] = useState(false);

  const handleToggle = (fileId) => {
    // Don't add null/undefined fileIds
    if (fileId == null) return;
    
    const updated = selectedFiles.includes(fileId)
      ? selectedFiles.filter(id => id !== fileId)
      : [...selectedFiles, fileId];
    onSelectionChange(updated);
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      // Filter out any null/undefined file_ids before setting the selection
      const validFileIds = uploads
        .map(f => f.file_id)
        .filter(id => id != null); // This removes both null and undefined
      onSelectionChange(validFileIds);
    } else {
      onSelectionChange([]);
    }
  };

  if (!sidebarOpen) {
    return (
      <button 
        className="sidebar-toggle-mobile"
        onClick={() => setSidebarOpen(true)}
      >
        ☰
      </button>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-logo">💬 DocChat</h1>
        <button 
          className="sidebar-close"
          onClick={() => setSidebarOpen(false)}
        >
          ✕
        </button>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        ➕ New Chat
      </button>

      {uploads.length > 0 && (
        <div className="documents-section">
          <h3 className="section-title">📁 Documents ({uploads.length})</h3>
          
          <label className="select-all-label">
            <input
              type="checkbox"
              checked={selectedFiles.length === uploads.length && uploads.length > 0}
              onChange={handleSelectAll}
            />
            <span>Select All</span>
          </label>

          <div className="documents-list">
            {uploads.map((file) => (
              <label key={file.file_id} className="document-item">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(file.file_id)}
                  onChange={() => handleToggle(file.file_id)}
                />
                <div className="document-info">
                  <span className="document-name">{file.filename}</span>
                  <span className="document-meta">
                    {file.chunk_count} chunks
                  </span>
                </div>
              </label>
            ))}
          </div>

          <div className="selection-summary">
            ✓ {selectedFiles.length}/{uploads.length} selected
          </div>
        </div>
      )}

      <div className="history-section">
        <button 
          className="history-toggle"
          onClick={() => setShowHistory(!showHistory)}
        >
          🕐 History ({chatHistory.length})
        </button>

        {showHistory && (
          <div className="history-list">
            {chatHistory.length === 0 ? (
              <p className="empty-history">No chat history</p>
            ) : (
              <>
                {chatHistory.slice(0, 10).map((chat) => (
                  <div key={chat.id} className="history-item">
                    <button 
                      className="history-item-name"
                      onClick={() => onLoadChat(chat.id)}
                    >
                      {chat.name}
                      <span className="history-item-meta">
                        {chat.messages} msg • {chat.files} file
                      </span>
                    </button>
                    <button
                      className="history-item-delete"
                      onClick={() => onDeleteChat(chat.id)}
                      title="Delete chat"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
                {chatHistory.length > 0 && (
                  <button 
                    className="clear-history-btn"
                    onClick={onDeleteAllHistory}
                  >
                    🗑️ Clear All History
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
