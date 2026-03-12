"""Documentation Skills

AI-callable skills for creating, maintaining, and publishing documentation.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from .base import Skill, SkillExecutionResult, SkillParameter, SkillStatus


class CreateDocumentationSkill(Skill):
    """Create comprehensive documentation from workflow or project context"""

    @property
    def name(self) -> str:
        return "create_documentation"

    @property
    def description(self) -> str:
        return "Create comprehensive documentation from workflow context, including procedures, troubleshooting guides, and technical specifications"

    @property
    def category(self) -> str:
        return "documentation"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="doc_type",
                type="string",
                description="Type of documentation to create",
                options=[
                    "procedure",
                    "troubleshooting",
                    "api_guide",
                    "runbook",
                    "technical_spec",
                    "user_guide",
                ],
            ),
            SkillParameter(
                name="title", type="string", description="Documentation title"
            ),
            SkillParameter(
                name="context_source",
                type="string",
                description="Source of context information",
                options=["current_workflow", "workflow_id", "project_notes"],
                default="current_workflow",
            ),
            SkillParameter(
                name="workflow_id",
                type="string",
                description="Specific workflow ID to document",
                required=False,
            ),
            SkillParameter(
                name="include_sections",
                type="string",
                description="Comma-separated list of sections to include",
                default="overview,steps,troubleshooting,references",
            ),
            SkillParameter(
                name="format",
                type="string",
                description="Output format",
                options=["markdown", "html", "docx"],
                default="markdown",
            ),
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None,
    ) -> SkillExecutionResult:
        """Execute documentation creation"""
        start_time = datetime.now()

        try:
            doc_type = parameters["doc_type"]
            title = parameters["title"]
            sections = [s.strip() for s in parameters["include_sections"].split(",")]

            # Get source context
            if parameters["context_source"] == "current_workflow":
                source_data = context.get("current_workflow", {})
            elif parameters["context_source"] == "workflow_id" and parameters.get(
                "workflow_id"
            ):
                # Would get workflow from orchestrator
                source_data = {"title": "Specified Workflow", "actions": []}
            else:
                source_data = context.get("project_notes", {})

            # Generate documentation content
            content = self._generate_documentation_content(
                doc_type, title, sections, source_data, context
            )

            # Create document using doc processor
            if orchestrator and hasattr(orchestrator, "doc_processor"):
                doc_result = orchestrator.doc_processor.create_document(
                    title=title,
                    content=content,
                    metadata={
                        "doc_type": doc_type,
                        "generated_by": "ai_documentation_skill",
                        "source_workflow": source_data.get("id"),
                        "created_at": datetime.now().isoformat(),
                    },
                )
            else:
                doc_result = {
                    "doc_id": f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "content": content,
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "doc_id": doc_result.get("doc_id"),
                    "title": title,
                    "doc_type": doc_type,
                    "content": content,
                    "format": parameters["format"],
                    "sections": sections,
                },
                execution_time=execution_time,
                metadata={
                    "source_context": parameters["context_source"],
                    "generated_sections": len(sections),
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

    def _generate_documentation_content(
        self,
        doc_type: str,
        title: str,
        sections: List[str],
        source_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Generate documentation content based on type and context"""
        content_parts = [f"# {title}\n"]

        # Add document metadata
        content_parts.extend(
            [
                f"**Document Type:** {doc_type.replace('_', ' ').title()}",
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"**Source:** {source_data.get('title', 'Workflow Context')}",
                "",
            ]
        )

        # Generate sections based on document type
        for section in sections:
            if section == "overview":
                content_parts.extend(
                    self._generate_overview_section(doc_type, source_data)
                )
            elif section == "steps":
                content_parts.extend(
                    self._generate_steps_section(doc_type, source_data)
                )
            elif section == "troubleshooting":
                content_parts.extend(
                    self._generate_troubleshooting_section(doc_type, source_data)
                )
            elif section == "references":
                content_parts.extend(
                    self._generate_references_section(doc_type, source_data, context)
                )

        return "\n".join(content_parts)

    def _generate_overview_section(
        self, doc_type: str, source_data: Dict[str, Any]
    ) -> List[str]:
        """Generate overview section"""
        lines = ["## Overview\n"]

        if doc_type == "procedure":
            lines.extend(
                [
                    "This document outlines the step-by-step procedure for completing the workflow:",
                    f"**{source_data.get('title', 'Workflow Process')}**",
                    "",
                ]
            )

            if source_data.get("description"):
                lines.extend(["### Purpose", source_data["description"], ""])

        elif doc_type == "troubleshooting":
            lines.extend(
                [
                    "This troubleshooting guide helps resolve common issues encountered during:",
                    f"**{source_data.get('title', 'Process or System')}**",
                    "",
                    "Use this guide to systematically diagnose and resolve problems.",
                    "",
                ]
            )

        elif doc_type == "runbook":
            lines.extend(
                [
                    "This runbook provides operational procedures for:",
                    f"**{source_data.get('title', 'System or Service')}**",
                    "",
                    "Follow these procedures during incidents, maintenance, or routine operations.",
                    "",
                ]
            )

        return lines

    def _generate_steps_section(
        self, doc_type: str, source_data: Dict[str, Any]
    ) -> List[str]:
        """Generate steps/procedures section"""
        lines = ["## Procedure\n"]

        actions = source_data.get("actions", [])
        if actions:
            lines.append("Follow these steps in order:\n")
            for i, action in enumerate(actions, 1):
                description = action.get("description", f"Step {i}")
                lines.append(f"{i}. **{description}**")

                # Add notes if available
                if action.get("notes"):
                    lines.extend([f"   - {action['notes']}", ""])
                else:
                    lines.append("")

        else:
            lines.extend(
                [
                    "### Prerequisites",
                    "- Ensure you have necessary permissions",
                    "- Verify system access and connectivity",
                    "",
                    "### Main Procedure",
                    "1. **Initial Setup**",
                    "   - Document specific steps based on workflow requirements",
                    "",
                    "2. **Execution**",
                    "   - Follow established procedures",
                    "   - Document any deviations or issues",
                    "",
                    "3. **Verification**",
                    "   - Confirm successful completion",
                    "   - Update relevant tracking systems",
                    "",
                ]
            )

        return lines

    def _generate_troubleshooting_section(
        self, doc_type: str, source_data: Dict[str, Any]
    ) -> List[str]:
        """Generate troubleshooting section"""
        lines = ["## Troubleshooting\n"]

        lines.extend(
            [
                "### Common Issues",
                "",
                "| Issue | Symptoms | Solution |",
                "|-------|----------|----------|",
                "| Access Problems | Cannot connect or authenticate | Verify credentials and network connectivity |",
                "| Timeout Errors | Operations fail with timeout | Check system load and increase timeout values |",
                "| Data Issues | Incorrect or missing data | Validate data sources and transformation logic |",
                "",
                "### Diagnostic Steps",
                "",
                "1. **Check System Status**",
                "   - Verify all required services are running",
                "   - Check system resource utilization",
                "",
                "2. **Review Logs**",
                "   - Check application logs for errors",
                "   - Review system event logs",
                "",
                "3. **Test Connectivity**",
                "   - Verify network connections",
                "   - Test API endpoints or database connections",
                "",
                "4. **Escalation**",
                "   - Contact system administrators if issues persist",
                "   - Document any temporary workarounds used",
                "",
            ]
        )

        return lines

    def _generate_references_section(
        self, doc_type: str, source_data: Dict[str, Any], context: Dict[str, Any]
    ) -> List[str]:
        """Generate references section"""
        lines = ["## References\n"]

        lines.extend(
            [
                "### Related Documentation",
                "- System architecture documents",
                "- API documentation",
                "- Configuration guides",
                "",
                "### External Resources",
                "- Vendor documentation",
                "- Community forums and knowledge bases",
                "- Monitoring and alerting dashboards",
                "",
                "### Contacts",
                "- **Primary Owner:** [To be specified]",
                "- **Technical Support:** [To be specified]",
                "- **Emergency Contact:** [To be specified]",
                "",
            ]
        )

        # Add workflow-specific references
        if source_data.get("id"):
            lines.extend(
                [
                    f"### Source Workflow",
                    f"- Workflow ID: {source_data['id']}",
                    f"- Created: {source_data.get('created_at', 'N/A')}",
                    "",
                ]
            )

        return lines


class UpdateDocumentationSkill(Skill):
    """Update existing documentation with new information"""

    @property
    def name(self) -> str:
        return "update_documentation"

    @property
    def description(self) -> str:
        return "Update existing documentation with new information, corrections, or additional sections"

    @property
    def category(self) -> str:
        return "documentation"

    @property
    def parameters(self) -> List[SkillParameter]:
        return [
            SkillParameter(
                name="doc_id", type="string", description="ID of document to update"
            ),
            SkillParameter(
                name="update_type",
                type="string",
                description="Type of update to perform",
                options=["append", "replace_section", "version_update", "correction"],
            ),
            SkillParameter(
                name="section",
                type="string",
                description="Section to update (for replace_section)",
                required=False,
            ),
            SkillParameter(
                name="content",
                type="string",
                description="New content to add or replace with",
            ),
            SkillParameter(
                name="reason",
                type="string",
                description="Reason for the update",
                default="Content update",
            ),
        ]

    async def execute(
        self,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        orchestrator: Any = None,
    ) -> SkillExecutionResult:
        """Execute documentation update"""
        start_time = datetime.now()

        try:
            doc_id = parameters["doc_id"]
            update_type = parameters["update_type"]
            content = parameters["content"]
            reason = parameters["reason"]

            # Get existing document
            if orchestrator and hasattr(orchestrator, "doc_processor"):
                existing_doc = orchestrator.doc_processor.get_document(doc_id)
                if not existing_doc:
                    raise ValueError(f"Document {doc_id} not found")

                # Perform update based on type
                if update_type == "append":
                    new_content = existing_doc["content"] + "\n\n" + content
                elif update_type == "replace_section":
                    new_content = self._replace_section(
                        existing_doc["content"], parameters.get("section", ""), content
                    )
                elif update_type == "version_update":
                    new_content = content  # Complete replacement
                else:  # correction
                    new_content = self._apply_correction(
                        existing_doc["content"], content
                    )

                # Update document
                update_result = orchestrator.doc_processor.update_document(
                    doc_id,
                    new_content,
                    metadata={
                        "update_type": update_type,
                        "update_reason": reason,
                        "updated_by": "ai_documentation_skill",
                        "updated_at": datetime.now().isoformat(),
                    },
                )
            else:
                update_result = {
                    "doc_id": doc_id,
                    "updated": True,
                    "new_content": content,
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillExecutionResult(
                skill_name=self.name,
                status=SkillStatus.COMPLETED,
                output={
                    "doc_id": doc_id,
                    "update_type": update_type,
                    "updated": True,
                    "reason": reason,
                },
                execution_time=execution_time,
                metadata={"content_length": len(content), "update_type": update_type},
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

    def _replace_section(
        self, existing_content: str, section_name: str, new_content: str
    ) -> str:
        """Replace a specific section in the document"""
        lines = existing_content.split("\n")
        new_lines = []
        in_target_section = False
        section_header = f"## {section_name}"

        for line in lines:
            if line.strip().startswith("##") and section_name.lower() in line.lower():
                in_target_section = True
                new_lines.append(line)
                new_lines.append(new_content)
            elif line.strip().startswith("##") and in_target_section:
                in_target_section = False
                new_lines.append(line)
            elif not in_target_section:
                new_lines.append(line)

        return "\n".join(new_lines)

    def _apply_correction(self, existing_content: str, correction_content: str) -> str:
        """Apply corrections to existing content"""
        # Simple append for now - could be enhanced with more sophisticated text replacement
        return existing_content + "\n\n## Corrections\n\n" + correction_content


class DocumentationSkills:
    """Collection of documentation-related skills"""

    @staticmethod
    def get_all_skills() -> List[Skill]:
        """Get all documentation skills"""
        return [CreateDocumentationSkill(), UpdateDocumentationSkill()]

    @staticmethod
    def register_all(registry) -> None:
        """Register all documentation skills with a registry"""
        for skill in DocumentationSkills.get_all_skills():
            registry.register(skill)
