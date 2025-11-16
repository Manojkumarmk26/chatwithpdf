export const API_BASE = "http://localhost:8000/api";

export const api = {
  // Chat endpoints
  createNewChat: async () => {
    const response = await fetch(`${API_BASE}/chat/new`, { method: "POST" });
    return response.json();
  },

  uploadDocuments: async (sessionId, files) => {
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    
    const response = await fetch(`${API_BASE}/upload?session_id=${sessionId}`, {
      method: "POST",
      body: formData
    });
    return response.json();
  },

  processQuery: async (sessionId, query, selectedFileIds) => {
    const response = await fetch(`${API_BASE}/chat/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        selected_file_ids: selectedFileIds
      })
    });
    return response.json();
  },

exportChat: async (sessionId, format) => {
    const response = await fetch(`${API_BASE}/chat/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        format
      })
    });
    return response.blob();
  },

  getSession: async (sessionId) => {
    const response = await fetch(`${API_BASE}/chat/${sessionId}`);
    return response.json();
  },

  updateFileSelection: async (sessionId, fileIds) => {
    const response = await fetch(`${API_BASE}/chat/${sessionId}/select-files`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fileIds)
    });
    return response.json();
  },

  deleteSession: async (sessionId) => {
    const response = await fetch(`${API_BASE}/chat/${sessionId}`, {
      method: "DELETE"
    });
    return response.json();
  },

  enhancedAnalysis: async (sessionId, selectedFileIds, query = null, analysisType = "comprehensive") => {
    const response = await fetch(`${API_BASE}/analysis/enhanced`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        selected_file_ids: selectedFileIds,
        query: query,
        analysis_type: analysisType
      })
    });
    return response.json();
  }
};