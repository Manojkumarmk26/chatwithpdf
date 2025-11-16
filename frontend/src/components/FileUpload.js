import React, { useState, useRef } from 'react';
import './FileUpload.css';
import { API_BASE } from '../services/api';

const FileUpload = ({ sessionId, onUploadSuccess }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(prev => [...prev, ...droppedFiles].slice(0, 10));
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles].slice(0, 10));
  };

  const handleRemoveFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (files.length === 0 || !sessionId) {
      alert("Please select files and ensure you have a valid session");
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      files.forEach(file => formData.append("files", file));

      // Add session_id as a query parameter
      const url = new URL(`${API_BASE}/upload`);
      url.searchParams.append('session_id', sessionId);

      console.log("Uploading to:", url.toString());
      
      const response = await fetch(url, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      console.log("Upload response:", result);
      
      if (result.status === 'success') {
        onUploadSuccess(result);
        setFiles([]);
      } else {
        throw new Error(result.message || 'Upload failed');
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div
        className={`drop-zone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.bmp"
          style={{ display: 'none' }}
        />
        <span className="drop-icon">📤</span>
        <p className="drop-text">
          Drag files here or click to browse
        </p>
        <p className="drop-subtext">
          PDF, Word, or Images (Max 10 files, 100MB each)
        </p>
      </div>

      {files.length > 0 && (
        <div className="files-preview">
          <h4>Selected Files ({files.length})</h4>
          <div className="files-list">
            {files.map((file, idx) => (
              <div key={idx} className="file-preview-item">
                <span className="file-icon">📄</span>
                <div className="file-details">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
                <button
                  className="remove-file-btn"
                  onClick={() => handleRemoveFile(idx)}
                  disabled={uploading}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading || files.length === 0}
          >
            {uploading ? '⏳ Uploading...' : '📤 Upload ' + files.length + ' File(s)'}
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;