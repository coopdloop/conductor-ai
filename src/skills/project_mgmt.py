"""Project Management Skills

AI-callable skills for managing projects, bugs, deployments, and team coordination.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from .base import Skill, SkillParameter, SkillExecutionResult, SkillStatus


class BugInvestigationSkill(Skill):
    """Systematic bug investigation and documentation workflow"""

    @property
    def name(self) -> str:
        return "bug_investigation"

    @property
    def description(self) -> str:
        return "Create a systematic workflow for investigating and documenting bugs, including reproduction steps, analysis, and resolution tracking"

    @property
    def category(self) -> str:
        return "project_mgmt"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="bug_title",
                type="string",
                description="Title or description of the bug"
            ),
            SkillParameter(
                name="severity",
                type="string",
                description="Bug severity level",
                options=["critical", "high", "medium", "low"],
                default="medium"
            ),
            SkillParameter(
                name="component",
                type="string",
                description="System component affected",
                required=False
            ),
            SkillParameter(
                name="reporter",
                type="string",
                description="Who reported the bug",
                required=False
            ),
            SkillParameter(
                name="initial_info",
                type="string",
                description="Initial information or symptoms",
                required=False
            )
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None
    ) -> SkillExecutionResult:
        """Execute bug investigation workflow creation"""
        start_time = datetime.now()

        try:
            bug_title = parameters["bug_title"]
            severity = parameters["severity"]
            component = parameters.get("component", "Unknown")

            # Create investigation workflow
            workflow_content = self._generate_bug_investigation_workflow(
                bug_title, severity, component, parameters
            )

            # Create workflow using orchestrator
            if orchestrator and hasattr(orchestrator, 'workflow_engine'):
                workflow_result = orchestrator.workflow_engine.create_workflow(
                    title=f"Bug Investigation: {bug_title}",
                    content=workflow_content,
                    priority=self._severity_to_priority(severity),
                    metadata={
                        "type": "bug_investigation",
                        "severity": severity,
                        "component": component,
                        "created_by": "ai_bug_investigation_skill"
                    }
                )
                workflow_id = workflow_result.get("workflow_id")
            else:
                workflow_id = f"bug_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Schedule follow-up reminders
            if orchestrator and hasattr(orchestrator, 'scheduler'):
                # Daily check-in for critical bugs, weekly for others
                if severity == "critical":
                    follow_up_time = datetime.now() + timedelta(hours=4)
                    orchestrator.scheduler.schedule_reminder(
                        f"Check progress on critical bug: {bug_title}",
                        follow_up_time.isoformat(),
                        metadata={"workflow_id": workflow_id, "type": "bug_followup"}
                    )
                else:
                    follow_up_time = datetime.now() + timedelta(days=2)
                    orchestrator.scheduler.schedule_reminder(
                        f"Check progress on bug investigation: {bug_title}",
                        follow_up_time.isoformat(),
                        metadata={"workflow_id": workflow_id, "type": "bug_followup"}
                    )

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "workflow_id": workflow_id,
                    "bug_title": bug_title,
                    "severity": severity,
                    "investigation_steps": 8,
                    "follow_up_scheduled": True
                },
                execution_time=execution_time,
                metadata={
                    "component": component,
                    "workflow_type": "bug_investigation"
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=execution_time,
                error=str(e)
            )

    def _generate_bug_investigation_workflow(
        self,
        bug_title: str,
        severity: str,
        component: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate bug investigation workflow content"""
        content_parts = [
            f"# Bug Investigation: {bug_title}",
            "",
            "## Bug Information",
            f"- **Severity:** {severity}",
            f"- **Component:** {component}",
            f"- **Reporter:** {parameters.get('reporter', 'Not specified')}",
            f"- **Date Reported:** {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Initial Information",
            parameters.get('initial_info', 'To be gathered during investigation'),
            "",
            "## Investigation Actions",
            "",
            "- [ ] **Reproduce the Issue**",
            "  - Document exact steps to reproduce",
            "  - Note environment details (OS, browser, version)",
            "  - Capture screenshots or recordings if applicable",
            "",
            "- [ ] **Gather System Information**",
            "  - Check system logs for error messages",
            "  - Review monitoring dashboards",
            "  - Document system state at time of incident",
            "",
            "- [ ] **Analyze Root Cause**",
            "  - Examine code changes in affected component",
            "  - Review recent deployments",
            "  - Check for similar historical issues",
            "",
            "- [ ] **Isolate the Problem**",
            "  - Identify minimum conditions to trigger bug",
            "  - Test in different environments",
            "  - Document scope and impact",
            "",
            "- [ ] **Develop Solution**",
            "  - Design fix approach",
            "  - Consider multiple solution options",
            "  - Estimate effort and risks",
            "",
            "- [ ] **Test Fix**",
            "  - Implement fix in test environment",
            "  - Verify issue resolution",
            "  - Test for regression issues",
            "",
            "- [ ] **Document Resolution**",
            "  - Create detailed resolution documentation",
            "  - Update knowledge base",
            "  - Note prevention measures",
            "",
            "- [ ] **Deploy and Verify**",
            "  - Deploy fix to production",
            "  - Monitor for issues",
            "  - Confirm resolution with reporter",
            "",
            "## Notes",
            "",
            "*Use this space for investigation notes, findings, and decisions.*",
            "",
            "## Reminders",
            "",
            f"- Check progress every {'4 hours' if severity == 'critical' else '2 days'}",
            "- Update stakeholders on investigation status",
            "- Document lessons learned for future prevention"
        ]

        return "\n".join(content_parts)

    def _severity_to_priority(self, severity: str) -> int:
        """Convert severity to numeric priority"""
        severity_map = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4
        }
        return severity_map.get(severity, 3)


class DeploymentWorkflowSkill(Skill):
    """Create deployment workflow with validation and rollback procedures"""

    @property
    def name(self) -> str:
        return "deployment_workflow"

    @property
    def description(self) -> str:
        return "Create a comprehensive deployment workflow including pre-deployment checks, deployment steps, validation, and rollback procedures"

    @property
    def category(self) -> str:
        return "project_mgmt"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="deployment_name",
                type="string",
                description="Name of the deployment"
            ),
            SkillParameter(
                name="environment",
                type="string",
                description="Target environment",
                options=["development", "staging", "production"],
                default="staging"
            ),
            SkillParameter(
                name="deployment_type",
                type="string",
                description="Type of deployment",
                options=["application", "database", "infrastructure", "configuration"],
                default="application"
            ),
            SkillParameter(
                name="risk_level",
                type="string",
                description="Risk level of deployment",
                options=["low", "medium", "high"],
                default="medium"
            ),
            SkillParameter(
                name="scheduled_time",
                type="string",
                description="Scheduled deployment time (ISO format)",
                required=False
            )
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None
    ) -> SkillExecutionResult:
        """Execute deployment workflow creation"""
        start_time = datetime.now()

        try:
            deployment_name = parameters["deployment_name"]
            environment = parameters["environment"]
            risk_level = parameters["risk_level"]

            # Create deployment workflow
            workflow_content = self._generate_deployment_workflow(
                deployment_name, environment, risk_level, parameters
            )

            # Create workflow
            if orchestrator and hasattr(orchestrator, 'workflow_engine'):
                workflow_result = orchestrator.workflow_engine.create_workflow(
                    title=f"Deployment: {deployment_name} to {environment}",
                    content=workflow_content,
                    priority=self._risk_to_priority(risk_level),
                    due_date=parameters.get("scheduled_time"),
                    metadata={
                        "type": "deployment",
                        "environment": environment,
                        "risk_level": risk_level,
                        "deployment_type": parameters["deployment_type"]
                    }
                )
                workflow_id = workflow_result.get("workflow_id")
            else:
                workflow_id = f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Schedule deployment reminders
            if parameters.get("scheduled_time") and orchestrator and hasattr(orchestrator, 'scheduler'):
                scheduled_dt = datetime.fromisoformat(parameters["scheduled_time"].replace('Z', '+00:00'))

                # Reminder 1 day before for high-risk deployments
                if risk_level == "high":
                    reminder_time = scheduled_dt - timedelta(days=1)
                    orchestrator.scheduler.schedule_reminder(
                        f"Pre-deployment checklist for: {deployment_name}",
                        reminder_time.isoformat(),
                        metadata={"workflow_id": workflow_id, "type": "deployment_reminder"}
                    )

                # Reminder 2 hours before
                reminder_time = scheduled_dt - timedelta(hours=2)
                orchestrator.scheduler.schedule_reminder(
                    f"Deployment starting soon: {deployment_name}",
                    reminder_time.isoformat(),
                    metadata={"workflow_id": workflow_id, "type": "deployment_reminder"}
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "workflow_id": workflow_id,
                    "deployment_name": deployment_name,
                    "environment": environment,
                    "risk_level": risk_level,
                    "scheduled_time": parameters.get("scheduled_time"),
                    "steps_count": 12
                },
                execution_time=execution_time,
                metadata={
                    "deployment_type": parameters["deployment_type"],
                    "environment": environment
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.FAILED,
                output={},
                execution_time=execution_time,
                error=str(e)
            )

    def _generate_deployment_workflow(
        self,
        deployment_name: str,
        environment: str,
        risk_level: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate deployment workflow content"""
        content_parts = [
            f"# Deployment: {deployment_name} to {environment.title()}",
            "",
            "## Deployment Information",
            f"- **Environment:** {environment}",
            f"- **Type:** {parameters['deployment_type']}",
            f"- **Risk Level:** {risk_level}",
            f"- **Scheduled Time:** {parameters.get('scheduled_time', 'TBD')}",
            "",
            "## Pre-Deployment Actions",
            "",
            "- [ ] **Verify Prerequisites**",
            "  - Confirm all dependencies are ready",
            "  - Check system resources and capacity",
            "  - Verify backup and rollback procedures",
            "",
            "- [ ] **Team Coordination**",
            "  - Notify stakeholders of deployment window",
            "  - Confirm team availability for support",
            "  - Set up communication channels",
            "",
            "- [ ] **Environment Preparation**",
            "  - Stop or scale down affected services",
            "  - Create database backups if needed",
            "  - Verify monitoring and alerting",
            "",
            "## Deployment Actions",
            "",
            "- [ ] **Execute Deployment**",
            "  - Follow deployment procedure",
            "  - Monitor deployment progress",
            "  - Document any issues or deviations",
            "",
            "- [ ] **Initial Validation**",
            "  - Verify services start successfully",
            "  - Check basic functionality",
            "  - Review error logs",
            "",
            "- [ ] **Comprehensive Testing**",
            "  - Run smoke tests",
            "  - Validate key user journeys",
            "  - Check integration points",
            "",
            "## Post-Deployment Actions",
            "",
            "- [ ] **Monitoring and Alerting**",
            "  - Monitor system metrics",
            "  - Watch for error rate increases",
            "  - Check performance baselines",
            "",
            "- [ ] **User Acceptance**",
            "  - Confirm functionality with stakeholders",
            "  - Address any immediate concerns",
            "  - Document known issues",
            "",
            "- [ ] **Documentation Updates**",
            "  - Update deployment documentation",
            "  - Record lessons learned",
            "  - Update runbooks if needed",
            "",
            "## Rollback Procedure",
            "",
            "**Rollback Triggers:**",
            "- Critical functionality is broken",
            "- Error rates exceed acceptable thresholds",
            "- Performance degradation is severe",
            "",
            "**Rollback Steps:**",
            "1. Stop current deployment",
            "2. Restore previous version",
            "3. Verify system stability",
            "4. Notify stakeholders",
            "",
            "## Notes",
            "",
            "*Document deployment progress, issues, and decisions here.*",
            "",
            "## Reminders",
            "",
            "- Monitor system for 24 hours post-deployment",
            "- Schedule post-deployment review meeting",
            "- Update incident response procedures if needed"
        ]

        return "\n".join(content_parts)

    def _risk_to_priority(self, risk_level: str) -> int:
        """Convert risk level to numeric priority"""
        risk_map = {
            "high": 2,
            "medium": 3,
            "low": 4
        }
        return risk_map.get(risk_level, 3)


class ProjectManagementSkills:
    """Collection of project management skills"""

    @staticmethod
    def get_all_skills() -> List[Skill]:
        """Get all project management skills"""
        return [
            BugInvestigationSkill(),
            DeploymentWorkflowSkill()
        ]

    @staticmethod
    def register_all(registry) -> None:
        """Register all project management skills with a registry"""
        for skill in ProjectManagementSkills.get_all_skills():
            registry.register(skill)