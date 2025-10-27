"""Git repository analyzer for extracting commit information from code."""
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BlameInfo:
    """Git blame information for a single line of code."""
    commit_hash: str        # Full commit hash
    author: str             # Author name
    author_email: str       # Author email
    commit_date: datetime   # Commit timestamp
    subject: str            # Commit message (first line)

    def is_newer_than(self, other: 'BlameInfo') -> bool:
        """Check if this commit is newer than another."""
        return self.commit_date > other.commit_date


class GitAnalyzer:
    """Analyzer for extracting Git commit information from a repository."""

    def __init__(self, repo_path: str):
        """
        Initialize Git analyzer.

        Args:
            repo_path: Path to the repository root directory
        """
        self.repo_path = Path(repo_path).resolve()
        self.is_git_repo = self._check_git_repo()
        self.remote_url = self._get_remote_url() if self.is_git_repo else None
        self.platform = self._detect_platform()
        self.blame_cache: Dict[str, Dict[int, BlameInfo]] = {}

    def _check_git_repo(self) -> bool:
        """
        Check if the directory is a Git repository.

        Returns:
            True if it's a valid Git repository, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True,
                timeout=5
            )
            return result.stdout.strip() == 'true'
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_remote_url(self) -> Optional[str]:
        """
        Get the remote URL of the origin.

        Returns:
            Remote URL string, or None if not found
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                check=True,
                timeout=5
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _detect_platform(self) -> Optional[str]:
        """
        Detect Git platform from remote URL.

        Returns:
            'github', 'gitlab', 'gitee', 'bitbucket', or None
        """
        if not self.remote_url:
            return None

        url_lower = self.remote_url.lower()

        if 'github.com' in url_lower:
            return 'github'
        elif 'gitlab.com' in url_lower:
            return 'gitlab'
        elif 'gitee.com' in url_lower:
            return 'gitee'
        elif 'bitbucket.org' in url_lower:
            return 'bitbucket'

        return None

    def _parse_repo_path(self) -> Optional[str]:
        """
        Parse repository path from remote URL.

        Examples:
            git@github.com:user/repo.git -> user/repo
            https://github.com/user/repo.git -> user/repo

        Returns:
            Repository path (user/repo), or None if parsing fails
        """
        if not self.remote_url:
            return None

        # Match user/repo pattern, with optional .git suffix
        # Pattern: [:/]([^/:]+/[^/]+?)(?:\.git)?$
        match = re.search(r'[:/]([^/:]+/[^/]+?)(?:\.git)?$', self.remote_url)
        if match:
            return match.group(1)

        return None

    def _generate_commit_url(self, commit_hash: str) -> Optional[str]:
        """
        Generate commit URL for the Git platform.

        Args:
            commit_hash: Full commit hash

        Returns:
            URL to view the commit on the platform, or None if unable to generate
        """
        repo_path = self._parse_repo_path()
        if not repo_path or not self.platform:
            return None

        url_templates = {
            'github': f'https://github.com/{repo_path}/commit/{commit_hash}',
            'gitlab': f'https://gitlab.com/{repo_path}/-/commit/{commit_hash}',
            'gitee': f'https://gitee.com/{repo_path}/commit/{commit_hash}',
            'bitbucket': f'https://bitbucket.org/{repo_path}/commits/{commit_hash}',
        }

        return url_templates.get(self.platform)

    def _format_relative_date(self, commit_date: datetime) -> str:
        """
        Format commit date as relative time.

        Args:
            commit_date: Commit timestamp

        Returns:
            Relative time string (e.g., "2 days ago")
        """
        now = datetime.now()
        delta = now - commit_date

        if delta.days == 0:
            if delta.seconds < 60:
                return "just now"
            elif delta.seconds < 3600:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.days == 1:
            return "yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.days < 365:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"

    def blame_file(self, file_path: str) -> Dict[int, BlameInfo]:
        """
        Get git blame information for all lines in a file (with caching).

        Args:
            file_path: Relative path from repository root

        Returns:
            Dictionary mapping line numbers (1-based) to BlameInfo
        """
        # Check cache
        if file_path in self.blame_cache:
            return self.blame_cache[file_path]

        if not self.is_git_repo:
            return {}

        absolute_path = self.repo_path / file_path
        if not absolute_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}

        try:
            result = subprocess.run(
                ['git', 'blame', '--line-porcelain', str(absolute_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',  # 明确指定 UTF-8 编码
                errors='replace',  # 遇到无法解码的字符时替换而不是报错
                check=True,
                timeout=30
            )

            blame_map = self._parse_blame_output(result.stdout)
            self.blame_cache[file_path] = blame_map
            return blame_map

        except subprocess.TimeoutExpired:
            logger.warning(f"Git blame timeout for {file_path}")
            return {}
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git blame failed for {file_path}: {e.stderr}")
            return {}
        except Exception as e:
            logger.warning(f"Unexpected error during git blame for {file_path}: {e}")
            return {}

    def _parse_blame_output(self, output: str) -> Dict[int, BlameInfo]:
        """
        Parse git blame --line-porcelain output.

        Format:
            <commit_hash> <original_line> <final_line> <num_lines>
            author <author_name>
            author-mail <email>
            author-time <unix_timestamp>
            summary <commit_subject>
            ...
            \t<code_line>

        Args:
            output: Output from git blame --line-porcelain

        Returns:
            Dictionary mapping line numbers to BlameInfo
        """
        if not output:
            logger.warning("Git blame output is empty")
            return {}

        result = {}
        lines = output.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Skip empty lines and code lines
            if not line or line.startswith('\t'):
                i += 1
                continue

            # First line: <hash> <original_line> <final_line> <num_lines>
            parts = line.split()
            if len(parts) < 3:
                i += 1
                continue

            commit_hash = parts[0]
            line_num = int(parts[2])  # final_line is the line number in current file

            # Parse metadata
            author = None
            author_email = None
            commit_date = None
            subject = None

            i += 1
            while i < len(lines):
                meta_line = lines[i]

                if meta_line.startswith('author '):
                    author = meta_line[7:]
                elif meta_line.startswith('author-mail '):
                    # Remove angle brackets
                    author_email = meta_line[12:].strip('<>')
                elif meta_line.startswith('author-time '):
                    timestamp = int(meta_line[12:])
                    commit_date = datetime.fromtimestamp(timestamp)
                elif meta_line.startswith('summary '):
                    subject = meta_line[8:]
                elif meta_line.startswith('\t'):
                    # Code line, end of this commit's metadata
                    break

                i += 1

            # Save BlameInfo if we have all required fields
            if all([author, author_email, commit_date, subject]):
                result[line_num] = BlameInfo(
                    commit_hash=commit_hash,
                    author=author,
                    author_email=author_email,
                    commit_date=commit_date,
                    subject=subject
                )

        return result

    def get_bug_blame_info(self, bug: Dict) -> Optional[BlameInfo]:
        """
        Get git blame information for a bug.

        If the bug spans multiple lines (start_line != end_line) and these lines
        come from different commits, return the newest commit.

        Args:
            bug: Bug dictionary containing file_path, start_line, end_line

        Returns:
            BlameInfo or None if unable to get blame info
        """
        file_path = bug.get('file_path')
        start_line = bug.get('start_line', 0)
        end_line = bug.get('end_line', 0)

        if not file_path or start_line == 0:
            return None

        # Get blame info for the file
        blame_map = self.blame_file(file_path)
        if not blame_map:
            return None

        # Collect blame info for all lines in the bug range
        bug_blames = []
        for line_num in range(start_line, end_line + 1):
            if line_num in blame_map:
                bug_blames.append(blame_map[line_num])

        if not bug_blames:
            return None

        # If multiple commits, select the newest one
        if len(bug_blames) > 1:
            newest_blame = max(bug_blames, key=lambda b: b.commit_date)
            return newest_blame
        else:
            return bug_blames[0]

    def enrich_bugs_with_git_info(self, bugs: List[Dict]) -> List[Dict]:
        """
        Add git_info field to all bugs.

        Args:
            bugs: List of bug dictionaries

        Returns:
            List of bugs with git_info added
        """
        if not self.is_git_repo:
            logger.warning("Not a git repository, skipping git enrichment")
            return bugs

        # Group bugs by file for efficient blame caching
        bugs_by_file = {}
        for bug in bugs:
            file_path = bug.get('file_path')
            if file_path:
                bugs_by_file.setdefault(file_path, []).append(bug)

        # Process bugs with progress indicator
        enriched_bugs = []

        try:
            from tqdm import tqdm
            show_progress = True
        except ImportError:
            logger.info("tqdm not available, progress bar disabled")
            show_progress = False

        bug_iterator = tqdm(bugs, desc="Adding git info") if show_progress else bugs

        for bug in bug_iterator:
            # Get blame info for this bug
            blame_info = self.get_bug_blame_info(bug)

            # Add git_info field
            if blame_info:
                # Generate commit URL
                commit_url = self._generate_commit_url(blame_info.commit_hash)

                # Format relative date
                date_relative = self._format_relative_date(blame_info.commit_date)

                bug['git_info'] = {
                    'hash': blame_info.commit_hash[:8],  # Short hash
                    'hash_full': blame_info.commit_hash,  # Full hash
                    'author': blame_info.author,
                    'email': blame_info.author_email,
                    'date': blame_info.commit_date.isoformat(),
                    'date_relative': date_relative,
                    'subject': blame_info.subject,
                    'url': commit_url
                }
            else:
                bug['git_info'] = None

            enriched_bugs.append(bug)

        return enriched_bugs
