"""Workflow Context Engineering

Provides structured, AI-optimized context about current workflow state,
related tasks, schedule, and user priorities.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.mcp_manager import MCPManager
from core.scheduler import Scheduler
from core.workflow_engine import WorkflowEngine, WorkflowStatus


@dataclass
class ContextSnapshot:
    """Immutable snapshot of workflow context at a point in time"""

    timestamp: str
    current_workflow: Optional[Dict[str, Any]]
    active_workflows: List[Dict[str, Any]]
    scheduled_tasks: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    user_focus: Optional[str]
    priority_insights: Dict[str, Any]
    context_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        """Create from dictionary"""
        return cls(**data)


class WorkflowContextEngine:
    """Manages workflow context for AI providers"""

    def __init__(
        self, workflow_engine: WorkflowEngine = None, scheduler: Scheduler = None
    ):
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.scheduler = scheduler or Scheduler()
        self.mcp_manager = MCPManager()

        # Context cache
        self._context_cache: Optional[ContextSnapshot] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # Cache for 5 minutes

        # Context storage - user-specific context should be gitignored
        self.context_dir = Path(".conductor/context")
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def get_current_context(self, refresh: bool = False) -> ContextSnapshot:
        """Get current workflow context snapshot"""
        now = datetime.now()

        # Use cache if valid and not forced refresh
        if (
            not refresh
            and self._context_cache
            and self._cache_expiry
            and now < self._cache_expiry
        ):
            return self._context_cache

        # Generate fresh context
        context = self._generate_context()

        # Update cache
        self._context_cache = context
        self._cache_expiry = now + self._cache_duration

        # Persist context
        self._save_context(context)

        return context

    def _generate_context(self) -> ContextSnapshot:
        """Generate fresh context snapshot"""
        now = datetime.now()

        # Get current workflow (most recent active/in-progress)
        current_workflow = self._get_current_workflow()

        # Get active workflows
        active_workflows = self._get_active_workflows()

        # Get today's scheduled tasks
        scheduled_tasks = self._get_scheduled_tasks()

        # Get recent activity
        recent_activity = self._get_recent_activity()

        # Determine user focus
        user_focus = self._determine_user_focus(current_workflow, active_workflows)

        # Generate priority insights
        priority_insights = self._generate_priority_insights(
            active_workflows, scheduled_tasks
        )

        # Create context hash for change detection
        context_data = {
            "current_workflow": current_workflow,
            "active_workflows": active_workflows,
            "scheduled_tasks": scheduled_tasks,
            "user_focus": user_focus,
        }
        context_hash = hashlib.md5(
            json.dumps(context_data, sort_keys=True).encode(), usedforsecurity=False
        ).hexdigest()

        return ContextSnapshot(
            timestamp=now.isoformat(),
            current_workflow=current_workflow,
            active_workflows=active_workflows,
            scheduled_tasks=scheduled_tasks,
            recent_activity=recent_activity,
            user_focus=user_focus,
            priority_insights=priority_insights,
            context_hash=context_hash,
        )

    def _get_current_workflow(self) -> Optional[Dict[str, Any]]:
        """Get the workflow user is currently focused on"""
        try:
            # Get most recent active or in-progress workflow
            workflows = self.workflow_engine.list_workflows()

            # Priority order: in_progress > active > pending (by recency)
            current = None
            for workflow in sorted(
                workflows, key=lambda w: w.get("updated_at", ""), reverse=True
            ):
                if workflow.get("status") == WorkflowStatus.IN_PROGRESS.value:
                    current = workflow
                    break
                elif (
                    workflow.get("status") == WorkflowStatus.ACTIVE.value
                    and not current
                ):
                    current = workflow
                elif (
                    workflow.get("status") == WorkflowStatus.PENDING.value
                    and not current
                ):
                    current = workflow

            if current:
                # Get detailed workflow information
                workflow_detail = self.workflow_engine.get_workflow(current["id"])
                if workflow_detail:
                    return workflow_detail

        except Exception as e:
            # Graceful fallback
            pass

        return None

    def _get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        try:
            workflows = self.workflow_engine.list_workflows()
            active_statuses = {
                WorkflowStatus.ACTIVE.value,
                WorkflowStatus.IN_PROGRESS.value,
                WorkflowStatus.PENDING.value,
            }

            active_workflows = []
            for workflow in workflows:
                if workflow.get("status") in active_statuses:
                    # Get summary version (not full detail to keep context manageable)
                    active_workflows.append(
                        {
                            "id": workflow.get("id"),
                            "title": workflow.get("title"),
                            "status": workflow.get("status"),
                            "priority": workflow.get("priority"),
                            "due_date": workflow.get("due_date"),
                            "progress": self._calculate_progress(workflow),
                            "updated_at": workflow.get("updated_at"),
                        }
                    )

            return sorted(
                active_workflows,
                key=lambda w: (
                    w.get("priority", 3),  # Higher priority first
                    w.get("due_date", "9999-12-31"),  # Earlier due date first
                ),
            )

        except Exception as e:
            return []

    def _get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Get today's scheduled tasks and near-term reminders"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)

            scheduled_tasks = []

            # Get today's reminders
            today_reminders = self.scheduler.get_due_reminders()
            for reminder in today_reminders:
                scheduled_tasks.append(
                    {
                        "type": "reminder",
                        "time": reminder.get("scheduled_for"),
                        "description": reminder.get("message"),
                        "priority": reminder.get("priority", "normal"),
                        "id": reminder.get("id"),
                    }
                )

            # Get workflow due dates
            active_workflows = self._get_active_workflows()
            for workflow in active_workflows:
                due_date_str = workflow.get("due_date")
                if due_date_str:
                    try:
                        due_date = datetime.fromisoformat(
                            due_date_str.replace("Z", "+00:00")
                        ).date()
                        if due_date <= tomorrow:
                            scheduled_tasks.append(
                                {
                                    "type": "workflow_due",
                                    "time": due_date_str,
                                    "description": f"Workflow due: {workflow.get('title')}",
                                    "priority": workflow.get("priority", "normal"),
                                    "workflow_id": workflow.get("id"),
                                }
                            )
                    except (ValueError, AttributeError):
                        pass

            return sorted(scheduled_tasks, key=lambda t: t.get("time", ""))

        except Exception as e:
            return []

    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent workflow activity"""
        try:
            # This would ideally come from an activity log
            # For now, synthesize from workflow states
            activities = []

            workflows = self.workflow_engine.list_workflows()
            for workflow in workflows[-10:]:  # Last 10 workflows
                activities.append(
                    {
                        "timestamp": workflow.get(
                            "updated_at", workflow.get("created_at")
                        ),
                        "type": "workflow_updated",
                        "description": f"Updated workflow: {workflow.get('title')}",
                        "workflow_id": workflow.get("id"),
                    }
                )

            return sorted(
                activities, key=lambda a: a.get("timestamp", ""), reverse=True
            )[:5]

        except Exception as e:
            return []

    def _determine_user_focus(
        self, current_workflow: Optional[Dict], active_workflows: List[Dict]
    ) -> Optional[str]:
        """Determine what the user should focus on"""
        if (
            current_workflow
            and current_workflow.get("status") == WorkflowStatus.IN_PROGRESS.value
        ):
            return f"Currently working on: {current_workflow.get('title')}"

        # Check for high priority pending items
        high_priority = [w for w in active_workflows if w.get("priority", 3) <= 2]
        if high_priority:
            return f"High priority: {high_priority[0].get('title')}"

        # Check for due items
        today = datetime.now().date().isoformat()
        due_soon = [
            w for w in active_workflows if w.get("due_date", "9999-12-31") <= today
        ]
        if due_soon:
            return f"Due today: {due_soon[0].get('title')}"

        return None

    def _generate_priority_insights(
        self, workflows: List[Dict], tasks: List[Dict]
    ) -> Dict[str, Any]:
        """Generate insights about priorities and recommendations"""
        insights = {
            "total_active_workflows": len(workflows),
            "high_priority_count": len(
                [w for w in workflows if w.get("priority", 3) <= 2]
            ),
            "overdue_count": 0,
            "recommendations": [],
        }

        today = datetime.now().date().isoformat()

        # Count overdue items
        for workflow in workflows:
            due_date = workflow.get("due_date", "9999-12-31")
            if due_date < today:
                insights["overdue_count"] += 1

        # Generate recommendations
        if insights["overdue_count"] > 0:
            insights["recommendations"].append(
                "You have overdue workflows that need attention"
            )

        if insights["high_priority_count"] > 3:
            insights["recommendations"].append(
                "Consider focusing on high-priority items to reduce workload"
            )

        if len(workflows) > 10:
            insights["recommendations"].append(
                "You have many active workflows. Consider consolidating or completing some"
            )

        return insights

    def _calculate_progress(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate workflow progress"""
        actions = workflow.get("actions", [])
        if not actions:
            return {"completed": 0, "total": 0, "percentage": 0}

        completed = sum(1 for action in actions if action.get("completed", False))
        total = len(actions)
        percentage = int((completed / total) * 100) if total > 0 else 0

        return {"completed": completed, "total": total, "percentage": percentage}

    def _save_context(self, context: ContextSnapshot):
        """Save context snapshot to disk"""
        try:
            context_file = (
                self.context_dir / f"context_{context.timestamp.replace(':', '-')}.json"
            )
            with open(context_file, "w") as f:
                json.dump(context.to_dict(), f, indent=2)

            # Keep only recent context files (last 24 hours)
            self._cleanup_old_contexts()

        except Exception as e:
            # Graceful failure - don't break the system
            pass

    def _cleanup_old_contexts(self):
        """Remove old context files"""
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            for context_file in self.context_dir.glob("context_*.json"):
                # Extract timestamp from filename
                timestamp_str = context_file.stem.replace("context_", "").replace(
                    "-", ":"
                )
                try:
                    file_time = datetime.fromisoformat(timestamp_str.split(".")[0])
                    if file_time < cutoff:
                        context_file.unlink()
                except (ValueError, IndexError):
                    pass
        except Exception as e:
            pass

    def get_ai_optimized_context(
        self, provider_name: str = "default"
    ) -> Dict[str, Any]:
        """Get context optimized for specific AI provider"""
        context = self.get_current_context()

        # Base context
        ai_context = {
            "current_workflow": context.current_workflow,
            "related_workflows": context.active_workflows[:5],  # Limit for context size
            "schedule": context.scheduled_tasks[:10],  # Today + near term
            "user_focus": context.user_focus,
            "insights": context.priority_insights,
            "timestamp": context.timestamp,
        }

        # Provider-specific optimizations
        if provider_name == "claude":
            # Claude handles more detailed context well
            ai_context["recent_activity"] = context.recent_activity
        elif provider_name == "openai":
            # GPT models prefer more concise context
            ai_context["related_workflows"] = context.active_workflows[:3]
            ai_context["schedule"] = context.scheduled_tasks[:5]

        return ai_context
