import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import { api } from './services/api';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initializeChat();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeChat = async () => {
    try {
      const response = await api.createNewChat();
      setSessionId(response.session_id);
      setMessages([]);
      setUploads([]);
      setSelectedFiles([]);
      setLoading(false);
    } catch (error) {
      console.error("Initialization error:", error);
    }
  };

  const handleUploadSuccess = async (result) => {
    const newFiles = result.uploaded_files.map(uf => ({
      file_id: uf.file_id,
      filename: uf.filename,
      file_type: uf.filename.split('.').pop(),
      upload_date: new Date().toISOString(),
      file_size: 0,
      chunk_count: uf.chunks,
      is_selected: true
    }));

    const updatedUploads = [...uploads, ...newFiles];
    setUploads(updatedUploads);
    
    const selectedIds = newFiles.map(f => f.file_id);
    setSelectedFiles([...selectedFiles, ...selectedIds]);
    
    if (sessionId) {
      await api.updateFileSelection(sessionId, [...selectedFiles, ...selectedIds]);
    }

    // Add system message
    setMessages(prev => [...prev, {
      role: 'system',
      content: `📄 Uploaded ${newFiles.length} file(s): ${newFiles.map(f => f.filename).join(', ')}`,
      timestamp: new Date(),
      source_files: []
    }]);
  };

  const handleSelectionChange = async (fileIds) => {
    setSelectedFiles(fileIds);
    if (sessionId) {
      await api.updateFileSelection(sessionId, fileIds);
    }
  };

  const handleNewChat = async () => {
    const newSession = {
      id: sessionId,
      name: `Chat - ${new Date().toLocaleString()}`,
      messages: messages.length,
      files: uploads.length
    };
    
    setChatHistory([newSession, ...chatHistory]);
    await initializeChat();
  };

  const handleDeleteChatHistory = async (chatId) => {
    setChatHistory(chatHistory.filter(c => c.id !== chatId));
  };

  const handleDeleteAllHistory = () => {
    if (window.confirm('Delete all chat history? This cannot be undone.')) {
      setChatHistory([]);
    }
  };

  const handleSendMessage = async (input) => {
    if (!input.trim() || selectedFiles.length === 0 || !sessionId) return;

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: input,
      timestamp: new Date(),
      source_files: []
    }]);

    try {
      // Process query
      const result = await api.processQuery(sessionId, input, selectedFiles);
      
      // Add assistant message with proper source attribution
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.answer,
        timestamp: new Date(),
        source_files: result.source_files,
        sources: result.retrieved_chunks
      }]);
    } catch (error) {
      console.error("Error:", error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Error processing query. Please try again.',
        timestamp: new Date(),
        source_files: []
      }]);
    }
  };


  const handleExport = async (format) => {
    try {
      const blob = await api.exportChat(sessionId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat_export.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export error:", error);
    }
  };

  if (loading) {
    return <div className="loading"><div className="spinner"></div>Loading...</div>;
  }

  return (
    <div className="app">
      <Sidebar 
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        uploads={uploads}
        selectedFiles={selectedFiles}
        onSelectionChange={handleSelectionChange}
        sessionId={sessionId}
        chatHistory={chatHistory}
        onLoadChat={(chatId) => setSessionId(chatId)}
        onDeleteChat={handleDeleteChatHistory}
        onDeleteAllHistory={handleDeleteAllHistory}
        onNewChat={handleNewChat}
      />

      <main className="main-container">
        <Chat
          sessionId={sessionId}
          selectedFiles={selectedFiles}
          messages={messages}
          uploads={uploads}
          onSendMessage={handleSendMessage}
          onExport={handleExport}
          onUpload={handleUploadSuccess}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
        />
        <div ref={messagesEndRef} />
      </main>
    </div>
  );
}

export default App;
