"""Version parsing and constraint checking."""

import logging
import re

logger = logging.getLogger(__name__)


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse semantic version string to tuple of integers."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def check_version_constraint(installed: str, constraint: str) -> bool:
    """Check if installed version satisfies constraint."""
    installed_ver = parse_version(installed)

    # Handle different constraint operators
    if constraint.startswith("^"):
        # Caret: Allow changes that do not modify left-most non-zero digit
        required_ver = parse_version(constraint[1:])
        if required_ver[0] > 0:
            # ^1.2.3 := >=1.2.3 <2.0.0
            return installed_ver >= required_ver and installed_ver[0] == required_ver[0]
        elif required_ver[1] > 0:
            # ^0.2.3 := >=0.2.3 <0.3.0
            return (
                installed_ver >= required_ver
                and installed_ver[0] == 0
                and installed_ver[1] == required_ver[1]
            )
        else:
            # ^0.0.3 := >=0.0.3 <0.0.4
            return installed_ver == required_ver

    elif constraint.startswith("~"):
        # Tilde: Allow patch-level changes
        required_ver = parse_version(constraint[1:])
        # ~1.2.3 := >=1.2.3 <1.3.0
        return (
            installed_ver >= required_ver
            and installed_ver[0] == required_ver[0]
            and installed_ver[1] == required_ver[1]
        )

    elif constraint.startswith(">="):
        required_ver = parse_version(constraint[2:])
        return installed_ver >= required_ver

    elif constraint.startswith("<="):
        required_ver = parse_version(constraint[2:])
        return installed_ver <= required_ver

    elif constraint.startswith(">"):
        required_ver = parse_version(constraint[1:])
        return installed_ver > required_ver

    elif constraint.startswith("<"):
        required_ver = parse_version(constraint[1:])
        return installed_ver < required_ver

    elif constraint.startswith("==") or constraint[0].isdigit():
        # Exact match
        required_ver = parse_version(constraint[2:] if constraint.startswith("==") else constraint)
        return installed_ver == required_ver

    else:
        logger.warning(f"Unknown version constraint format: {constraint}")
        return True  # Allow by default if constraint format unknown
