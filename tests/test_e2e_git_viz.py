"""End-to-end tests for git visualization feature."""
import pytest
import subprocess
import json
from pathlib import Path


class TestGitVizE2E:
    """End-to-end tests for git visualization."""

    def test_git_enrich_with_valid_repo(self, tmp_path):
        """Test git enrichment with a valid git repository (via config)."""
        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/test/repo.git'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create a test Python file
        test_file = repo_dir / "test.py"
        test_file.write_text("def buggy_function():\n    x = None\n    return x.value\n")

        # Add and commit
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add buggy function'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create a config file with git_enrich enabled
        config_file = repo_dir / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test"
  model: "gpt-4"

viz:
  embed_source: true
  git_enrich: true
""")

        # Create a mock pyscan report
        report_file = repo_dir / "report.json"
        report = {
            "timestamp": "2025-01-01T00:00:00",
            "scan_directory": str(repo_dir),
            "bugs": [
                {
                    "bug_id": "BUG_0001",
                    "function_name": "buggy_function",
                    "file_path": "test.py",
                    "function_start_line": 1,
                    "function_end_line": 3,
                    "severity": "high",
                    "bug_type": "NullPointerError",
                    "description": "Potential null pointer dereference",
                    "start_line": 3,
                    "end_line": 3,
                    "suggestion": "Check if x is None before accessing attributes",
                    "callers": [],
                    "callees": [],
                    "inferred_callers": []
                }
            ]
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f)

        # Import and use CLI
        from pyscan_viz.cli import main
        import sys

        # Mock sys.argv for CLI
        output_html = repo_dir / "output.html"
        original_argv = sys.argv
        try:
            sys.argv = ['pyscan_viz', str(report_file), '-o', str(output_html), '-c', str(config_file)]
            main()
        except SystemExit:
            pass  # CLI calls sys.exit(0) on success
        finally:
            sys.argv = original_argv

        # Verify HTML was generated
        assert output_html.exists(), "HTML output file was not generated"

        # Verify HTML contains git information
        html_content = output_html.read_text(encoding='utf-8')
        assert 'git_info' in html_content, "HTML should contain git_info data"
        assert 'Test User' in html_content or 'test@example.com' in html_content, \
            "HTML should contain commit author information"

    def test_git_enrich_without_git_repo(self, tmp_path):
        """Test git enrichment gracefully handles non-git directories."""
        # Create a non-git directory
        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()

        # Create a test Python file
        test_file = non_git_dir / "test.py"
        test_file.write_text("def test():\n    pass\n")

        # Create a config file with git_enrich enabled
        config_file = non_git_dir / "config.yaml"
        config_file.write_text("""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test"
  model: "gpt-4"

viz:
  embed_source: true
  git_enrich: true
""")

        # Create a mock pyscan report
        report_file = non_git_dir / "report.json"
        report = {
            "timestamp": "2025-01-01T00:00:00",
            "scan_directory": str(non_git_dir),
            "bugs": [
                {
                    "bug_id": "BUG_0001",
                    "function_name": "test",
                    "file_path": "test.py",
                    "function_start_line": 1,
                    "function_end_line": 2,
                    "severity": "low",
                    "bug_type": "TestBug",
                    "description": "Test bug",
                    "start_line": 2,
                    "end_line": 2,
                    "suggestion": "Fix it",
                    "callers": [],
                    "callees": [],
                    "inferred_callers": []
                }
            ]
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f)

        # Import and use CLI
        from pyscan_viz.cli import main
        import sys

        # Mock sys.argv for CLI
        output_html = non_git_dir / "output.html"
        original_argv = sys.argv
        try:
            sys.argv = ['pyscan_viz', str(report_file), '-o', str(output_html), '-c', str(config_file)]
            main()
        except SystemExit:
            pass  # CLI calls sys.exit(0) on success
        finally:
            sys.argv = original_argv

        # Verify HTML was still generated (graceful degradation)
        assert output_html.exists(), "HTML output file should be generated even without git"

        # Verify HTML was generated correctly
        html_content = output_html.read_text(encoding='utf-8')
        assert 'BUG_0001' in html_content, "HTML should contain bug information"
