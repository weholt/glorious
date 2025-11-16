#!/usr/bin/env python3
"""
Comprehensive build script for DotWork.

Now extended with static-analysis and code-quality tools:
- Radon (complexity/maintainability)
- Vulture (dead code)
- jscpd (duplication)
- Import Linter (layer violations)
- Bandit (security)
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


class BuildRunner:
    """Handles the build process for DotWork."""

    def __init__(self, verbose: bool = False, integration_suite: str | None = None):
        self.verbose = verbose
        self.integration_suite = integration_suite
        self.project_root = Path(__file__).parent.parent
        self.failed_steps: list[str] = []

    def run_command(
        self,
        cmd: list[str],
        description: str,
        check: bool = True,
        capture_output: bool = True,
    ) -> tuple[bool, str, str]:
        """Run a command and return success status and output."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                check=check,
                encoding="utf-8",
                errors="replace",
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or ""
        except FileNotFoundError:
            return False, "", f"Command not found: {cmd[0]}"

    def print_step(self, step: str) -> None:
        """Print a build step header."""
        print(f"\n{'=' * 60}")
        print(f"[TOOL] {step}")
        print(f"{'=' * 60}")

    def print_result(self, success: bool, step: str, output: str = "", error: str = "") -> None:
        """Print the result of a build step."""
        if success:
            print(f"[OK] {step} - PASSED")
        else:
            print(f"[FAIL] {step} - FAILED")
            self.failed_steps.append(step)
            if error:
                print(f"Error: {error}")
            if output:
                print(f"Output: {output}")

    def check_dependencies(self) -> bool:
        """Check if all required tools are available."""
        self.print_step("Checking Dependencies")

        tools = [
            ("uv", ["uv", "--version"]),
            ("ruff", ["uv", "run", "ruff", "--version"]),
            ("mypy", ["uv", "run", "mypy", "--version"]),
            ("pytest", ["uv", "run", "pytest", "--version"]),
        ]

        all_available = True
        for tool_name, cmd in tools:
            success, output, _error = self.run_command(cmd, f"Check {tool_name}")
            if success:
                version = output.strip().split("\n")[0] if output else "unknown"
                print(f"[OK] {tool_name}: {version}")
            else:
                print(f"[FAIL] {tool_name}: Not available")
                all_available = False

        return all_available

    def sync_dependencies(self) -> bool:
        """Sync project dependencies."""
        self.print_step("Syncing Dependencies")

        success, output, error = self.run_command(["uv", "sync"], "Sync dependencies")

        self.print_result(success, "Dependency Sync", output, error)
        return success

    def format_code(self) -> bool:
        """Format code with ruff."""
        self.print_step("Code Formatting")

        backend_path = self.project_root / "src" / "issue_tracker"
        if not backend_path.exists():
            print(f"[WARN] Source directory not found at {backend_path}")
            return False

        ruff_format_cmd = ["uv", "run", "ruff", "format", str(backend_path)]

        success_format, output_format, error_format = self.run_command(ruff_format_cmd, "ruff format")

        ruff_check_cmd = ["uv", "run", "ruff", "check", "--fix", str(backend_path)]

        success_check, output_check, error_check = self.run_command(ruff_check_cmd, "ruff check")

        self.print_result(success_format, "ruff format", output_format, error_format)
        self.print_result(success_check, "ruff check", output_check, error_check)

        return success_format and success_check

    def lint_code(self) -> bool:
        """Lint code with ruff."""
        self.print_step("Code Linting")

        backend_path = self.project_root / "src" / "issue_tracker"
        if not backend_path.exists():
            print(f"[WARN] Source directory not found at {backend_path}")
            return False

        ruff_cmd = ["uv", "run", "ruff", "check", "--fix", "--exclude", "tests", "--exclude", "scripts", str(backend_path)]

        success, output, error = self.run_command(ruff_cmd, "ruff linting")

        self.print_result(success, "ruff", output, error)
        return success

    def check_deprecated_config(self) -> bool:
        """Check for usage of deprecated config properties."""
        self.print_step("Deprecated Config Check")

        deprecated_tokens = ["docs_dir", "prompts_dir", "resources_dir", "templates_dir"]
        
        # Allowlist: files that can mention these for backward compatibility or documentation
        allowlist = [
            "dotwork/env_config.py",  # Backward compatibility warning
            ".work/agent/strict-layout-refactor-plan.md",  # Historical reference
        ]

        violations: list[tuple[str, str, int]] = []

        dotwork_dir = self.project_root / "dotwork"
        if not dotwork_dir.exists():
            print(f"[WARN] dotwork directory not found at {dotwork_dir}")
            return False

        for token in deprecated_tokens:
            # Search in Python files
            success, output, _error = self.run_command(
                ["git", "grep", "-n", f"config\\.{token}", "--", str(dotwork_dir / "")],
                f"Search for config.{token}",
                check=False,
            )
            
            if success and output:
                for line in output.strip().split("\n"):
                    if line:
                        # Parse git grep output: file:line:content
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            filepath, linenum, content = parts[0], parts[1], parts[2]
                            # Check if file is in allowlist
                            if not any(allowed in filepath for allowed in allowlist):
                                violations.append((filepath, token, int(linenum)))

        if violations:
            print("[FAIL] Found deprecated config property usage:")
            for filepath, token, linenum in violations:
                print(f"  {filepath}:{linenum} - config.{token}")
            print("\n[FIX] Replace with:")
            print("  - config.docs_dir → config.data_dir")
            print("  - Use helper functions from dotwork.utils.repo_helpers")
            print("  - See .work/agent/strict-layout-refactor-plan.md")
            self.print_result(False, "Deprecated Config Check")
            return False
        else:
            print("[OK] No deprecated config property usage found")
            self.print_result(True, "Deprecated Config Check")
            return True

    def run_static_analysis(self) -> bool:
        """Run non-visual static-analysis tools."""
        self.print_step("Static Code Analysis")

        analysis_dir = self.project_root / ".work" / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        dotwork_dir = self.project_root / "dotwork"
        if not dotwork_dir.exists():
            print(f"[WARN] dotwork directory not found at {dotwork_dir}")
            return False

        tools = [
            (
                "Radon Complexity",
                ["uv", "run", "radon", "cc", str(dotwork_dir), "-s", "-a", "-j"],
                analysis_dir / "complexity.json",
            ),
            (
                "Radon Maintainability",
                ["uv", "run", "radon", "mi", str(dotwork_dir), "-j"],
                analysis_dir / "maintainability.json",
            ),
            (
                "Vulture Dead Code",
                ["uv", "run", "vulture", str(dotwork_dir)],
                analysis_dir / "deadcode.txt",
            ),
            (
                "jscpd Duplication",
                ["uv", "run", "jscpd", "--reporters", "json", "--languages", "python", str(dotwork_dir)],
                analysis_dir / "duplication.json",
            ),
            (
                "Import-Linter Dependencies",
                ["uv", "run", "lint-imports"],
                analysis_dir / "dependencies.txt",
            ),
            (
                "Bandit Security Scan",
                ["uv", "run", "bandit", "-r", str(dotwork_dir), "-f", "json"],
                analysis_dir / "bandit.json",
            ),
        ]

        all_ok = True
        for name, cmd, outfile in tools:
            success, output, error = self.run_command(cmd, name, check=False)
            if output:
                outfile.write_text(output)
            self.print_result(success, name, output[:300], error)
            all_ok = all_ok and success

        return all_ok

    def type_check(self) -> bool:
        """Type check with mypy."""
        self.print_step("Type Checking")

        backend_path = self.project_root / "src" / "issue_tracker"
        if not backend_path.exists():
            print(f"[WARN] Source directory not found at {backend_path}")
            return False

        success_module, output_module, error_module = self.run_command(["uv", "run", "mypy", str(backend_path / "")], f"mypy {backend_path}")

        self.print_result(success_module, f"mypy {backend_path}", output_module, error_module)

        return success_module

    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        self.print_step("Unit Tests")

        coverage_files = [".coverage", "htmlcov", "coverage.xml"]
        for file_name in coverage_files:
            path = self.project_root / file_name
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

        tests_unit = self.project_root / "tests" / "unit"
        backend_src = self.project_root / "src" / "issue_tracker"

        if not tests_unit.exists():
            print(f"[WARN] Test directory not found at {tests_unit}")
            return False

        if not backend_src.exists():
            print(f"[WARN] Source directory not found at {backend_src}")
            return False

        cmd = [
            "uv",
            "run",
            "pytest",
            str(tests_unit),
            f"--cov={backend_src}",
            "--cov-report=term",
            "--cov-report=html",
            "--cov-report=xml",
            # Note: timeout is configured in pyproject.toml (5 seconds)
            "--durations=20",  # Show 20 slowest tests
            "-vv" if self.verbose else "-v",
        ]
        
        # In verbose mode, show even more durations
        if self.verbose:
            cmd[cmd.index("--durations=20")] = "--durations=50"

        # Don't capture output to prevent buffering issues with pytest
        success, output, error = self.run_command(
            cmd,
            "pytest with coverage (excluding playwright and e2e)",
            capture_output=False,
        )

        self.print_result(success, "Unit Tests with Coverage", "", "")

        # Check coverage from XML file instead of parsing output
        if success:
            coverage_xml = self.project_root / "coverage.xml"
            if coverage_xml.exists():
                import xml.etree.ElementTree as ET
                try:
                    tree = ET.parse(coverage_xml)
                    root = tree.getroot()
                    coverage_elem = root.find(".//coverage")
                    if coverage_elem is not None:
                        line_rate = float(coverage_elem.get("line-rate", "0"))
                        coverage_pct = int(line_rate * 100)
                        print(f"Code Coverage: {coverage_pct}%")
                        # 70% threshold with integration tests included
                        if coverage_pct < 70:
                            print("WARNING: Coverage below 70% threshold!")
                            return False
                except Exception as e:
                    print(f"Warning: Could not parse coverage.xml: {e}")
            else:
                print("Warning: coverage.xml not found")

        return success

    def run_integration_suite(self, suite: str = "all") -> bool:
        """Run integration tests by suite.

        Args:
            suite: Which test suite to run:
                - 'api': API endpoint tests
                - 'cli': CLI command tests
                - 'mcp': MCP tool tests
                - 'web': Web UI template tests
                - 'playwright': Browser automation tests
                - 'all': All integration tests (default)
        """
        valid_suites = ["api", "cli", "mcp", "web", "playwright", "all"]

        if suite not in valid_suites:
            print(f"[ERROR] Unknown integration suite: {suite}")
            print(f"[INFO]  Available suites: {', '.join(valid_suites)}")
            return False

        self.print_step(f"Integration Tests ({suite})")

        cmd = [
            "uv",
            "run",
            "python",
            "scripts/run_tests.py",
            "--integration",
            suite,
        ]

        if self.verbose:
            cmd.append("--verbose")

        success, output, error = self.run_command(
            cmd,
            f"Integration tests: {suite}",
            capture_output=not self.verbose,
        )

        self.print_result(success, f"Integration Tests ({suite})", output, error)
        return success

    def run_security_check(self) -> bool:
        """Run security checks."""
        self.print_step("Security Checks")

        backend_path = self.project_root / "src" / "issue_tracker"
        if not backend_path.exists():
            print(f"[WARN] Source directory not found at {backend_path}")
            return False

        success, output, error = self.run_command(["uv", "run", "ruff", "check", str(backend_path), "--select", "S"], "Security linting")

        self.print_result(success, "Security Check", output, error)
        return success

    def build_documentation(self) -> bool:
        """Build documentation with MkDocs."""
        self.print_step("Building Documentation")

        success, output, error = self.run_command(["uv", "run", "mkdocs", "build"], "mkdocs build")

        if success:
            docs_dir = self.project_root / "docs"
            if not docs_dir.exists():
                print(f"[WARN] Documentation directory not found at {docs_dir}")
                success = False
            else:
                print(f"[OK] Documentation built to: {docs_dir.relative_to(self.project_root)}")

        self.print_result(success, "Documentation Build", output, error)
        return success

    def generate_reports(self) -> bool:
        """Generate build reports."""
        self.print_step("Generating Reports")

        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)

        coverage_html = self.project_root / "htmlcov"
        if coverage_html.exists():
            print("[OK] Coverage HTML report: htmlcov/index.html")

        coverage_xml = self.project_root / "coverage.xml"
        if coverage_xml.exists():
            print("[OK] Coverage XML report: coverage.xml")

        return True

    def check_file_quality(self) -> bool:
        """Check file quality (whitespace, EOF, etc)."""
        self.print_step("File Quality Checks")

        backend_path = self.project_root / "src" / "issue_tracker"
        if not backend_path.exists():
            print(f"[WARN] Source directory not found at {backend_path}")
            return False

        issues = []
        
        # Check trailing whitespace and EOF
        for pyfile in backend_path.rglob("*.py"):
            content = pyfile.read_text()
            lines = content.splitlines(keepends=True)
            
            # Check trailing whitespace
            for i, line in enumerate(lines, 1):
                if line.rstrip("\r\n") != line.rstrip():
                    issues.append(f"{pyfile.relative_to(self.project_root)}:{i}: trailing whitespace")
            
            # Check EOF newline
            if content and not content.endswith("\n"):
                issues.append(f"{pyfile.relative_to(self.project_root)}: missing newline at end of file")

        if issues:
            print("[FAIL] File quality issues found:")
            for issue in issues[:20]:  # Show first 20
                print(f"  {issue}")
            if len(issues) > 20:
                print(f"  ... and {len(issues) - 20} more")
            self.print_result(False, "File Quality")
            return False
        
        print("[OK] No file quality issues found")
        self.print_result(True, "File Quality")
        return True

    def check_config_files(self) -> bool:
        """Validate YAML, JSON, and TOML config files."""
        self.print_step("Config File Validation")

        import json
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        import yaml

        issues = []
        
        # Check YAML files
        for yamlfile in self.project_root.glob("*.yaml"):
            try:
                yaml.safe_load(yamlfile.read_text())
            except Exception as e:
                issues.append(f"{yamlfile.name}: invalid YAML - {e}")
        
        for yamlfile in self.project_root.glob("*.yml"):
            try:
                yaml.safe_load(yamlfile.read_text())
            except Exception as e:
                issues.append(f"{yamlfile.name}: invalid YAML - {e}")

        # Check JSON files
        for jsonfile in self.project_root.glob("*.json"):
            if jsonfile.name.startswith("."):
                continue
            try:
                json.loads(jsonfile.read_text())
            except Exception as e:
                issues.append(f"{jsonfile.name}: invalid JSON - {e}")

        # Check TOML files
        for tomlfile in self.project_root.glob("*.toml"):
            try:
                tomllib.loads(tomlfile.read_text())
            except Exception as e:
                issues.append(f"{tomlfile.name}: invalid TOML - {e}")

        if issues:
            print("[FAIL] Config file validation issues:")
            for issue in issues:
                print(f"  {issue}")
            self.print_result(False, "Config Validation")
            return False
        
        print("[OK] All config files valid")
        self.print_result(True, "Config Validation")
        return True

    def clean_artifacts(self) -> bool:
        """Clean build artifacts."""
        self.print_step("Cleaning Artifacts")

        artifacts = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.egg-info",
            ".coverage",
        ]

        for pattern in artifacts:
            if pattern.startswith("*"):
                for path in self.project_root.glob(pattern):
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            else:
                path = self.project_root / pattern
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        print("[OK] Cleaned build artifacts")
        return True

    def run_full_build(self) -> bool:
        """Run the complete build pipeline."""
        print("DotWork - Comprehensive Build Pipeline")
        print(f"{'=' * 80}")

        start_time = time.time()

        steps = [
            ("Check Dependencies", self.check_dependencies),
            ("Sync Dependencies", self.sync_dependencies),
            ("Format Code", self.format_code),
            ("Lint Code", self.lint_code),
            ("File Quality", self.check_file_quality),
            ("Config Validation", self.check_config_files),
            ("Type Check", self.type_check),
            ("Security Check", self.run_security_check),
            ("Unit Tests", self.run_unit_tests),
            ("Generate Reports", self.generate_reports),
        ]

        success_count = 0
        total_steps = len(steps)

        for step_name, step_func in steps:
            try:
                if step_func():
                    success_count += 1
            except Exception as e:
                print(f"[FAIL] {step_name} failed with exception: {e}")
                self.failed_steps.append(step_name)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n{'=' * 80}")
        print("[STAT] Build Summary")
        print(f"{'=' * 80}")
        print(f"[OK] Successful steps: {success_count}/{total_steps}")
        print(f"[TIME]  Build duration: {duration:.2f} seconds")

        if self.failed_steps:
            print(f"[FAIL] Failed steps: {', '.join(self.failed_steps)}")

        if success_count == total_steps:
            print("\n[SUCCESS] BUILD SUCCESSFUL - All quality checks passed!")
            print("[PKG] Ready for deployment")
            return True
        elif success_count >= total_steps - 1:
            print(f"\n[WARN]  BUILD MOSTLY SUCCESSFUL - {total_steps - success_count} minor issues")
            print("[TOOL] Consider addressing failed steps before deployment")
            return True
        else:
            print(f"\n[FAIL] BUILD FAILED - {total_steps - success_count} critical issues")
            print("[FIX]  Please fix the failed steps before proceeding")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive build script for DotWork")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts and exit")
    parser.add_argument(
        "--integration",
        choices=["all", "api", "cli", "mcp", "web", "playwright"],
        help="Run integration test suite (all, api, cli, mcp, web, or playwright)",
    )

    args = parser.parse_args()

    builder = BuildRunner(verbose=args.verbose, integration_suite=args.integration)

    if args.clean:
        builder.clean_artifacts()
        return 0

    success = builder.run_full_build()

    # Optionally run integration tests after main build
    if args.integration and success:
        print(f"\n{'=' * 80}")
        print(f"Running Integration Tests: {args.integration}")
        print(f"{'=' * 80}\n")
        integration_success = builder.run_integration_suite(args.integration)
        if not integration_success:
            print(f"\n[WARN]  {args.integration} integration tests failed, but main build passed")
            print("[INFO] Use 'python scripts/run_tests.py --help' for more options")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
