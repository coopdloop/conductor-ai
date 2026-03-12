import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class WorkflowStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(Enum):
    JIRA_UPDATE = "jira_update"
    CONFLUENCE_PUBLISH = "confluence_publish"
    GITHUB_COMMIT = "github_commit"
    SLACK_MESSAGE = "slack_message"
    EMAIL_SEND = "email_send"
    REMINDER = "reminder"
    FOLLOW_UP = "follow_up"
    CUSTOM_COMMAND = "custom_command"


@dataclass
class WorkflowAction:
    """Represents a single action within a workflow."""

    id: str
    type: ActionType
    description: str
    parameters: Dict[str, Any]
    completed: bool = False
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WorkflowReminder:
    """Represents a reminder/scheduled item."""

    id: str
    workflow_id: str
    message: str
    scheduled_for: str
    completed: bool = False
    recurring: Optional[str] = None  # daily, weekly, monthly


@dataclass
class Workflow:
    """Represents a complete workflow/skill."""

    id: str
    title: str
    description: str
    status: WorkflowStatus
    priority: int  # 1-5, where 1 is highest
    created_at: str
    updated_at: str
    due_date: Optional[str] = None
    tags: List[str] = None
    actions: List[WorkflowAction] = None
    reminders: List[WorkflowReminder] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.actions is None:
            self.actions = []
        if self.reminders is None:
            self.reminders = []
        if self.metadata is None:
            self.metadata = {}


class WorkflowEngine:
    """Manages and executes workflows/skills."""

    def __init__(self, workflows_dir: Path = None):
        # User-generated workflows should go to gitignored directory
        self.workflows_dir = workflows_dir or Path("user_workflows")
        self.workflows_dir.mkdir(exist_ok=True)

        self.state_file = self.workflows_dir / ".workflow_state.json"
        self.workflows: Dict[str, Workflow] = {}
        self.load_workflows()

    def create_workflow_from_markdown(
        self, markdown_content: str, title: str = None
    ) -> Workflow:
        """Parse a markdown file and create a workflow."""

        # Extract YAML frontmatter if present
        frontmatter = {}
        content = markdown_content

        if markdown_content.startswith("---\n"):
            parts = markdown_content.split("---\n", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    content = parts[2]
                except:
                    pass

        # Extract title from frontmatter or first H1
        if not title:
            title = frontmatter.get("title")
            if not title:
                h1_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
                if h1_match:
                    title = h1_match.group(1).strip()
                else:
                    title = "Untitled Workflow"

        # Generate workflow ID
        workflow_id = self._generate_workflow_id(title)

        # Parse actions from markdown
        actions = self._parse_actions_from_markdown(content)

        # Parse reminders from markdown
        reminders = self._parse_reminders_from_markdown(content, workflow_id)

        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=frontmatter.get(
                "description", self._extract_description(content)
            ),
            status=WorkflowStatus(frontmatter.get("status", "pending")),
            priority=frontmatter.get("priority", 3),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            due_date=frontmatter.get("due_date"),
            tags=frontmatter.get("tags", []),
            actions=actions,
            reminders=reminders,
            metadata=frontmatter,
        )

        self.workflows[workflow_id] = workflow
        self.save_workflows()
        return workflow

    def _parse_actions_from_markdown(self, content: str) -> List[WorkflowAction]:
        """Parse action items from markdown content."""
        actions = []
        action_id = 1

        # Find action patterns in markdown
        patterns = {
            ActionType.JIRA_UPDATE: r"(?:update|comment on|close)\s+(?:ticket|issue|task)\s+([A-Z]+-\d+)",
            ActionType.FOLLOW_UP: r"follow[- ]?up with\s+(.+?)(?:\s+in\s+(.+?))?(?:\.|$)",
            ActionType.REMINDER: r"remind\s+me\s+(.+?)(?:\s+(?:at|on)\s+(.+?))?(?:\.|$)",
            ActionType.SLACK_MESSAGE: r"(?:send|message)\s+(.+?)\s+(?:on|in)\s+slack",
            ActionType.CONFLUENCE_PUBLISH: r"(?:publish|update)\s+(.+?)\s+(?:to|on|in)\s+confluence",
            ActionType.GITHUB_COMMIT: r"(?:commit|push|update)\s+(.+?)\s+(?:to|on)\s+github",
        }

        # Search for task lists and bullet points
        task_patterns = [
            r"- \[ \]\s*(.+)",  # Unchecked checkboxes
            r"- (.+?)(?:\n|$)",  # Regular bullet points
            r"\d+\.\s+(.+?)(?:\n|$)",  # Numbered lists
        ]

        for pattern in task_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                task_text = match.group(1).strip()

                # Determine action type based on content
                action_type = ActionType.CUSTOM_COMMAND
                parameters = {"description": task_text}

                # Check against specific action patterns
                for act_type, act_pattern in patterns.items():
                    if re.search(act_pattern, task_text, re.IGNORECASE):
                        action_type = act_type
                        match_obj = re.search(act_pattern, task_text, re.IGNORECASE)
                        if match_obj:
                            parameters = {
                                "target": match_obj.group(1).strip(),
                                "description": task_text,
                            }
                            if len(match_obj.groups()) > 1 and match_obj.group(2):
                                parameters["timing"] = match_obj.group(2).strip()
                        break

                actions.append(
                    WorkflowAction(
                        id=f"action_{action_id}",
                        type=action_type,
                        description=task_text,
                        parameters=parameters,
                    )
                )
                action_id += 1

        return actions

    def _parse_reminders_from_markdown(
        self, content: str, workflow_id: str
    ) -> List[WorkflowReminder]:
        """Parse reminders from markdown content."""
        reminders = []
        reminder_id = 1

        # Pattern for reminder extraction
        reminder_patterns = [
            r"remind\s+me\s+(.+?)\s+(?:at|on)\s+(.+?)(?:\.|$)",
            r"(?:reminder|alert|notify):\s*(.+?)(?:\s+(?:at|on)\s+(.+?))?(?:\.|$)",
            r"follow[- ]?up\s+(.+?)\s+(?:tomorrow|next\s+week|in\s+\d+\s+days?)",
        ]

        for pattern in reminder_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                message = match.group(1).strip()
                timing = (
                    match.group(2).strip()
                    if len(match.groups()) > 1 and match.group(2)
                    else "tomorrow 8am"
                )

                # Parse timing to datetime
                scheduled_time = self._parse_reminder_time(timing)

                reminders.append(
                    WorkflowReminder(
                        id=f"reminder_{reminder_id}",
                        workflow_id=workflow_id,
                        message=message,
                        scheduled_for=scheduled_time,
                        recurring=self._extract_recurring_pattern(timing),
                    )
                )
                reminder_id += 1

        return reminders

    def _parse_reminder_time(self, timing_text: str) -> str:
        """Parse natural language timing into ISO datetime."""
        now = datetime.now()

        # Simple parsing - could be enhanced with more sophisticated NLP
        if "tomorrow" in timing_text.lower():
            target_date = now + timedelta(days=1)
            # Extract time if specified
            time_match = re.search(
                r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", timing_text.lower()
            )
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2) or 0)
                if time_match.group(3) == "pm" and hour != 12:
                    hour += 12
                elif time_match.group(3) == "am" and hour == 12:
                    hour = 0
                target_date = target_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            else:
                target_date = target_date.replace(
                    hour=8, minute=0, second=0, microsecond=0
                )
        else:
            # Default to tomorrow 8am
            target_date = now + timedelta(days=1)
            target_date = target_date.replace(hour=8, minute=0, second=0, microsecond=0)

        return target_date.isoformat()

    def _extract_recurring_pattern(self, timing_text: str) -> Optional[str]:
        """Extract recurring pattern from timing text."""
        if "daily" in timing_text.lower():
            return "daily"
        elif "weekly" in timing_text.lower():
            return "weekly"
        elif "monthly" in timing_text.lower():
            return "monthly"
        return None

    def get_active_workflows(self) -> List[Workflow]:
        """Get all active workflows."""
        return [w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE]

    def get_pending_workflows(self) -> List[Workflow]:
        """Get all pending workflows."""
        return [
            w for w in self.workflows.values() if w.status == WorkflowStatus.PENDING
        ]

    def get_today_priorities(self) -> List[Workflow]:
        """Get high priority workflows for today."""
        today = datetime.now().date()
        priorities = []

        for workflow in self.workflows.values():
            if workflow.status in [WorkflowStatus.ACTIVE, WorkflowStatus.PENDING]:
                # Check if high priority
                if workflow.priority <= 2:
                    priorities.append(workflow)
                # Check if due today
                elif workflow.due_date:
                    try:
                        due_date = datetime.fromisoformat(workflow.due_date).date()
                        if due_date <= today:
                            priorities.append(workflow)
                    except:
                        pass

        return sorted(priorities, key=lambda w: w.priority)

    def get_due_reminders(self) -> List[WorkflowReminder]:
        """Get reminders that are due."""
        now = datetime.now()
        due_reminders = []

        for workflow in self.workflows.values():
            for reminder in workflow.reminders:
                if not reminder.completed:
                    try:
                        due_time = datetime.fromisoformat(reminder.scheduled_for)
                        if due_time <= now:
                            due_reminders.append(reminder)
                    except:
                        pass

        return due_reminders

    def update_workflow_status(self, workflow_id: str, status: WorkflowStatus) -> bool:
        """Update workflow status."""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = status
            self.workflows[workflow_id].updated_at = datetime.now().isoformat()
            self.save_workflows()
            return True
        return False

    def complete_action(self, workflow_id: str, action_id: str) -> bool:
        """Mark an action as completed."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            for action in workflow.actions:
                if action.id == action_id:
                    action.completed = True
                    action.completed_at = datetime.now().isoformat()
                    workflow.updated_at = datetime.now().isoformat()

                    # Check if all actions completed
                    if all(action.completed for action in workflow.actions):
                        workflow.status = WorkflowStatus.COMPLETED

                    self.save_workflows()
                    return True
        return False

    def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        for workflow in self.workflows.values():
            for reminder in workflow.reminders:
                if reminder.id == reminder_id:
                    reminder.completed = True
                    self.save_workflows()
                    return True
        return False

    def save_workflow_to_file(self, workflow_id: str) -> bool:
        """Save workflow to a markdown file."""
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]

        # Create frontmatter
        frontmatter = {
            "title": workflow.title,
            "description": workflow.description,
            "status": workflow.status.value,
            "priority": workflow.priority,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "tags": workflow.tags,
        }
        if workflow.due_date:
            frontmatter["due_date"] = workflow.due_date

        # Create markdown content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False)
        content += "---\n\n"
        content += f"# {workflow.title}\n\n"
        content += f"{workflow.description}\n\n"

        if workflow.actions:
            content += "## Actions\n\n"
            for action in workflow.actions:
                check = "x" if action.completed else " "
                content += f"- [{check}] {action.description}\n"
            content += "\n"

        if workflow.reminders:
            content += "## Reminders\n\n"
            for reminder in workflow.reminders:
                status = (
                    "(completed)"
                    if reminder.completed
                    else f"(due: {reminder.scheduled_for})"
                )
                content += f"- {reminder.message} {status}\n"

        # Save to file
        filename = f"{workflow.id}.md"
        filepath = self.workflows_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    def load_workflows(self):
        """Load workflows from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for workflow_data in data.get("workflows", []):
                    # Convert back to proper types
                    workflow_data["status"] = WorkflowStatus(workflow_data["status"])

                    # Convert actions
                    actions = []
                    for action_data in workflow_data.get("actions", []):
                        action_data["type"] = ActionType(action_data["type"])
                        actions.append(WorkflowAction(**action_data))
                    workflow_data["actions"] = actions

                    # Convert reminders
                    reminders = []
                    for reminder_data in workflow_data.get("reminders", []):
                        reminders.append(WorkflowReminder(**reminder_data))
                    workflow_data["reminders"] = reminders

                    workflow = Workflow(**workflow_data)
                    self.workflows[workflow.id] = workflow
            except Exception as e:
                print(f"Error loading workflows: {e}")

    def save_workflows(self):
        """Save workflows to state file."""
        data = {"workflows": [], "last_updated": datetime.now().isoformat()}

        for workflow in self.workflows.values():
            workflow_dict = asdict(workflow)
            # Convert enums to strings
            workflow_dict["status"] = workflow.status.value
            for action in workflow_dict["actions"]:
                action["type"] = action["type"].value
            data["workflows"].append(workflow_dict)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _generate_workflow_id(self, title: str) -> str:
        """Generate a unique workflow ID from title."""
        base_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        base_id = base_id[:30]  # Limit length

        # Ensure uniqueness
        counter = 1
        workflow_id = base_id
        while workflow_id in self.workflows:
            workflow_id = f"{base_id}_{counter}"
            counter += 1

        return workflow_id

    def _extract_description(self, content: str) -> str:
        """Extract description from markdown content."""
        # Get first paragraph after title
        lines = content.split("\n")
        description_lines = []
        found_title = False

        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                found_title = True
                continue
            if found_title and line:
                if line.startswith("#"):  # Another heading
                    break
                description_lines.append(line)
            elif found_title and not line and description_lines:
                break  # End of first paragraph

        return " ".join(description_lines) or "No description available"
