"""Reusable promotional-video project and artifact contracts."""

from .model import (
    ArtifactPolicy,
    Chapter,
    ConfigBinding,
    Cue,
    ProjectConfig,
    RunManifest,
    SignoffRecord,
    SourceRecord,
)
from .operations import (
    initialize_project,
    preserve_artifact,
    record_signoff,
    start_run,
)
from .export_commands import ExportCommandResult, handle_export_command
from .media import (
    BOUND_MEDIA_PROBE_FORMAT_VERSION,
    BOUND_MEDIA_PROBE_KIND,
    BoundMediaProbe,
    bind_media_probe,
    load_bound_media_probe,
    parse_bound_media_probe_json,
    probe_and_write_bound_media,
    write_bound_media_probe,
)
from .pipeline import (
    PipelineComposer,
    PipelineInvocation,
    PipelineResult,
    run_invocation,
    run_pipeline,
)
from .pipeline_commands import (
    CommandOutcome,
    handle_audit,
    handle_build,
    handle_plan,
)
from .project import load_document
from .registry import AdapterFactory, ComponentRegistry, PresetFactory
from .review_commands import ReviewCommandResult, run_review_command
from .runlog import (
    AutomatedAuditRecord,
    PhaseRecord,
    append_automated_audit_record,
    append_phase_record,
)
from .sources import PreparedVisual, VisualSource

__all__ = [
    "ArtifactPolicy",
    "AdapterFactory",
    "AutomatedAuditRecord",
    "BOUND_MEDIA_PROBE_FORMAT_VERSION",
    "BOUND_MEDIA_PROBE_KIND",
    "BoundMediaProbe",
    "Chapter",
    "ConfigBinding",
    "ComponentRegistry",
    "CommandOutcome",
    "Cue",
    "ProjectConfig",
    "PipelineComposer",
    "PipelineInvocation",
    "PipelineResult",
    "PhaseRecord",
    "PreparedVisual",
    "PresetFactory",
    "ReviewCommandResult",
    "RunManifest",
    "SignoffRecord",
    "SourceRecord",
    "VisualSource",
    "ExportCommandResult",
    "append_automated_audit_record",
    "append_phase_record",
    "bind_media_probe",
    "initialize_project",
    "load_document",
    "load_bound_media_probe",
    "parse_bound_media_probe_json",
    "preserve_artifact",
    "record_signoff",
    "handle_export_command",
    "handle_audit",
    "handle_build",
    "handle_plan",
    "run_invocation",
    "run_pipeline",
    "run_review_command",
    "probe_and_write_bound_media",
    "start_run",
    "write_bound_media_probe",
]

__version__ = "0.1.0"
