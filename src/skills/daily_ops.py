"""Daily Operations Skills

AI-callable skills for daily work management, team coordination, and routine operations.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import Skill, SkillExecutionResult, SkillParameter, SkillStatus


class StandupPrepSkill(Skill):
    """Prepare for daily standup meetings by analyzing current work state"""

    @property
    def name(self) -> str:
        return "standup_prep"

    @property
    def description(self) -> str:
        return "Analyze current workflows and prepare talking points for daily standup meetings, including yesterday's progress, today's plans, and blockers"

    @property
    def category(self) -> str:
        return "daily_ops"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="meeting_time",
                type="string",
                description="Standup meeting time (e.g., '9:00 AM', 'tomorrow 9am')",
                default="today 9am",
            ),
            SkillParameter(
                name="team_name",
                type="string",
                description="Team or project name",
                required=False,
            ),
            SkillParameter(
                name="include_metrics",
                type="boolean",
                description="Include productivity metrics in summary",
                default=False,
            ),
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None,
    ) -> SkillExecutionResult:
        """Execute standup preparation"""
        start_time = datetime.now()

        try:
            # Analyze current workflow state
            active_workflows = context.get("active_workflows", [])
            current_workflow = context.get("current_workflow")
            schedule = context.get("schedule", [])

            # Generate standup content
            standup_content = self._generate_standup_summary(
                active_workflows, current_workflow, schedule, parameters
            )

            # Create document for standup notes
            if orchestrator and hasattr(orchestrator, "doc_processor"):
                doc_result = orchestrator.doc_processor.create_document(
                    title=f"Standup Prep - {datetime.now().strftime('%Y-%m-%d')}",
                    content=standup_content,
                    metadata={
                        "type": "standup_prep",
                        "team": parameters.get("team_name", "Default"),
                        "created_by": "ai_standup_skill",
                    },
                )
                doc_id = doc_result.get("doc_id")
            else:
                doc_id = f"standup_{datetime.now().strftime('%Y%m%d')}"

            # Schedule reminder for meeting
            if orchestrator and hasattr(orchestrator, "scheduler"):
                # Parse meeting time and create reminder 15 minutes before
                meeting_time = parameters["meeting_time"]
                try:
                    if "today" in meeting_time.lower():
                        base_time = datetime.now().replace(
                            hour=9, minute=0, second=0, microsecond=0
                        )
                    elif "tomorrow" in meeting_time.lower():
                        base_time = (datetime.now() + timedelta(days=1)).replace(
                            hour=9, minute=0, second=0, microsecond=0
                        )
                    else:
                        base_time = datetime.now() + timedelta(
                            hours=1
                        )  # Default fallback

                    reminder_time = base_time - timedelta(minutes=15)
                    orchestrator.scheduler.schedule_reminder(
                        f"Standup meeting in 15 minutes - Review prep notes",
                        reminder_time.isoformat(),
                        metadata={"doc_id": doc_id, "type": "standup_reminder"},
                    )
                except:
                    pass  # Graceful fallback

            execution_time = (datetime.now() - start_time).total_seconds()

            # Extract key metrics for output
            total_workflows = len(active_workflows)
            in_progress_count = len(
                [w for w in active_workflows if w.get("status") == "in_progress"]
            )
            completed_actions = self._count_completed_actions(active_workflows)

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "doc_id": doc_id,
                    "standup_summary": standup_content,
                    "total_workflows": total_workflows,
                    "in_progress_count": in_progress_count,
                    "completed_actions": completed_actions,
                    "meeting_time": parameters["meeting_time"],
                },
                execution_time=execution_time,
                metadata={
                    "team": parameters.get("team_name"),
                    "include_metrics": parameters["include_metrics"],
                },
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=execution_time,
                error=str(e),
            )

    def _generate_standup_summary(
        self,
        active_workflows: List[Dict],
        current_workflow: Dict,
        schedule: List[Dict],
        parameters: Dict[str, Any],
    ) -> str:
        """Generate standup summary content"""
        content_parts = [
            f"# Standup Prep - {datetime.now().strftime('%A, %B %d, %Y')}",
            "",
            f"**Team:** {parameters.get('team_name', 'Development Team')}",
            f"**Meeting Time:** {parameters['meeting_time']}",
            "",
        ]

        # Yesterday's Progress
        content_parts.extend(["## Yesterday's Progress", ""])

        if current_workflow:
            progress = current_workflow.get("progress", {})
            completed = progress.get("completed", 0)
            total = progress.get("total", 0)

            content_parts.extend(
                [
                    f"**Main Focus:** {current_workflow.get('title', 'Current Work')}",
                    f"- Progress: {completed}/{total} actions completed ({progress.get('percentage', 0)}%)",
                    f"- Status: {current_workflow.get('status', 'unknown').replace('_', ' ').title()}",
                    "",
                ]
            )

        # Active work summary
        if active_workflows:
            high_priority = [w for w in active_workflows if w.get("priority", 5) <= 2]
            if high_priority:
                content_parts.extend(["**High Priority Items:**", ""])
                for workflow in high_priority[:3]:  # Limit to top 3
                    progress = workflow.get("progress", {})
                    content_parts.append(
                        f"- {workflow.get('title')}: {progress.get('completed', 0)}/{progress.get('total', 0)} complete"
                    )

        content_parts.extend(["", "## Today's Plan", ""])

        # Today's focus
        if current_workflow and current_workflow.get("status") == "in_progress":
            content_parts.extend(
                [
                    f"**Primary Focus:** Continue {current_workflow.get('title')}",
                    f"- Next actions to complete",
                    "",
                ]
            )

        # Scheduled items
        today_items = [
            item for item in schedule if self._is_today(item.get("time", ""))
        ]
        if today_items:
            content_parts.extend(["**Scheduled Items:**", ""])
            for item in today_items[:5]:  # Limit to 5 items
                time_str = (
                    item.get("time", "").split("T")[-1][:5]
                    if "T" in item.get("time", "")
                    else "TBD"
                )
                content_parts.append(
                    f"- {time_str}: {item.get('description', 'Scheduled task')}"
                )
            content_parts.append("")

        # Blockers and needs
        content_parts.extend(
            [
                "## Blockers & Support Needed",
                "",
                "*Note any blockers or support needed from team members*",
                "",
                "- [ ] No current blockers",
                "- [ ] Need review on: [specify]",
                "- [ ] Waiting for: [specify]",
                "",
            ]
        )

        # Metrics (if requested)
        if parameters.get("include_metrics"):
            total_workflows = len(active_workflows)
            completed_actions = self._count_completed_actions(active_workflows)

            content_parts.extend(
                [
                    "## Metrics",
                    "",
                    f"- **Active Workflows:** {total_workflows}",
                    f"- **Completed Actions (this week):** {completed_actions}",
                    f"- **Current Velocity:** {self._estimate_velocity(active_workflows)} actions/day",
                    "",
                ]
            )

        # Notes section
        content_parts.extend(
            [
                "## Notes",
                "",
                "*Space for additional notes or updates during the standup*",
                "",
            ]
        )

        return "\n".join(content_parts)

    def _is_today(self, time_str: str) -> bool:
        """Check if a time string represents today"""
        today = datetime.now().date()
        try:
            if "T" in time_str:
                date_part = time_str.split("T")[0]
                item_date = datetime.fromisoformat(date_part).date()
                return item_date == today
        except:
            pass
        return False

    def _count_completed_actions(self, workflows: List[Dict]) -> int:
        """Count completed actions across workflows"""
        total = 0
        for workflow in workflows:
            progress = workflow.get("progress", {})
            total += progress.get("completed", 0)
        return total

    def _estimate_velocity(self, workflows: List[Dict]) -> float:
        """Estimate actions completed per day"""
        total_actions = self._count_completed_actions(workflows)
        # Simple estimation - could be enhanced with historical data
        return round(total_actions / 7, 1)  # Assume work is spread over a week


class FollowUpManagementSkill(Skill):
    """Manage follow-ups with team members and stakeholders"""

    @property
    def name(self) -> str:
        return "follow_up_management"

    @property
    def description(self) -> str:
        return "Create and manage follow-up actions with team members, stakeholders, and external parties based on current workflow needs"

    @property
    def category(self) -> str:
        return "daily_ops"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="follow_up_type",
                type="string",
                description="Type of follow-up needed",
                options=[
                    "status_check",
                    "approval_request",
                    "information_gathering",
                    "coordination",
                    "escalation",
                ],
            ),
            SkillParameter(
                name="stakeholder",
                type="string",
                description="Person or team to follow up with",
            ),
            SkillParameter(
                name="context",
                type="string",
                description="Context or reason for follow-up",
            ),
            SkillParameter(
                name="urgency",
                type="string",
                description="Urgency level",
                options=["low", "normal", "high", "urgent"],
                default="normal",
            ),
            SkillParameter(
                name="follow_up_date",
                type="string",
                description="When to follow up (e.g., 'tomorrow', '2024-01-15', 'next week')",
                default="tomorrow",
            ),
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None,
    ) -> SkillExecutionResult:
        """Execute follow-up management"""
        start_time = datetime.now()

        try:
            follow_up_type = parameters["follow_up_type"]
            stakeholder = parameters["stakeholder"]
            context_info = parameters["context"]
            urgency = parameters["urgency"]

            # Create follow-up workflow
            workflow_content = self._generate_follow_up_workflow(
                follow_up_type, stakeholder, context_info, urgency, parameters
            )

            # Create workflow
            if orchestrator and hasattr(orchestrator, "workflow_engine"):
                workflow_result = orchestrator.workflow_engine.create_workflow(
                    title=f"Follow-up: {follow_up_type.replace('_', ' ').title()} with {stakeholder}",
                    content=workflow_content,
                    priority=self._urgency_to_priority(urgency),
                    metadata={
                        "type": "follow_up",
                        "stakeholder": stakeholder,
                        "follow_up_type": follow_up_type,
                        "urgency": urgency,
                    },
                )
                workflow_id = workflow_result.get("workflow_id")
            else:
                workflow_id = f"follow_up_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Schedule follow-up reminder
            if orchestrator and hasattr(orchestrator, "scheduler"):
                follow_up_time = self._parse_follow_up_time(
                    parameters["follow_up_date"]
                )
                orchestrator.scheduler.schedule_reminder(
                    f"Follow up with {stakeholder}: {context_info}",
                    follow_up_time.isoformat(),
                    metadata={
                        "workflow_id": workflow_id,
                        "stakeholder": stakeholder,
                        "type": "follow_up_reminder",
                    },
                )

                # Schedule escalation reminder for high urgency items
                if urgency in ["high", "urgent"]:
                    escalation_time = follow_up_time + timedelta(days=1)
                    orchestrator.scheduler.schedule_reminder(
                        f"Escalation check: {context_info}",
                        escalation_time.isoformat(),
                        metadata={
                            "workflow_id": workflow_id,
                            "type": "escalation_reminder",
                        },
                    )

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "workflow_id": workflow_id,
                    "stakeholder": stakeholder,
                    "follow_up_type": follow_up_type,
                    "urgency": urgency,
                    "scheduled_time": parameters["follow_up_date"],
                    "escalation_scheduled": urgency in ["high", "urgent"],
                },
                execution_time=execution_time,
                metadata={"follow_up_type": follow_up_type, "urgency": urgency},
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=execution_time,
                error=str(e),
            )

    def _generate_follow_up_workflow(
        self,
        follow_up_type: str,
        stakeholder: str,
        context: str,
        urgency: str,
        parameters: Dict[str, Any],
    ) -> str:
        """Generate follow-up workflow content"""
        content_parts = [
            f"# Follow-up: {follow_up_type.replace('_', ' ').title()}",
            "",
            "## Follow-up Details",
            f"- **Stakeholder:** {stakeholder}",
            f"- **Type:** {follow_up_type.replace('_', ' ').title()}",
            f"- **Urgency:** {urgency}",
            f"- **Context:** {context}",
            f"- **Scheduled:** {parameters['follow_up_date']}",
            "",
            "## Actions",
            "",
        ]

        # Customize actions based on follow-up type
        if follow_up_type == "status_check":
            content_parts.extend(
                [
                    "- [ ] **Prepare Status Request**",
                    "  - Review what information is needed",
                    "  - Prepare specific questions",
                    "  - Gather current context",
                    "",
                    "- [ ] **Contact Stakeholder**",
                    f"  - Reach out to {stakeholder}",
                    "  - Request status update",
                    "  - Provide necessary context",
                    "",
                    "- [ ] **Document Response**",
                    "  - Record status information received",
                    "  - Note any concerns or blockers",
                    "  - Update relevant workflows or documentation",
                    "",
                ]
            )

        elif follow_up_type == "approval_request":
            content_parts.extend(
                [
                    "- [ ] **Prepare Approval Request**",
                    "  - Compile all necessary information",
                    "  - Prepare justification or business case",
                    "  - Include relevant documentation",
                    "",
                    "- [ ] **Submit Request**",
                    f"  - Send approval request to {stakeholder}",
                    "  - Provide all supporting materials",
                    "  - Set clear expectations for timeline",
                    "",
                    "- [ ] **Track Response**",
                    "  - Monitor for approval response",
                    "  - Follow up if no response received",
                    "  - Document approval decision and conditions",
                    "",
                ]
            )

        elif follow_up_type == "information_gathering":
            content_parts.extend(
                [
                    "- [ ] **Prepare Information Request**",
                    "  - Define specific information needed",
                    "  - Prepare clear questions",
                    "  - Explain why information is needed",
                    "",
                    "- [ ] **Request Information**",
                    f"  - Contact {stakeholder} for information",
                    "  - Provide context and deadline",
                    "  - Offer to schedule a meeting if needed",
                    "",
                    "- [ ] **Process Information**",
                    "  - Review information received",
                    "  - Validate and verify as needed",
                    "  - Update workflows or documentation",
                    "",
                ]
            )

        else:  # Default actions for other types
            content_parts.extend(
                [
                    "- [ ] **Prepare Communication**",
                    "  - Review what needs to be communicated",
                    "  - Prepare talking points or message",
                    "  - Gather supporting information",
                    "",
                    "- [ ] **Contact Stakeholder**",
                    f"  - Reach out to {stakeholder}",
                    "  - Communicate the information or request",
                    "  - Schedule follow-up if needed",
                    "",
                    "- [ ] **Document Outcome**",
                    "  - Record response and decisions",
                    "  - Note any action items",
                    "  - Update workflows as needed",
                    "",
                ]
            )

        content_parts.extend(
            [
                "## Notes",
                "",
                f"*Context: {context}*",
                "",
                "*Use this space to document communication and outcomes.*",
                "",
                "## Reminders",
                "",
                f"- Follow up with {stakeholder} on {parameters['follow_up_date']}",
                "- Update relevant workflows based on outcome",
                "- Document lessons learned for future reference",
            ]
        )

        return "\n".join(content_parts)

    def _parse_follow_up_time(self, follow_up_date: str) -> datetime:
        """Parse follow-up time string to datetime"""
        now = datetime.now()

        if "tomorrow" in follow_up_date.lower():
            return now + timedelta(days=1)
        elif "next week" in follow_up_date.lower():
            return now + timedelta(days=7)
        elif "today" in follow_up_date.lower():
            return now + timedelta(hours=2)
        else:
            try:
                # Try to parse as ISO date
                return datetime.fromisoformat(follow_up_date)
            except:
                # Default to tomorrow
                return now + timedelta(days=1)

    def _urgency_to_priority(self, urgency: str) -> int:
        """Convert urgency to numeric priority"""
        urgency_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
        return urgency_map.get(urgency, 3)


class DailyOperationsSkills:
    """Collection of daily operations skills"""

    @staticmethod
    def get_all_skills() -> List[Skill]:
        """Get all daily operations skills"""
        return [StandupPrepSkill(), FollowUpManagementSkill()]

    @staticmethod
    def register_all(registry) -> None:
        """Register all daily operations skills with a registry"""
        for skill in DailyOperationsSkills.get_all_skills():
            registry.register(skill)
