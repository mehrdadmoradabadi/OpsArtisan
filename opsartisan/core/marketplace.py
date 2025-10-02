"""Template marketplace for discovering and installing remote templates."""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import click

from opsartisan.config import USER_TEMPLATES_DIR
from opsartisan.utils.file_utils import copy_directory


class TemplateMarketplace:
    """Manages template discovery and installation from remote sources."""

    def __init__(self):
        self.marketplace_url = "https://api.opsartisan.io/templates"
        # For now, use a static catalog
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        """
        Load template catalog from marketplace.
        In production, this would fetch from an API.
        """
        # Mock catalog for demonstration
        return [
            {
                'id': 'advanced-k8s',
                'title': 'Advanced Kubernetes Deployment',
                'description': 'Full-featured K8s deployment with ingress, secrets, HPA',
                'author': 'OpsArtisan Community',
                'version': '1.0.0',
                'downloads': 1523,
                'tags': ['kubernetes', 'production', 'scalability'],
                'git_url': 'https://github.com/opsartisan/template-advanced-k8s.git'
            },
            {
                'id': 'secure-nginx',
                'title': 'Secure Nginx Configuration',
                'description': 'Hardened Nginx config with best practices',
                'author': 'Security Team',
                'version': '2.1.0',
                'downloads': 892,
                'tags': ['nginx', 'security', 'web-server'],
                'git_url': 'https://github.com/opsartisan/template-secure-nginx.git'
            },
            {
                'id': 'multi-env-terraform',
                'title': 'Multi-Environment Terraform',
                'description': 'Terraform setup for dev/staging/prod environments',
                'author': 'Infrastructure Team',
                'version': '1.5.0',
                'downloads': 2341,
                'tags': ['terraform', 'infrastructure', 'multi-env'],
                'git_url': 'https://github.com/opsartisan/template-multi-env-tf.git'
            }
        ]

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search marketplace templates by keyword.
        """
        keyword_lower = keyword.lower()
        results = []

        for template in self.catalog:
            searchable = [
                template.get('id', ''),
                template.get('title', ''),
                template.get('description', ''),
                ' '.join(template.get('tags', []))
            ]

            if any(keyword_lower in field.lower() for field in searchable):
                # Check if already installed
                local_path = USER_TEMPLATES_DIR / template['id']
                template['installed'] = local_path.exists()
                results.append(template)

        return results

    def install_from_marketplace(self, template_id: str) -> str:
        """
        Install a template from the marketplace catalog.
        """
        # Find template in catalog
        template_info = None
        for template in self.catalog:
            if template['id'] == template_id:
                template_info = template
                break

        if not template_info:
            raise ValueError(f"Template '{template_id}' not found in marketplace")

        git_url = template_info.get('git_url')
        if not git_url:
            raise ValueError(f"No git URL found for template '{template_id}'")

        return self.install_from_git(git_url, custom_name=template_id)

    def install_from_git(
            self,
            git_url: str,
            custom_name: Optional[str] = None
    ) -> str:
        """
        Clone a template from a git repository.

        Args:
            git_url: Git repository URL
            custom_name: Optional custom template ID

        Returns:
            The installed template ID
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Clone repository
            click.echo(f"Cloning from {git_url}...")
            try:
                subprocess.run(
                    ['git', 'clone', '--depth', '1', git_url, str(temp_path / 'repo')],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to clone repository: {e.stderr}")

            repo_path = temp_path / 'repo'

            # Load descriptor to get template ID
            descriptor_path = repo_path / 'descriptor.json'
            if not descriptor_path.exists():
                raise ValueError("No descriptor.json found in repository root")

            with open(descriptor_path) as f:
                descriptor = json.load(f)

            template_id = custom_name or descriptor.get('id')
            if not template_id:
                raise ValueError("Template descriptor missing 'id' field")

            # Copy to user templates directory
            dest_path = USER_TEMPLATES_DIR / template_id

            if dest_path.exists():
                if not click.confirm(
                        f"Template '{template_id}' already exists. Overwrite?"
                ):
                    raise RuntimeError("Installation cancelled")
                shutil.rmtree(dest_path)

            USER_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            copy_directory(repo_path, dest_path)

            # Remove .git directory
            git_dir = dest_path / '.git'
            if git_dir.exists():
                shutil.rmtree(git_dir)

            return template_id

    def list_installed(self) -> List[str]:
        """
        List all installed templates from marketplace.
        """
        if not USER_TEMPLATES_DIR.exists():
            return []

        installed = []
        for item in USER_TEMPLATES_DIR.iterdir():
            if item.is_dir() and (item / 'descriptor.json').exists():
                installed.append(item.name)

        return installed

    def update(self, template_id: str) -> bool:
        """
        Update an installed template to the latest version.
        """
        # Find in catalog
        template_info = None
        for template in self.catalog:
            if template['id'] == template_id:
                template_info = template
                break

        if not template_info:
            click.echo(f"Template '{template_id}' not found in marketplace", err=True)
            return False

        local_path = USER_TEMPLATES_DIR / template_id
        if not local_path.exists():
            click.echo(f"Template '{template_id}' is not installed", err=True)
            return False

        # Backup current version
        backup_path = local_path.parent / f"{template_id}.backup"
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.move(str(local_path), str(backup_path))

        try:
            self.install_from_git(template_info['git_url'], custom_name=template_id)
            click.echo(click.style(f"✓ Updated {template_id}", fg='green'))

            # Remove backup on success
            shutil.rmtree(backup_path)
            return True

        except Exception as e:
            # Restore backup on failure
            click.echo(f"Update failed: {e}", err=True)
            if local_path.exists():
                shutil.rmtree(local_path)
            shutil.move(str(backup_path), str(local_path))
            click.echo("Restored previous version", err=True)
            return False

    def get_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a marketplace template.
        """
        for template in self.catalog:
            if template['id'] == template_id:
                return template
        return None