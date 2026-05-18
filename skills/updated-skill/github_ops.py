#!/usr/bin/env python3
"""
GitHub Operations for Calorie Tracker
Handles file sync with GitHub repository
"""

import subprocess
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional

class GitHubSync:
    def __init__(self, config_path: str = "/mnt/user-data/uploads/ct_config.json"):
        """Initialize with GitHub config"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.token = self.config['github_token']
        self.repo = self.config['github_repo']
        self.branch = self.config.get('github_branch', 'main')
        
        # Build authenticated repo URL
        username = self.repo.split('/')[0]
        repo_name = self.repo.split('/')[1]
        self.repo_url = f"https://{self.token}@github.com/{username}/{repo_name}.git"
        
        self.temp_dir = None
    
    def clone_repo(self) -> str:
        """Clone repository to temporary directory"""
        self.temp_dir = tempfile.mkdtemp(prefix="calorie_tracker_")
        
        try:
            # Clone with depth 1 for speed
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--branch', self.branch, self.repo_url, self.temp_dir],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                # Branch might not exist, try without branch spec
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', self.repo_url, self.temp_dir],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    raise Exception(f"Git clone failed: {result.stderr}")
            
            return self.temp_dir
        
        except Exception as e:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise e
    
    def pull_file(self, filename: str, destination: str) -> bool:
        """Pull a single file from GitHub to destination"""
        try:
            repo_dir = self.clone_repo()
            source_path = os.path.join(repo_dir, filename)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, destination)
                print(f"Pulled {filename} from GitHub")
                return True
            else:
                print(f"{filename} not found in GitHub repo (first time?)")
                return False
        
        except Exception as e:
            print(f"Failed to pull {filename}: {e}")
            return False
        
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
    
    def push_files(self, files: Dict[str, str], commit_message: str) -> bool:
        """
        Push multiple files to GitHub
        
        Args:
            files: Dict mapping {destination_path_in_repo: source_path_on_disk}
            commit_message: Git commit message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            repo_dir = self.clone_repo()
            
            # Copy files to repo directory
            for dest_path, source_path in files.items():
                dest_full = os.path.join(repo_dir, dest_path)
                
                # Create parent directories if needed
                os.makedirs(os.path.dirname(dest_full), exist_ok=True)
                
                shutil.copy2(source_path, dest_full)
                print(f"Staged {dest_path}")
            
            # Git operations
            os.chdir(repo_dir)
            
            # Configure git (required for commit)
            subprocess.run(['git', 'config', 'user.name', 'Calorie Tracker'], check=True)
            subprocess.run(['git', 'config', 'user.email', 'ct@calorietracker.app'], check=True)
            
            # Stage files
            for dest_path in files.keys():
                subprocess.run(['git', 'add', dest_path], check=True)
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and 'nothing to commit' not in result.stdout:
                print(f"Commit warning: {result.stdout}")
            
            # Push
            result = subprocess.run(
                ['git', 'push', 'origin', self.branch],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Git push failed: {result.stderr}")
            
            print(f"Pushed to GitHub: {commit_message}")
            return True
        
        except Exception as e:
            print(f"Failed to push to GitHub: {e}")
            return False
        
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
    
    def sync_database(self, db_path: str, json_path: str, device_id: str) -> bool:
        """
        Full sync workflow: pull latest, merge, push updated
        
        Args:
            db_path: Path to local SQLite database
            json_path: Path to exported JSON file
            device_id: Device identifier for commit message
        
        Returns:
            True if successful, False otherwise
        """
        from datetime import datetime
        
        # Pull latest database from GitHub
        temp_db = db_path + ".remote"
        pulled = self.pull_file('calorie_tracker.db', temp_db)
        
        if pulled and os.path.exists(temp_db):
            # Remote database exists, need to merge
            # For now, we'll use a simple strategy: keep local (latest writes win)
            # In production, you'd implement proper merge logic here
            print("Remote database found, keeping local version (latest)")
            os.remove(temp_db)
        
        # Push both files
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        commit_msg = f"Update from {device_id} at {timestamp}"
        
        files_to_push = {
            'calorie_tracker.db': db_path,
            'dashboard_data.json': json_path
        }
        
        return self.push_files(files_to_push, commit_msg)


def sync_to_github(db_path: str, json_path: str, config_path: str, device_id: str) -> bool:
    """Standalone sync function"""
    try:
        syncer = GitHubSync(config_path)
        return syncer.sync_database(db_path, json_path, device_id)
    except Exception as e:
        print(f"GitHub sync error: {e}")
        return False


if __name__ == "__main__":
    # Test GitHub operations
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_ops.py <test_pull|test_push>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    config_path = "/mnt/user-data/uploads/ct_config.json"
    
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    
    syncer = GitHubSync(config_path)
    
    if command == "test_pull":
        success = syncer.pull_file('calorie_tracker.db', '/tmp/test_pull.db')
        print(f"Pull {'succeeded' if success else 'failed'}")
    
    elif command == "test_push":
        # Create dummy files
        with open('/tmp/test.txt', 'w') as f:
            f.write("Test file from calorie tracker\n")
        
        success = syncer.push_files(
            {'test/test.txt': '/tmp/test.txt'},
            'Test commit from calorie tracker'
        )
        print(f"Push {'succeeded' if success else 'failed'}")
