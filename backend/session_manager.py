"""
Session Management Module
Handles persistent storage and recovery of chat sessions
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages session persistence and recovery."""
    
    def __init__(self, sessions_dir: Path = Path("./sessions")):
        """Initialize session manager."""
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ SessionManager initialized at {self.sessions_dir}")
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session metadata to disk."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            # Add timestamp
            session_data['last_updated'] = datetime.now().isoformat()
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"✅ Session {session_id} saved")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session metadata from disk."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                logger.warning(f"⚠️ Session {session_id} not found")
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            logger.info(f"✅ Session {session_id} loaded")
            return session_data
        except Exception as e:
            logger.error(f"❌ Failed to load session {session_id}: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """List all available sessions."""
        try:
            sessions = [f.stem for f in self.sessions_dir.glob("*.json")]
            logger.info(f"✅ Found {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to list sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"✅ Session {session_id} deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 7) -> int:
        """Delete sessions older than specified days."""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    last_updated = datetime.fromisoformat(session_data.get('last_updated', ''))
                    if last_updated < cutoff_time:
                        session_file.unlink()
                        deleted_count += 1
                except:
                    pass
            
            logger.info(f"✅ Cleaned up {deleted_count} old sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"❌ Failed to cleanup sessions: {e}")
            return 0
