#!/usr/bin/env python3
"""
TDD Artifacts Management Script

Centralized CLI tool for managing TDD workflow artifacts, reducing cognitive
overhead for phase agents and ensuring consistent artifact structure.

Usage:
    scripts/tdd_artifacts.py <command> [options]

Commands:
    init            Create artifact directory structure
    start-phase     Initialize phase directory and metadata
    complete-phase  Finalize phase with summary and auto-diff
    capture-logs    Copy build/test logs to phase directory
    record-files    Record file paths to phase-specific list
    capture-diff    Manually capture git diff
    status          Show current workflow state
    reset-phase     Reset stuck/failed phase to pending
    validate        Check artifact consistency

Author: Guido (Python Engineer Persona)
Design: TDD Artifacts Script Design Specification v2.0
"""

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
import shutil
import glob as glob_module


# ============================================================================
# Constants
# ============================================================================

SCHEMA_VERSION = "1.0"
BASE_DIR = Path(".claude/temp/")
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class TDDArtifactsError(Exception):
    """Base exception for all TDD artifacts script errors."""
    pass


class FeatureNotFoundError(TDDArtifactsError):
    """Feature directory doesn't exist."""
    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        super().__init__(f"Feature '{feature_name}' not initialized")


class InvalidPhaseError(TDDArtifactsError):
    """Invalid phase name provided."""
    def __init__(self, phase: str):
        self.phase = phase
        super().__init__(f"Invalid phase '{phase}'. Must be one of: red, green, refactor")


class PhaseStateError(TDDArtifactsError):
    """Phase in wrong state for operation."""
    def __init__(self, phase: str, current_status: str, expected_status: str):
        self.phase = phase
        self.current_status = current_status
        self.expected_status = expected_status
        super().__init__(
            f"Phase '{phase}' is '{current_status}', expected '{expected_status}'"
        )


class MetadataCorruptedError(TDDArtifactsError):
    """Metadata file is corrupted or invalid."""
    pass


class GitOperationError(TDDArtifactsError):
    """Git command failed (non-fatal in most cases)."""
    pass


# ============================================================================
# Enums
# ============================================================================

class Phase(str, Enum):
    """TDD workflow phases (hardcoded, not extensible)."""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"


class PhaseStatus(str, Enum):
    """Phase lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FeatureStatus(str, Enum):
    """Overall feature workflow status."""
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class PhaseInfo:
    """Phase status information in manifest."""
    status: PhaseStatus


@dataclass
class PhaseMetadata:
    """Phase-specific metadata with schema versioning."""
    schema_version: str
    phase: Phase
    status: PhaseStatus
    started_at: str  # ISO 8601 timestamp
    completed_at: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class FeatureManifest:
    """Feature-level metadata and phase tracking."""
    schema_version: str
    feature_name: str
    feature_impl_dir: str
    created_at: str
    current_phase: Optional[str]
    status: FeatureStatus
    phases: dict[str, PhaseInfo]


# ============================================================================
# Utility Functions
# ============================================================================

def normalize_feature_name(name: str) -> str:
    """
    Normalize feature name to <feature>_impl format.

    Args:
        name: Raw feature name (e.g., "async_copy")

    Returns:
        Normalized name (e.g., "async_copy_impl")
    """
    if name.endswith("_impl"):
        return name
    return f"{name}_impl"


def get_feature_dir(feature_name: str, base_dir: Path = BASE_DIR) -> Path:
    """
    Get feature implementation directory path.

    Args:
        feature_name: Feature name (will be normalized)
        base_dir: Base directory for artifacts

    Returns:
        Path to feature directory
    """
    impl_name = normalize_feature_name(feature_name)
    return base_dir / impl_name


def validate_feature_exists(feature_dir: Path) -> None:
    """
    Validate that feature directory exists.

    Args:
        feature_dir: Path to feature directory

    Raises:
        FeatureNotFoundError: If directory doesn't exist
    """
    if not feature_dir.exists():
        feature_name = feature_dir.name.replace("_impl", "")
        raise FeatureNotFoundError(feature_name)


def validate_phase(phase_str: str) -> Phase:
    """
    Validate and convert phase string to Phase enum.

    Args:
        phase_str: Phase name as string

    Returns:
        Phase enum value

    Raises:
        InvalidPhaseError: If phase is not valid
    """
    try:
        return Phase(phase_str)
    except ValueError:
        raise InvalidPhaseError(phase_str)


def get_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format with timezone.

    Returns:
        Formatted timestamp string
    """
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


def read_manifest(feature_dir: Path) -> FeatureManifest:
    """
    Read and parse feature manifest.json.

    Args:
        feature_dir: Path to feature directory

    Returns:
        Parsed FeatureManifest

    Raises:
        MetadataCorruptedError: If manifest is invalid
    """
    manifest_path = feature_dir / "manifest.json"
    try:
        with manifest_path.open('r') as f:
            data = json.load(f)

        # Convert nested dicts to PhaseInfo objects
        phases = {
            phase_name: PhaseInfo(status=PhaseStatus(phase_data["status"]))
            for phase_name, phase_data in data["phases"].items()
        }

        return FeatureManifest(
            schema_version=data["schema_version"],
            feature_name=data["feature_name"],
            feature_impl_dir=data["feature_impl_dir"],
            created_at=data["created_at"],
            current_phase=data.get("current_phase"),
            status=FeatureStatus(data["status"]),
            phases=phases
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise MetadataCorruptedError(f"Invalid manifest.json: {e}")


def write_manifest(feature_dir: Path, manifest: FeatureManifest) -> None:
    """
    Write feature manifest atomically.

    Args:
        feature_dir: Path to feature directory
        manifest: FeatureManifest to write
    """
    manifest_path = feature_dir / "manifest.json"
    temp_path = manifest_path.with_suffix('.json.tmp')

    # Convert to dict for JSON serialization
    data = {
        "schema_version": manifest.schema_version,
        "feature_name": manifest.feature_name,
        "feature_impl_dir": manifest.feature_impl_dir,
        "created_at": manifest.created_at,
        "current_phase": manifest.current_phase,
        "status": manifest.status.value,
        "phases": {
            phase_name: {"status": phase_info.status.value}
            for phase_name, phase_info in manifest.phases.items()
        }
    }

    # Atomic write: write to temp, then rename
    with temp_path.open('w') as f:
        json.dump(data, f, indent=2)
    temp_path.replace(manifest_path)


def read_phase_metadata(phase_dir: Path) -> PhaseMetadata:
    """
    Read and parse phase metadata.json.

    Args:
        phase_dir: Path to phase directory

    Returns:
        Parsed PhaseMetadata

    Raises:
        MetadataCorruptedError: If metadata is invalid
    """
    metadata_path = phase_dir / "metadata.json"
    try:
        with metadata_path.open('r') as f:
            data = json.load(f)

        return PhaseMetadata(
            schema_version=data["schema_version"],
            phase=Phase(data["phase"]),
            status=PhaseStatus(data["status"]),
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            summary=data.get("summary")
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise MetadataCorruptedError(f"Invalid metadata.json: {e}")


def write_phase_metadata(phase_dir: Path, metadata: PhaseMetadata) -> None:
    """
    Write phase metadata atomically.

    Args:
        phase_dir: Path to phase directory
        metadata: PhaseMetadata to write
    """
    metadata_path = phase_dir / "metadata.json"
    temp_path = metadata_path.with_suffix('.json.tmp')

    data = {
        "schema_version": metadata.schema_version,
        "phase": metadata.phase.value,
        "status": metadata.status.value,
        "started_at": metadata.started_at,
        "completed_at": metadata.completed_at,
        "summary": metadata.summary
    }

    with temp_path.open('w') as f:
        json.dump(data, f, indent=2)
    temp_path.replace(metadata_path)


def capture_git_diff(output_path: Path, since_commit: str = "HEAD") -> bool:
    """
    Capture git diff to file.

    Args:
        output_path: Where to save the diff
        since_commit: Commit to diff against

    Returns:
        True if successful, False otherwise

    Raises:
        GitOperationError: If git command fails critically
    """
    try:
        result = subprocess.run(
            ["git", "diff", since_commit],
            capture_output=True,
            text=True,
            check=True
        )
        output_path.write_text(result.stdout)
        logger.info(f"Captured git diff to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git diff failed: {e}")
        # Create empty file to indicate attempt was made
        output_path.write_text(f"# Git diff failed: {e}\n")
        return False
    except FileNotFoundError:
        raise GitOperationError("Git not found in PATH")


def auto_detect_logs(build_dir: Path, tmp_dir: Path) -> tuple[Optional[Path], Optional[Path]]:
    """
    Auto-detect build and test log locations.

    Args:
        build_dir: Build directory path
        tmp_dir: Temporary directory path

    Returns:
        Tuple of (build_log_path, test_log_path), either can be None
    """
    build_log = None
    test_log = None

    # Build log candidates
    build_candidates = [
        build_dir / "build-output.log",
        build_dir / "Testing" / "Temporary" / "LastBuild.log",
    ]

    # Add glob patterns for tmp directory
    tmp_build_patterns = list(tmp_dir.glob("build-*.log"))
    build_candidates.extend(tmp_build_patterns)

    for candidate in build_candidates:
        if candidate.exists():
            build_log = candidate
            logger.info(f"Auto-detected build log: {candidate}")
            break

    # Test log candidates
    test_candidates = [
        build_dir / "test-results.log",
        build_dir / "Testing" / "Temporary" / "LastTest.log",
    ]

    tmp_test_patterns = list(tmp_dir.glob("test-*.log"))
    test_candidates.extend(tmp_test_patterns)

    for candidate in test_candidates:
        if candidate.exists():
            test_log = candidate
            logger.info(f"Auto-detected test log: {candidate}")
            break

    return build_log, test_log


# ============================================================================
# Command Implementations
# ============================================================================

def cmd_init(feature: str, base_dir: Path = BASE_DIR) -> None:
    """
    Initialize feature artifact directory structure.

    Args:
        feature: Feature name
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)

    if feature_dir.exists():
        logger.warning(f"Feature directory already exists: {feature_dir}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            logger.info("Aborted.")
            sys.exit(1)
        shutil.rmtree(feature_dir)

    # Create directory structure
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "red-phase").mkdir(exist_ok=True)
    (feature_dir / "green-phase").mkdir(exist_ok=True)
    (feature_dir / "refactor-phase").mkdir(exist_ok=True)

    # Create initial manifest
    manifest = FeatureManifest(
        schema_version=SCHEMA_VERSION,
        feature_name=feature,
        feature_impl_dir=feature_dir.name,
        created_at=get_timestamp(),
        current_phase=None,
        status=FeatureStatus.INITIALIZED,
        phases={
            "red": PhaseInfo(status=PhaseStatus.PENDING),
            "green": PhaseInfo(status=PhaseStatus.PENDING),
            "refactor": PhaseInfo(status=PhaseStatus.PENDING),
        }
    )

    write_manifest(feature_dir, manifest)
    logger.info(f"Initialized feature artifact directory: {feature_dir}")
    print(f"Created: {feature_dir}")


def cmd_start_phase(feature: str, phase: Phase, base_dir: Path = BASE_DIR) -> None:
    """
    Start a phase and create metadata.

    Args:
        feature: Feature name
        phase: Phase to start
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)

    # Read manifest
    manifest = read_manifest(feature_dir)

    # Check phase not already started/completed
    current_status = manifest.phases[phase.value].status
    if current_status != PhaseStatus.PENDING:
        raise PhaseStateError(phase.value, current_status.value, PhaseStatus.PENDING.value)

    # Update manifest
    manifest.current_phase = phase.value
    manifest.phases[phase.value].status = PhaseStatus.IN_PROGRESS
    manifest.status = FeatureStatus.IN_PROGRESS
    write_manifest(feature_dir, manifest)

    # Create phase metadata
    phase_dir = feature_dir / f"{phase.value}-phase"
    phase_metadata = PhaseMetadata(
        schema_version=SCHEMA_VERSION,
        phase=phase,
        status=PhaseStatus.IN_PROGRESS,
        started_at=get_timestamp()
    )
    write_phase_metadata(phase_dir, phase_metadata)

    logger.info(f"Started phase '{phase.value}' for feature '{feature}'")
    print(f"Phase '{phase.value}' started at {phase_metadata.started_at}")


def cmd_complete_phase(feature: str, phase: Phase, summary: str, base_dir: Path = BASE_DIR) -> None:
    """
    Complete a phase with summary and auto-capture git diff.

    Args:
        feature: Feature name
        phase: Phase to complete
        summary: Human-readable summary
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)

    # Read manifest
    manifest = read_manifest(feature_dir)

    # Check phase is in progress
    current_status = manifest.phases[phase.value].status
    if current_status != PhaseStatus.IN_PROGRESS:
        raise PhaseStateError(phase.value, current_status.value, PhaseStatus.IN_PROGRESS.value)

    # Read phase metadata
    phase_dir = feature_dir / f"{phase.value}-phase"
    phase_metadata = read_phase_metadata(phase_dir)

    # Auto-capture git diff
    diff_path = phase_dir / "git-diff.patch"
    capture_git_diff(diff_path)

    # Update phase metadata
    phase_metadata.status = PhaseStatus.COMPLETED
    phase_metadata.completed_at = get_timestamp()
    phase_metadata.summary = summary
    write_phase_metadata(phase_dir, phase_metadata)

    # Update manifest
    manifest.current_phase = None
    manifest.phases[phase.value].status = PhaseStatus.COMPLETED
    write_manifest(feature_dir, manifest)

    logger.info(f"Completed phase '{phase.value}' for feature '{feature}'")
    print(f"Phase '{phase.value}' completed at {phase_metadata.completed_at}")
    print(f"Summary: {summary}")


def cmd_capture_logs(
    feature: str,
    phase: Phase,
    build_log: Optional[Path] = None,
    test_log: Optional[Path] = None,
    base_dir: Path = BASE_DIR
) -> None:
    """
    Capture build and test logs to phase directory.

    Args:
        feature: Feature name
        phase: Phase name
        build_log: Optional explicit build log path
        test_log: Optional explicit test log path
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)
    phase_dir = feature_dir / f"{phase.value}-phase"

    # Auto-detect if not specified
    if build_log is None or test_log is None:
        build_dir = Path("build")
        tmp_dir = Path("/tmp")
        detected_build, detected_test = auto_detect_logs(build_dir, tmp_dir)

        if build_log is None:
            build_log = detected_build
        if test_log is None:
            test_log = detected_test

    # Copy build log
    build_dest = phase_dir / "build-output.log"
    if build_log and build_log.exists():
        shutil.copy2(build_log, build_dest)
        logger.info(f"Copied build log: {build_log} -> {build_dest}")
    else:
        build_dest.write_text("# Build log not found - placeholder created\n")
        logger.warning(f"Build log not found, created placeholder: {build_dest}")

    # Copy test log
    test_dest = phase_dir / "test-results.log"
    if test_log and test_log.exists():
        shutil.copy2(test_log, test_dest)
        logger.info(f"Copied test log: {test_log} -> {test_dest}")
    else:
        test_dest.write_text("# Test log not found - placeholder created\n")
        logger.warning(f"Test log not found, created placeholder: {test_dest}")

    print(f"Logs captured to {phase_dir}")


def cmd_record_files(
    feature: str,
    phase: Phase,
    list_name: str,
    files: list[str],
    base_dir: Path = BASE_DIR
) -> None:
    """
    Record file paths to phase-specific list.

    Args:
        feature: Feature name
        phase: Phase name
        list_name: Output filename
        files: List of file paths to record
        base_dir: Base directory for artifacts
    """
    if not files:
        raise ValueError("No files specified for --files parameter")

    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)
    phase_dir = feature_dir / f"{phase.value}-phase"

    # Write file list
    list_path = phase_dir / list_name
    list_path.write_text("\n".join(files) + "\n")

    logger.info(f"Recorded {len(files)} files to {list_path}")
    print(f"Recorded {len(files)} files to {list_path}")


def cmd_capture_diff(
    feature: str,
    phase: Phase,
    since_commit: str = "HEAD",
    base_dir: Path = BASE_DIR
) -> None:
    """
    Manually capture git diff.

    Args:
        feature: Feature name
        phase: Phase name
        since_commit: Commit to diff against
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)
    phase_dir = feature_dir / f"{phase.value}-phase"

    diff_path = phase_dir / "git-diff.patch"
    success = capture_git_diff(diff_path, since_commit)

    if success:
        print(f"Git diff captured to {diff_path}")
    else:
        print(f"Warning: Git diff failed, placeholder created at {diff_path}")


def cmd_status(feature: str, base_dir: Path = BASE_DIR) -> None:
    """
    Show current workflow state.

    Args:
        feature: Feature name
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)

    manifest = read_manifest(feature_dir)

    print(f"\nFeature: {manifest.feature_name} ({manifest.feature_impl_dir})")
    print(f"Created: {manifest.created_at}")
    print(f"Current Phase: {manifest.current_phase or 'None'}")
    print(f"Overall Status: {manifest.status.value}")

    # Warn if schema version mismatch
    if manifest.schema_version != SCHEMA_VERSION:
        print(f"⚠ Warning: Manifest schema version {manifest.schema_version} differs from current {SCHEMA_VERSION}")
    print("\nPhase Status:")

    for phase_name in ["red", "green", "refactor"]:
        phase_info = manifest.phases[phase_name]
        status_symbol = "✓" if phase_info.status == PhaseStatus.COMPLETED else \
                       "▶" if phase_info.status == PhaseStatus.IN_PROGRESS else " "

        phase_dir = feature_dir / f"{phase_name}-phase"

        # Try to read phase metadata for details
        details = ""
        if (phase_dir / "metadata.json").exists():
            try:
                metadata = read_phase_metadata(phase_dir)
                if metadata.status == PhaseStatus.COMPLETED:
                    details = f" ({metadata.started_at} - {metadata.completed_at}) - \"{metadata.summary}\""
                elif metadata.status == PhaseStatus.IN_PROGRESS:
                    details = f" (started {metadata.started_at})"
            except MetadataCorruptedError:
                details = " [metadata corrupted]"

        print(f"{status_symbol} {phase_name:8} : {phase_info.status.value}{details}")

    # List artifacts
    print("\nArtifacts:")
    for phase_name in ["red", "green", "refactor"]:
        phase_dir = feature_dir / f"{phase_name}-phase"
        for artifact_file in phase_dir.iterdir():
            if artifact_file.is_file():
                if artifact_file.suffix == '.list':
                    # Count lines for .list files
                    line_count = len(artifact_file.read_text().strip().split('\n'))
                    print(f"- {phase_name}-phase/{artifact_file.name} ({line_count} files)")
                else:
                    print(f"- {phase_name}-phase/{artifact_file.name} (exists)")


def cmd_reset_phase(
    feature: str,
    phase: Phase,
    force: bool = False,
    keep_artifacts: bool = False,
    base_dir: Path = BASE_DIR
) -> None:
    """
    Reset a stuck/failed phase to pending.

    Args:
        feature: Feature name
        phase: Phase to reset
        force: Skip confirmation prompt
        keep_artifacts: Keep artifacts when resetting
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)

    manifest = read_manifest(feature_dir)
    current_status = manifest.phases[phase.value].status

    if current_status == PhaseStatus.PENDING:
        logger.warning(f"Phase '{phase.value}' already pending")
        print(f"Phase '{phase.value}' is already in pending state")
        return

    if current_status == PhaseStatus.COMPLETED and not force:
        logger.error(f"Phase '{phase.value}' is completed. Use --force to reset.")
        sys.exit(1)

    # Confirmation prompt
    if not force:
        print(f"\nWarning: Resetting phase '{phase.value}' will:")
        print(f"- Set status back to 'pending'")
        if not keep_artifacts:
            print(f"- Delete phase metadata")
            print(f"- Delete artifacts in {phase.value}-phase/ directory")
        print()
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            logger.info("Aborted.")
            sys.exit(2)

    # Update manifest
    manifest.phases[phase.value].status = PhaseStatus.PENDING
    if manifest.current_phase == phase.value:
        manifest.current_phase = None
    write_manifest(feature_dir, manifest)

    # Delete artifacts unless keeping
    if not keep_artifacts:
        phase_dir = feature_dir / f"{phase.value}-phase"
        for artifact in phase_dir.iterdir():
            if artifact.is_file():
                artifact.unlink()
                logger.info(f"Deleted: {artifact}")

    logger.info(f"Reset phase '{phase.value}' to pending")
    print(f"Phase '{phase.value}' reset to pending")


def cmd_validate(feature: str, base_dir: Path = BASE_DIR) -> None:
    """
    Validate artifact consistency.

    Args:
        feature: Feature name
        base_dir: Base directory for artifacts
    """
    feature_dir = get_feature_dir(feature, base_dir)
    validate_feature_exists(feature_dir)

    errors = []
    warnings = []

    print(f"\nValidating feature: {feature}\n")

    # Check manifest exists and is valid
    try:
        manifest = read_manifest(feature_dir)
        print(f"✓ manifest.json valid (schema v{manifest.schema_version})")
    except MetadataCorruptedError as e:
        errors.append(f"manifest.json corrupted: {e}")
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Check phase directories exist
    all_dirs_exist = True
    for phase_name in ["red", "green", "refactor"]:
        phase_dir = feature_dir / f"{phase_name}-phase"
        if not phase_dir.exists():
            errors.append(f"Missing directory: {phase_dir}")
            all_dirs_exist = False

    if all_dirs_exist:
        print("✓ Phase directories exist")

    # Check phase metadata consistency
    in_progress_count = 0
    for phase_name in ["red", "green", "refactor"]:
        phase_info = manifest.phases[phase_name]
        phase_dir = feature_dir / f"{phase_name}-phase"
        metadata_path = phase_dir / "metadata.json"

        if phase_info.status == PhaseStatus.IN_PROGRESS:
            in_progress_count += 1
            if not metadata_path.exists():
                warnings.append(
                    f"{phase_name}-phase marked 'in_progress' but no metadata.json found"
                )

        if metadata_path.exists():
            try:
                metadata = read_phase_metadata(phase_dir)

                # Check status consistency
                if metadata.status.value != phase_info.status.value:
                    errors.append(
                        f"{phase_name}-phase: metadata status '{metadata.status.value}' "
                        f"doesn't match manifest status '{phase_info.status.value}'"
                    )

                # Check timestamps are logical
                if metadata.completed_at and metadata.started_at:
                    # Basic string comparison works for ISO 8601
                    if metadata.completed_at < metadata.started_at:
                        errors.append(
                            f"{phase_name}-phase: completed_at < started_at"
                        )
            except MetadataCorruptedError as e:
                errors.append(f"{phase_name}-phase: {e}")

    # Check only one phase in progress
    if in_progress_count > 1:
        errors.append(f"Multiple phases in_progress: {in_progress_count}")

    # Check current_phase consistency
    if manifest.current_phase:
        current_status = manifest.phases[manifest.current_phase].status
        if current_status != PhaseStatus.IN_PROGRESS:
            errors.append(
                f"current_phase='{manifest.current_phase}' but phase status='{current_status.value}' "
                "(expected 'in_progress')"
            )

    if not errors and not warnings:
        print("✓ Phase metadata consistent")

    # Print warnings
    for warning in warnings:
        print(f"⚠ Warning: {warning}")

    # Print errors
    for error in errors:
        print(f"✗ Error: {error}")

    # Summary
    print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        sys.exit(1)


# ============================================================================
# CLI Setup
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="TDD Artifacts Management Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True

    # init command
    init_parser = subparsers.add_parser('init', help='Initialize feature artifact directory')
    init_parser.add_argument('--feature', required=True, help='Feature name')
    init_parser.add_argument('--base-dir', type=Path, default=BASE_DIR,
                            help=f'Base directory for artifacts (default: {BASE_DIR})')

    # start-phase command
    start_parser = subparsers.add_parser('start-phase', help='Start a phase')
    start_parser.add_argument('--feature', required=True, help='Feature name')
    start_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                             help='Phase to start')

    # complete-phase command
    complete_parser = subparsers.add_parser('complete-phase', help='Complete a phase')
    complete_parser.add_argument('--feature', required=True, help='Feature name')
    complete_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                                help='Phase to complete')
    complete_parser.add_argument('--summary', required=True, help='Phase completion summary')

    # capture-logs command
    logs_parser = subparsers.add_parser('capture-logs', help='Capture build/test logs')
    logs_parser.add_argument('--feature', required=True, help='Feature name')
    logs_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                            help='Phase name')
    logs_parser.add_argument('--build-log', type=Path, help='Build log path')
    logs_parser.add_argument('--test-log', type=Path, help='Test log path')

    # record-files command
    files_parser = subparsers.add_parser('record-files', help='Record file paths')
    files_parser.add_argument('--feature', required=True, help='Feature name')
    files_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                             help='Phase name')
    files_parser.add_argument('--list-name', required=True, help='List filename')
    files_parser.add_argument('--files', nargs='+', required=True, help='File paths')

    # capture-diff command
    diff_parser = subparsers.add_parser('capture-diff', help='Capture git diff')
    diff_parser.add_argument('--feature', required=True, help='Feature name')
    diff_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                            help='Phase name')
    diff_parser.add_argument('--since-commit', default='HEAD', help='Commit to diff against')

    # status command
    status_parser = subparsers.add_parser('status', help='Show workflow state')
    status_parser.add_argument('--feature', required=True, help='Feature name')

    # reset-phase command
    reset_parser = subparsers.add_parser('reset-phase', help='Reset phase to pending')
    reset_parser.add_argument('--feature', required=True, help='Feature name')
    reset_parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'],
                             help='Phase to reset')
    reset_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    reset_parser.add_argument('--keep-artifacts', action='store_true',
                             help='Keep artifacts when resetting')

    # validate command
    validate_parser = subparsers.add_parser('validate', help='Validate artifact consistency')
    validate_parser.add_argument('--feature', required=True, help='Feature name')

    return parser


def main() -> None:
    """Main entry point with exception handling."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == 'init':
            cmd_init(args.feature, args.base_dir)

        elif args.command == 'start-phase':
            phase = validate_phase(args.phase)
            cmd_start_phase(args.feature, phase)

        elif args.command == 'complete-phase':
            phase = validate_phase(args.phase)
            cmd_complete_phase(args.feature, phase, args.summary)

        elif args.command == 'capture-logs':
            phase = validate_phase(args.phase)
            cmd_capture_logs(args.feature, phase, args.build_log, args.test_log)

        elif args.command == 'record-files':
            phase = validate_phase(args.phase)
            cmd_record_files(args.feature, phase, args.list_name, args.files)

        elif args.command == 'capture-diff':
            phase = validate_phase(args.phase)
            cmd_capture_diff(args.feature, phase, args.since_commit)

        elif args.command == 'status':
            cmd_status(args.feature)

        elif args.command == 'reset-phase':
            phase = validate_phase(args.phase)
            cmd_reset_phase(args.feature, phase, args.force, args.keep_artifacts)

        elif args.command == 'validate':
            cmd_validate(args.feature)

    except FeatureNotFoundError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        print(f"  Run: scripts/tdd_artifacts.py init --feature {e.feature_name}", file=sys.stderr)
        sys.exit(1)

    except InvalidPhaseError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    except PhaseStateError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        if e.expected_status == PhaseStatus.PENDING.value:
            print(f"  Complete it first: scripts/tdd_artifacts.py complete-phase "
                  f"--feature <feature> --phase {e.phase} --summary \"...\"", file=sys.stderr)
        sys.exit(3)

    except TDDArtifactsError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except ValueError as e:
        logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    except KeyboardInterrupt:
        print("\nAborted by user", file=sys.stderr)
        sys.exit(130)


# Allow script to be imported for testing without executing main()
# This enables pytest to import functions without running CLI
if __name__ == '__main__':
    main()
