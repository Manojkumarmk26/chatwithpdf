/**
 * Summary Panel Component
 * Displays and manages document summaries
 */

import React, { useState, useEffect } from "react";
import summaryApi from "../services/summaryApi";
import "./SummaryPanel.css";

const SummaryPanel = ({ sessionId, userId = "default_user", selectedFiles = [] }) => {
  const [summaries, setSummaries] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("generate");
  const [condensedSummary, setCondensedSummary] = useState(null);
  const [combinedSummary, setCombinedSummary] = useState(null);

  // Load saved summaries on mount
  useEffect(() => {
    loadSavedSummaries();
  }, []);

  /**
   * Load all saved summaries
   */
  const loadSavedSummaries = async () => {
    try {
      const response = await summaryApi.listSummaries();
      if (response.success) {
        const summaryMap = {};
        response.summaries.forEach((summary) => {
          summaryMap[summary.filename] = summary;
        });
        setSummaries(summaryMap);
      }
    } catch (err) {
      console.error("Failed to load summaries:", err);
    }
  };

  /**
   * Generate summary for a file
   */
  const handleGenerateSummary = async (filename) => {
    setLoading(true);
    setError(null);
    try {
      const response = await summaryApi.generateSummary(filename, sessionId, userId);
      if (response.success) {
        setSummaries((prev) => ({
          ...prev,
          [filename]: {
            filename,
            length: response.metadata.length,
            saved_at: response.metadata.saved_at,
            document_type: response.metadata.document_type
          }
        }));
        alert(`✅ Summary generated for ${filename}`);
      }
    } catch (err) {
      setError(`Failed to generate summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Retrieve and display a summary
   */
  const handleRetrieveSummary = async (filename) => {
    setLoading(true);
    setError(null);
    try {
      const response = await summaryApi.retrieveSummary(filename);
      if (response.success) {
        setSummaries((prev) => ({
          ...prev,
          [filename]: {
            ...prev[filename],
            content: response.summary
          }
        }));
      }
    } catch (err) {
      setError(`Failed to retrieve summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Combine multiple summaries
   */
  const handleCombineSummaries = async () => {
    if (selectedFiles.length === 0) {
      setError("Please select at least one file");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await summaryApi.combineSummaries(
        selectedFiles,
        sessionId,
        userId
      );
      if (response.success) {
        setCombinedSummary(response.summary);
        setActiveTab("combined");
      }
    } catch (err) {
      setError(`Failed to combine summaries: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Condense a summary
   */
  const handleCondenseSummary = async (summaryText) => {
    setLoading(true);
    setError(null);
    try {
      const response = await summaryApi.condenseSummary(summaryText);
      if (response.success) {
        setCondensedSummary(response.condensed_summary);
        setActiveTab("condensed");
      }
    } catch (err) {
      setError(`Failed to condense summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Download summary as text file
   */
  const downloadSummary = (filename, content) => {
    const element = document.createElement("a");
    element.setAttribute(
      "href",
      "data:text/plain;charset=utf-8," + encodeURIComponent(content)
    );
    element.setAttribute("download", `${filename}_summary.txt`);
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="summary-panel">
      <div className="summary-header">
        <h2>📄 Summary Manager</h2>
        <p className="session-info">Session: {sessionId}</p>
      </div>

      {error && <div className="error-message">❌ {error}</div>}

      <div className="summary-tabs">
        <button
          className={`tab ${activeTab === "generate" ? "active" : ""}`}
          onClick={() => setActiveTab("generate")}
        >
          Generate
        </button>
        <button
          className={`tab ${activeTab === "combine" ? "active" : ""}`}
          onClick={() => setActiveTab("combine")}
        >
          Combine
        </button>
        <button
          className={`tab ${activeTab === "list" ? "active" : ""}`}
          onClick={() => setActiveTab("list")}
        >
          Saved ({Object.keys(summaries).length})
        </button>
        {condensedSummary && (
          <button
            className={`tab ${activeTab === "condensed" ? "active" : ""}`}
            onClick={() => setActiveTab("condensed")}
          >
            Condensed
          </button>
        )}
        {combinedSummary && (
          <button
            className={`tab ${activeTab === "combined" ? "active" : ""}`}
            onClick={() => setActiveTab("combined")}
          >
            Combined
          </button>
        )}
      </div>

      <div className="summary-content">
        {/* Generate Tab */}
        {activeTab === "generate" && (
          <div className="tab-content">
            <h3>Generate Summary</h3>
            <p>Select a file to generate a summary:</p>
            <div className="file-list">
              {selectedFiles.length > 0 ? (
                selectedFiles.map((file) => (
                  <div key={file} className="file-item">
                    <span>{file}</span>
                    <button
                      onClick={() => handleGenerateSummary(file)}
                      disabled={loading}
                      className="btn-primary"
                    >
                      {loading ? "Generating..." : "Generate"}
                    </button>
                  </div>
                ))
              ) : (
                <p className="no-files">No files selected</p>
              )}
            </div>
          </div>
        )}

        {/* Combine Tab */}
        {activeTab === "combine" && (
          <div className="tab-content">
            <h3>Combine Summaries</h3>
            <p>Combine {selectedFiles.length} selected files into one summary:</p>
            <button
              onClick={handleCombineSummaries}
              disabled={loading || selectedFiles.length === 0}
              className="btn-primary"
            >
              {loading ? "Combining..." : "Combine Summaries"}
            </button>
          </div>
        )}

        {/* List Tab */}
        {activeTab === "list" && (
          <div className="tab-content">
            <h3>Saved Summaries</h3>
            {Object.keys(summaries).length > 0 ? (
              <div className="summary-list">
                {Object.entries(summaries).map(([filename, summary]) => (
                  <div key={filename} className="summary-item">
                    <div className="summary-info">
                      <h4>{filename}</h4>
                      <p className="meta">
                        Type: {summary.document_type || "Unknown"} | Length:{" "}
                        {summary.length || 0} chars
                      </p>
                      <p className="meta">
                        Saved: {new Date(summary.saved_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="summary-actions">
                      <button
                        onClick={() => handleRetrieveSummary(filename)}
                        disabled={loading}
                        className="btn-secondary"
                      >
                        View
                      </button>
                      {summary.content && (
                        <>
                          <button
                            onClick={() =>
                              handleCondenseSummary(summary.content)
                            }
                            disabled={loading}
                            className="btn-secondary"
                          >
                            Condense
                          </button>
                          <button
                            onClick={() =>
                              downloadSummary(filename, summary.content)
                            }
                            className="btn-secondary"
                          >
                            Download
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-summaries">No saved summaries yet</p>
            )}
          </div>
        )}

        {/* Condensed Tab */}
        {activeTab === "condensed" && condensedSummary && (
          <div className="tab-content">
            <h3>Condensed Summary</h3>
            <div className="summary-text">
              <p>{condensedSummary}</p>
            </div>
            <button
              onClick={() =>
                downloadSummary("condensed_summary", condensedSummary)
              }
              className="btn-primary"
            >
              Download
            </button>
          </div>
        )}

        {/* Combined Tab */}
        {activeTab === "combined" && combinedSummary && (
          <div className="tab-content">
            <h3>Combined Summary</h3>
            <div className="summary-text">
              <p>{combinedSummary}</p>
            </div>
            <button
              onClick={() =>
                downloadSummary("combined_summary", combinedSummary)
              }
              className="btn-primary"
            >
              Download
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryPanel;
