"""Tests for GitAnalyzer."""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from pyscan_viz.git_analyzer import GitAnalyzer, BlameInfo
from pyscan.config import GitPlatformConfig


class TestBlameInfo:
    """Tests for BlameInfo dataclass."""

    def test_is_newer_than(self):
        """Test comparing commit dates."""
        older = BlameInfo(
            commit_hash="abc123",
            author="John Doe",
            author_email="john@example.com",
            commit_date=datetime(2025, 1, 1),
            subject="Old commit"
        )
        newer = BlameInfo(
            commit_hash="def456",
            author="Jane Smith",
            author_email="jane@example.com",
            commit_date=datetime(2025, 1, 2),
            subject="New commit"
        )

        assert newer.is_newer_than(older)
        assert not older.is_newer_than(newer)


class TestGitAnalyzer:
    """Tests for GitAnalyzer class."""

    def test_check_git_repo_valid(self, tmp_path):
        """Test detecting a valid Git repository."""
        # Initialize a git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(tmp_path))
        assert analyzer.is_git_repo is True

    def test_check_git_repo_invalid(self, tmp_path):
        """Test detecting a non-Git directory."""
        # tmp_path is not a git repo
        analyzer = GitAnalyzer(str(tmp_path))
        assert analyzer.is_git_repo is False

    def test_detect_platform_github(self):
        """Test detecting GitHub platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "git@github.com:user/repo.git"
        assert analyzer._detect_platform() == 'github'

        analyzer.remote_url = "https://github.com/user/repo.git"
        assert analyzer._detect_platform() == 'github'

    def test_detect_platform_gitlab(self):
        """Test detecting GitLab platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "git@gitlab.com:user/repo.git"
        assert analyzer._detect_platform() == 'gitlab'

        analyzer.remote_url = "https://gitlab.com/user/repo.git"
        assert analyzer._detect_platform() == 'gitlab'

    def test_detect_platform_gitee(self):
        """Test detecting Gitee platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "git@gitee.com:user/repo.git"
        assert analyzer._detect_platform() == 'gitee'

    def test_detect_platform_bitbucket(self):
        """Test detecting Bitbucket platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://bitbucket.org/user/repo.git"
        assert analyzer._detect_platform() == 'bitbucket'

    def test_detect_platform_unknown(self):
        """Test detecting unknown platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://unknown.com/user/repo.git"
        assert analyzer._detect_platform() is None

    def test_parse_repo_path_ssh(self):
        """Test parsing repository path from SSH URL."""
        analyzer = GitAnalyzer(".")

        analyzer.remote_url = "git@github.com:user/repo.git"
        assert analyzer._parse_repo_path() == "user/repo"

        analyzer.remote_url = "git@gitlab.com:group/project.git"
        assert analyzer._parse_repo_path() == "group/project"

    def test_parse_repo_path_https(self):
        """Test parsing repository path from HTTPS URL."""
        analyzer = GitAnalyzer(".")

        analyzer.remote_url = "https://github.com/user/repo.git"
        assert analyzer._parse_repo_path() == "user/repo"

        analyzer.remote_url = "https://github.com/user/repo"
        assert analyzer._parse_repo_path() == "user/repo"

    def test_parse_repo_path_ssh_protocol(self):
        """Test parsing repository path from ssh:// URL."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "ssh://git@github.com/user/repo.git"
        assert analyzer._parse_repo_path() == "user/repo"

    def test_generate_commit_url_github(self):
        """Test generating GitHub commit URL."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://github.com/user/repo.git"
        analyzer.platform = 'github'

        url = analyzer._generate_commit_url("abc123def456")
        assert url == "https://github.com/user/repo/commit/abc123def456"

    def test_generate_commit_url_gitlab(self):
        """Test generating GitLab commit URL."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://gitlab.com/user/project.git"
        analyzer.platform = 'gitlab'

        url = analyzer._generate_commit_url("abc123")
        assert url == "https://gitlab.com/user/project/-/commit/abc123"

    def test_generate_commit_url_gitee(self):
        """Test generating Gitee commit URL."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://gitee.com/user/repo.git"
        analyzer.platform = 'gitee'

        url = analyzer._generate_commit_url("abc123")
        assert url == "https://gitee.com/user/repo/commit/abc123"

    def test_generate_commit_url_bitbucket(self):
        """Test generating Bitbucket commit URL."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://bitbucket.org/user/repo.git"
        analyzer.platform = 'bitbucket'

        url = analyzer._generate_commit_url("abc123")
        assert url == "https://bitbucket.org/user/repo/commits/abc123"

    def test_generate_commit_url_no_platform(self):
        """Test generating commit URL with unknown platform."""
        analyzer = GitAnalyzer(".")
        analyzer.remote_url = "https://unknown.com/user/repo.git"
        analyzer.platform = None

        url = analyzer._generate_commit_url("abc123")
        assert url is None

    def test_format_relative_date(self):
        """Test formatting relative dates."""
        analyzer = GitAnalyzer(".")
        now = datetime.now()

        # Just now
        recent = now - timedelta(seconds=30)
        assert "just now" in analyzer._format_relative_date(recent)

        # Minutes ago
        minutes_ago = now - timedelta(minutes=5)
        result = analyzer._format_relative_date(minutes_ago)
        assert "minute" in result

        # Hours ago
        hours_ago = now - timedelta(hours=3)
        result = analyzer._format_relative_date(hours_ago)
        assert "hour" in result

        # Yesterday
        yesterday = now - timedelta(days=1)
        assert "yesterday" in analyzer._format_relative_date(yesterday)

        # Days ago
        days_ago = now - timedelta(days=5)
        result = analyzer._format_relative_date(days_ago)
        assert "days ago" in result

        # Weeks ago
        weeks_ago = now - timedelta(weeks=2)
        result = analyzer._format_relative_date(weeks_ago)
        assert "week" in result

        # Months ago
        months_ago = now - timedelta(days=60)
        result = analyzer._format_relative_date(months_ago)
        assert "month" in result

        # Years ago
        years_ago = now - timedelta(days=400)
        result = analyzer._format_relative_date(years_ago)
        assert "year" in result

    def test_parse_blame_output(self):
        """Test parsing git blame --line-porcelain output."""
        analyzer = GitAnalyzer(".")

        # Sample git blame output (porcelain format)
        blame_output = """a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0 1 1 1
author John Doe
author-mail <john@example.com>
author-time 1698000000
author-tz +0800
committer John Doe
committer-mail <john@example.com>
committer-time 1698000000
committer-tz +0800
summary Fix null pointer bug
previous b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1 test.py
filename test.py
\tdef process_data(data):
b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1 2 2 1
author Jane Smith
author-mail <jane@example.com>
author-time 1697000000
author-tz +0800
committer Jane Smith
committer-mail <jane@example.com>
committer-time 1697000000
committer-tz +0800
summary Add validation
filename test.py
\treturn data
"""

        result = analyzer._parse_blame_output(blame_output)

        # Verify parsing results
        assert len(result) == 2

        # Check line 1
        assert 1 in result
        blame_info_1 = result[1]
        assert blame_info_1.commit_hash == "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
        assert blame_info_1.author == "John Doe"
        assert blame_info_1.author_email == "john@example.com"
        assert blame_info_1.subject == "Fix null pointer bug"
        assert blame_info_1.commit_date == datetime.fromtimestamp(1698000000)

        # Check line 2
        assert 2 in result
        blame_info_2 = result[2]
        assert blame_info_2.commit_hash == "b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1"
        assert blame_info_2.author == "Jane Smith"
        assert blame_info_2.author_email == "jane@example.com"
        assert blame_info_2.subject == "Add validation"

        # Test is_newer_than
        assert blame_info_1.is_newer_than(blame_info_2)

    def test_blame_file_with_cache(self, tmp_path):
        """Test git blame file with caching mechanism."""
        import subprocess

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create a test file
        test_file = repo_dir / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n")

        # Add and commit
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create GitAnalyzer
        analyzer = GitAnalyzer(str(repo_dir))

        # First call - should execute git blame
        result1 = analyzer.blame_file("test.py")
        assert len(result1) == 2  # Two lines
        assert 1 in result1
        assert 2 in result1
        assert result1[1].author == "Test User"
        assert result1[1].author_email == "test@example.com"

        # Second call - should use cache
        result2 = analyzer.blame_file("test.py")
        assert result2 is result1  # Same object from cache

    def test_blame_file_not_found(self, tmp_path):
        """Test git blame for non-existent file."""
        import subprocess

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(repo_dir))

        # Try to blame a non-existent file
        result = analyzer.blame_file("nonexistent.py")
        assert result == {}

    def test_blame_file_not_git_repo(self, tmp_path):
        """Test git blame when not a git repository."""
        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()

        analyzer = GitAnalyzer(str(non_git_dir))
        assert analyzer.is_git_repo is False

        # Should return empty dict for non-git repos
        result = analyzer.blame_file("any_file.py")
        assert result == {}

    def test_get_bug_blame_info_single_line(self, tmp_path):
        """Test getting blame info for single-line bug."""
        import subprocess

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create and commit a test file
        test_file = repo_dir / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n")
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add hello'],
                      cwd=repo_dir, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(repo_dir))

        # Bug on single line
        bug = {
            'file_path': 'test.py',
            'start_line': 1,
            'end_line': 1
        }

        blame_info = analyzer.get_bug_blame_info(bug)
        assert blame_info is not None
        assert blame_info.author == "Test User"
        assert blame_info.subject == "Add hello"

    def test_get_bug_blame_info_multi_line_same_commit(self, tmp_path):
        """Test getting blame info for multi-line bug with same commit."""
        import subprocess

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create and commit a test file with multiple lines
        test_file = repo_dir / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n    return 42\n")
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add hello'],
                      cwd=repo_dir, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(repo_dir))

        # Bug spans lines 1-2 (same commit)
        bug = {
            'file_path': 'test.py',
            'start_line': 1,
            'end_line': 2
        }

        blame_info = analyzer.get_bug_blame_info(bug)
        assert blame_info is not None
        assert blame_info.author == "Test User"

    def test_get_bug_blame_info_multi_line_different_commits(self, tmp_path):
        """Test getting blame info for multi-line bug with different commits - should return newest."""
        import subprocess
        import time

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'User1'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'user1@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)

        # First commit - line 1
        test_file = repo_dir / "test.py"
        test_file.write_text("def hello():\n    pass\n")
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'First commit'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Wait a bit to ensure different timestamps
        time.sleep(1)

        # Second commit - modify line 2
        subprocess.run(['git', 'config', 'user.name', 'User2'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'user2@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)
        test_file.write_text("def hello():\n    print('Hello')\n")
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Second commit'],
                      cwd=repo_dir, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(repo_dir))

        # Bug spans lines 1-2 (different commits, line 2 is newer)
        bug = {
            'file_path': 'test.py',
            'start_line': 1,
            'end_line': 2
        }

        blame_info = analyzer.get_bug_blame_info(bug)
        assert blame_info is not None
        # Should return the newest commit (User2)
        assert blame_info.author == "User2"
        assert blame_info.subject == "Second commit"

    def test_enrich_bugs_with_git_info(self, tmp_path):
        """Test enriching multiple bugs with git information."""
        import subprocess

        # Create a temporary git repository
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/user/repo.git'],
                      cwd=repo_dir, check=True, capture_output=True)

        # Create and commit a test file
        test_file = repo_dir / "test.py"
        test_file.write_text("def hello():\n    print('Hello')\n    return 42\n")
        subprocess.run(['git', 'add', 'test.py'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add hello function'],
                      cwd=repo_dir, check=True, capture_output=True)

        analyzer = GitAnalyzer(str(repo_dir))

        # Create test bugs
        bugs = [
            {
                'bug_id': 'BUG_0001',
                'file_path': 'test.py',
                'start_line': 1,
                'end_line': 1
            },
            {
                'bug_id': 'BUG_0002',
                'file_path': 'test.py',
                'start_line': 2,
                'end_line': 2
            }
        ]

        # Enrich bugs
        enriched = analyzer.enrich_bugs_with_git_info(bugs)

        # Verify enrichment
        assert len(enriched) == 2

        # Check first bug
        assert enriched[0]['git_info'] is not None
        git_info = enriched[0]['git_info']
        assert 'hash' in git_info
        assert 'hash_full' in git_info
        assert git_info['author'] == 'Test User'
        assert git_info['email'] == 'test@example.com'
        assert git_info['subject'] == 'Add hello function'
        assert 'date' in git_info
        assert 'date_relative' in git_info
        assert 'url' in git_info
        assert 'github.com' in git_info['url']

        # Check second bug (should have same commit info due to caching)
        assert enriched[1]['git_info'] is not None
        assert enriched[1]['git_info']['author'] == 'Test User'

    def test_enrich_bugs_not_git_repo(self, tmp_path):
        """Test enriching bugs in non-git directory."""
        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()

        analyzer = GitAnalyzer(str(non_git_dir))

        bugs = [
            {
                'bug_id': 'BUG_0001',
                'file_path': 'test.py',
                'start_line': 1,
                'end_line': 1
            }
        ]

        # Should return original bugs unchanged
        enriched = analyzer.enrich_bugs_with_git_info(bugs)
        assert len(enriched) == 1
        # Original bugs should be returned (warning logged)

    def test_custom_platform_detection(self):
        """Test detecting custom platform."""
        custom_platform = GitPlatformConfig(
            name='company-gitlab',
            detect_pattern='gitlab.company.com',
            repo_path_regex=r'[:/]([^/:]+/[^/]+?)(?:\.git)?$',
            commit_url_template='https://gitlab.company.com/{repo_path}/-/commit/{hash}'
        )

        analyzer = GitAnalyzer('.', custom_platforms=[custom_platform])
        analyzer.remote_url = 'git@gitlab.company.com:team/project.git'

        # Should detect custom platform
        platform = analyzer._detect_platform()
        assert platform == 'company-gitlab'

    def test_custom_platform_override_builtin(self):
        """Test custom platform overrides builtin platform."""
        # Override github with custom URL template
        custom_github = GitPlatformConfig(
            name='github',
            detect_pattern='github.com',
            repo_path_regex=r'[:/]([^/:]+/[^/]+?)(?:\.git)?$',
            commit_url_template='https://custom-github-viewer.com/{repo_path}/commits/{hash}'
        )

        analyzer = GitAnalyzer('.', custom_platforms=[custom_github])
        analyzer.remote_url = 'git@github.com:user/repo.git'
        analyzer.platform = 'github'

        # Should use custom template
        url = analyzer._generate_commit_url('abc123def456')
        assert url == 'https://custom-github-viewer.com/user/repo/commits/abc123def456'
        assert 'custom-github-viewer.com' in url

    def test_custom_platform_parse_repo_path(self):
        """Test custom platform with custom regex."""
        # Azure DevOps style URL
        azure_platform = GitPlatformConfig(
            name='azure-devops',
            detect_pattern='dev.azure.com',
            repo_path_regex=r'dev\.azure\.com/([^/]+/[^/]+/_git/[^/]+)',
            commit_url_template='https://dev.azure.com/{repo_path}/commit/{hash}'
        )

        analyzer = GitAnalyzer('.', custom_platforms=[azure_platform])
        analyzer.remote_url = 'https://dev.azure.com/myorg/myproject/_git/myrepo'
        analyzer.platform = 'azure-devops'

        # Should parse using custom regex
        repo_path = analyzer._parse_repo_path()
        assert repo_path == 'myorg/myproject/_git/myrepo'

        # Should generate URL correctly
        url = analyzer._generate_commit_url('abc123')
        assert url == 'https://dev.azure.com/myorg/myproject/_git/myrepo/commit/abc123'

    def test_builtin_platforms_still_work(self):
        """Test that builtin platforms work without custom config."""
        analyzer = GitAnalyzer('.')
        analyzer.remote_url = 'git@github.com:user/repo.git'

        # Should detect builtin platform
        platform = analyzer._detect_platform()
        assert platform == 'github'

        # Should parse repo path
        repo_path = analyzer._parse_repo_path()
        assert repo_path == 'user/repo'

        # Should generate URL
        analyzer.platform = 'github'
        url = analyzer._generate_commit_url('abc123')
        assert url == 'https://github.com/user/repo/commit/abc123'
