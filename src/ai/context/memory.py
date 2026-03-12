"""Memory Management for AI Conversations

Maintains conversation history and context across AI interactions to provide
continuity and learning capabilities.
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ConversationTurn:
    """A single turn in an AI conversation"""

    timestamp: str
    user_input: str
    ai_response: str
    context_hash: str
    actions_taken: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextMemory:
    """Represents stored context about workflows and user patterns"""

    user_id: str
    context_type: str  # workflow, preference, pattern
    key: str
    value: Any
    confidence: float
    last_updated: str
    usage_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConversationMemory:
    """Manages AI conversation history and learning"""

    def __init__(self, memory_dir: Path = None):
        # User conversation memory should be in gitignored directory
        self.memory_dir = memory_dir or Path(".conductor/memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database for efficient querying
        self.db_path = self.memory_dir / "conversations.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for conversation storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    actions_taken TEXT,  -- JSON string
                    metadata TEXT,       -- JSON string
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,  -- JSON string
                    confidence REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, context_type, key)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id, timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_memory_user
                ON context_memory(user_id, context_type)
            """)

            conn.commit()

    def add_conversation_turn(
        self,
        session_id: str,
        user_input: str,
        ai_response: str,
        context_hash: str,
        actions_taken: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None,
    ) -> int:
        """Add a conversation turn to memory"""
        actions_taken = actions_taken or []
        metadata = metadata or {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversations
                (session_id, timestamp, user_input, ai_response, context_hash, actions_taken, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    datetime.now().isoformat(),
                    user_input,
                    ai_response,
                    context_hash,
                    json.dumps(actions_taken),
                    json.dumps(metadata),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(
        self, session_id: str, limit: int = 10, since: datetime = None
    ) -> List[ConversationTurn]:
        """Get conversation history for a session"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT timestamp, user_input, ai_response, context_hash, actions_taken, metadata
                FROM conversations
                WHERE session_id = ?
            """
            params = [session_id]

            if since:
                query += " AND timestamp > ?"
                params.append(since.isoformat())

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.cursor()
            cursor.execute(query, params)

            turns = []
            for row in cursor.fetchall():
                (
                    timestamp,
                    user_input,
                    ai_response,
                    context_hash,
                    actions_json,
                    metadata_json,
                ) = row
                turns.append(
                    ConversationTurn(
                        timestamp=timestamp,
                        user_input=user_input,
                        ai_response=ai_response,
                        context_hash=context_hash,
                        actions_taken=json.loads(actions_json) if actions_json else [],
                        metadata=json.loads(metadata_json) if metadata_json else {},
                    )
                )

            return list(reversed(turns))  # Return chronological order

    def learn_from_interaction(
        self,
        user_id: str,
        interaction_type: str,
        key: str,
        value: Any,
        confidence: float = 1.0,
    ):
        """Learn and store patterns from user interactions"""
        with sqlite3.connect(self.db_path) as conn:
            # Try to update existing memory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT usage_count, confidence FROM context_memory
                WHERE user_id = ? AND context_type = ? AND key = ?
            """,
                (user_id, interaction_type, key),
            )

            row = cursor.fetchone()
            if row:
                # Update existing memory with weighted average
                old_count, old_confidence = row
                new_count = old_count + 1
                # Weighted average of confidence scores
                new_confidence = (old_confidence * old_count + confidence) / new_count

                cursor.execute(
                    """
                    UPDATE context_memory
                    SET value = ?, confidence = ?, last_updated = ?, usage_count = ?
                    WHERE user_id = ? AND context_type = ? AND key = ?
                """,
                    (
                        json.dumps(value),
                        new_confidence,
                        datetime.now().isoformat(),
                        new_count,
                        user_id,
                        interaction_type,
                        key,
                    ),
                )
            else:
                # Insert new memory
                cursor.execute(
                    """
                    INSERT INTO context_memory
                    (user_id, context_type, key, value, confidence, last_updated, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        interaction_type,
                        key,
                        json.dumps(value),
                        confidence,
                        datetime.now().isoformat(),
                        1,
                    ),
                )

            conn.commit()

    def recall_context(
        self, user_id: str, context_type: str = None, min_confidence: float = 0.5
    ) -> List[ContextMemory]:
        """Recall stored context for a user"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT user_id, context_type, key, value, confidence, last_updated, usage_count
                FROM context_memory
                WHERE user_id = ? AND confidence >= ?
            """
            params = [user_id, min_confidence]

            if context_type:
                query += " AND context_type = ?"
                params.append(context_type)

            query += " ORDER BY confidence DESC, usage_count DESC, last_updated DESC"

            cursor = conn.cursor()
            cursor.execute(query, params)

            memories = []
            for row in cursor.fetchall():
                (
                    user_id,
                    ctx_type,
                    key,
                    value_json,
                    confidence,
                    last_updated,
                    usage_count,
                ) = row
                memories.append(
                    ContextMemory(
                        user_id=user_id,
                        context_type=ctx_type,
                        key=key,
                        value=json.loads(value_json),
                        confidence=confidence,
                        last_updated=last_updated,
                        usage_count=usage_count,
                    )
                )

            return memories

    def get_similar_contexts(
        self, current_context_hash: str, limit: int = 5
    ) -> List[ConversationTurn]:
        """Find conversations with similar context"""
        with sqlite3.connect(self.db_path) as conn:
            # For now, exact match on context hash
            # Could be enhanced with similarity algorithms
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT timestamp, user_input, ai_response, context_hash, actions_taken, metadata
                FROM conversations
                WHERE context_hash = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (current_context_hash, limit),
            )

            turns = []
            for row in cursor.fetchall():
                (
                    timestamp,
                    user_input,
                    ai_response,
                    context_hash,
                    actions_json,
                    metadata_json,
                ) = row
                turns.append(
                    ConversationTurn(
                        timestamp=timestamp,
                        user_input=user_input,
                        ai_response=ai_response,
                        context_hash=context_hash,
                        actions_taken=json.loads(actions_json) if actions_json else [],
                        metadata=json.loads(metadata_json) if metadata_json else {},
                    )
                )

            return turns

    def suggest_actions_from_history(
        self, current_context_hash: str, user_id: str, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Suggest actions based on historical patterns"""
        # Get similar contexts
        similar_turns = self.get_similar_contexts(current_context_hash, 10)

        # Extract successful actions
        action_frequency = {}
        for turn in similar_turns:
            for action in turn.actions_taken:
                action_type = action.get("type")
                if action_type and action.get("success", True):
                    action_frequency[action_type] = (
                        action_frequency.get(action_type, 0) + 1
                    )

        # Get user preferences
        user_memories = self.recall_context(user_id, "preference")
        preferred_actions = set()
        for memory in user_memories:
            if memory.key == "preferred_actions" and memory.confidence > 0.7:
                preferred_actions.update(memory.value)

        # Combine frequency and preferences
        suggestions = []
        for action_type, frequency in sorted(
            action_frequency.items(), key=lambda x: x[1], reverse=True
        )[:limit]:
            confidence = min(frequency / len(similar_turns), 1.0)
            if action_type in preferred_actions:
                confidence += 0.2

            suggestions.append(
                {
                    "action_type": action_type,
                    "confidence": confidence,
                    "frequency": frequency,
                    "reason": f"Used {frequency} times in similar contexts",
                }
            )

        return suggestions[:limit]

    def cleanup_old_conversations(self, days: int = 30):
        """Clean up old conversation data"""
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                DELETE FROM conversations
                WHERE timestamp < ?
            """,
                (cutoff.isoformat(),),
            )

            # Keep context memory longer (90 days)
            context_cutoff = datetime.now() - timedelta(days=90)
            conn.execute(
                """
                DELETE FROM context_memory
                WHERE last_updated < ? AND usage_count < 3
            """,
                (context_cutoff.isoformat(),),
            )

            conn.commit()

    def export_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """Export conversation history for analysis or backup"""
        turns = self.get_conversation_history(session_id, limit=1000)

        return {
            "session_id": session_id,
            "export_timestamp": datetime.now().isoformat(),
            "conversation_count": len(turns),
            "conversations": [turn.to_dict() for turn in turns],
        }
