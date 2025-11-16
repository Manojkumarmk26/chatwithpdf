import React, { useState } from 'react';
import './ExportButton.css';

const ExportButton = ({ sessionId, onExport, disabled = false }) => {
  const [exporting, setExporting] = useState(null);

  const handleExport = async (format) => {
    setExporting(format);
    try {
      await onExport(format);
    } catch (error) {
      console.error("Export error:", error);
      alert("Export failed. Please try again.");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="export-buttons">
      <button
        onClick={() => handleExport('pdf')}
        disabled={disabled || exporting}
        className="export-btn pdf-btn"
        title="Export as PDF"
      >
        {exporting === 'pdf' ? '⏳' : '📄'} PDF
      </button>
      <button
        onClick={() => handleExport('docx')}
        disabled={disabled || exporting}
        className="export-btn docx-btn"
        title="Export as Word"
      >
        {exporting === 'docx' ? '⏳' : '📝'} Word
      </button>
      <button
        onClick={() => handleExport('txt')}
        disabled={disabled || exporting}
        className="export-btn txt-btn"
        title="Export as Text"
      >
        {exporting === 'txt' ? '⏳' : '📋'} TXT
      </button>
    </div>
  );
};

export default ExportButton;