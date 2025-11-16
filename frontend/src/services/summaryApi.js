/**
 * Summary API Service
 * Handles all summary-related API calls to the backend
 */

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const SUMMARY_API = `${API_BASE}/api/summary`;

/**
 * Generate a summary for a document
 * @param {string} filename - The filename of the document
 * @param {string} sessionId - The session ID
 * @param {string} userId - The user ID (optional)
 * @returns {Promise<Object>} Summary response with text and metadata
 */
export const generateSummary = async (filename, sessionId, userId = "default_user") => {
  try {
    const response = await fetch(`${SUMMARY_API}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename,
        session_id: sessionId,
        user_id: userId
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to generate summary: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error generating summary:", error);
    throw error;
  }
};

/**
 * Combine multiple summaries into one
 * @param {Array<string>} filenames - Array of filenames to combine
 * @param {string} sessionId - The session ID
 * @param {string} userId - The user ID (optional)
 * @returns {Promise<Object>} Combined summary response
 */
export const combineSummaries = async (filenames, sessionId, userId = "default_user") => {
  try {
    const response = await fetch(`${SUMMARY_API}/combine`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filenames,
        session_id: sessionId,
        user_id: userId
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to combine summaries: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error combining summaries:", error);
    throw error;
  }
};

/**
 * Condense a summary into a brief executive summary
 * @param {string} summaryText - The summary text to condense
 * @returns {Promise<Object>} Condensed summary response
 */
export const condenseSummary = async (summaryText) => {
  try {
    const response = await fetch(`${SUMMARY_API}/condense`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        summary_text: summaryText
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to condense summary: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error condensing summary:", error);
    throw error;
  }
};

/**
 * Retrieve a previously saved summary
 * @param {string} filename - The filename to retrieve summary for
 * @returns {Promise<Object>} Summary response with text and metadata
 */
export const retrieveSummary = async (filename) => {
  try {
    const response = await fetch(`${SUMMARY_API}/retrieve/${encodeURIComponent(filename)}`);

    if (!response.ok) {
      throw new Error(`Failed to retrieve summary: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error retrieving summary:", error);
    throw error;
  }
};

/**
 * List all saved summaries
 * @returns {Promise<Object>} List of all saved summaries with metadata
 */
export const listSummaries = async () => {
  try {
    const response = await fetch(`${SUMMARY_API}/list`);

    if (!response.ok) {
      throw new Error(`Failed to list summaries: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error listing summaries:", error);
    throw error;
  }
};

export default {
  generateSummary,
  combineSummaries,
  condenseSummary,
  retrieveSummary,
  listSummaries
};
