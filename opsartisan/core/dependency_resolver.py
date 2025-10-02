"""Dependency resolution for templates."""

from typing import Dict, Any, List, Set
import click


class DependencyResolver:
    """Resolves and checks template dependencies."""

    def __init__(self, template_manager):
        self.template_manager = template_manager
        self._resolution_cache = {}

    def check_dependencies(self, template: Dict[str, Any]) -> List[str]:
        """
        Check if all dependencies are available.
        Returns list of missing dependency IDs.
        """
        dependencies = template.get('dependencies', [])
        if not dependencies:
            return []

        missing = []
        for dep_id in dependencies:
            dep_template = self.template_manager.get_template(dep_id)
            if not dep_template:
                missing.append(dep_id)

        return missing

    def resolve_dependency_order(self, template: Dict[str, Any]) -> List[str]:
        """
        Resolve the order in which dependencies should be generated.
        Returns list of template IDs in dependency order.
        Uses topological sort to handle complex dependency graphs.
        """
        template_id = template.get('id')

        if template_id in self._resolution_cache:
            return self._resolution_cache[template_id]

        visited = set()
        order = []

        def visit(tid: str, path: Set[str]):
            if tid in path:
                cycle = ' -> '.join(path) + f' -> {tid}'
                raise ValueError(
                    f"Circular dependency detected: {cycle}"
                )

            if tid in visited:
                return

            tmpl = self.template_manager.get_template(tid)
            if not tmpl:
                raise ValueError(f"Dependency template not found: {tid}")

            visited.add(tid)
            path.add(tid)

            # Visit dependencies first
            for dep_id in tmpl.get('dependencies', []):
                visit(dep_id, path.copy())

            order.append(tid)

        try:
            visit(template_id, set())
        except ValueError as e:
            click.echo(click.style(f"Dependency error: {e}", fg='red'), err=True)
            raise

        self._resolution_cache[template_id] = order
        return order

    def get_dependency_tree(self, template: Dict[str, Any], level: int = 0) -> str:
        """
        Generate a visual dependency tree.
        """
        template_id = template.get('id')
        title = template.get('title', template_id)

        indent = "  " * level
        prefix = "└─ " if level > 0 else ""

        tree = f"{indent}{prefix}{title} ({template_id})\n"

        dependencies = template.get('dependencies', [])
        for dep_id in dependencies:
            dep_template = self.template_manager.get_template(dep_id)
            if dep_template:
                tree += self.get_dependency_tree(dep_template, level + 1)
            else:
                tree += f"{indent}  └─ ⚠️  {dep_id} (not found)\n"

        return tree

    def validate_all_dependencies(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all dependencies can be resolved.
        Returns dict with 'valid' bool and 'errors' list.
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        try:
            order = self.resolve_dependency_order(template)

            # Check for missing dependencies
            missing = self.check_dependencies(template)
            if missing:
                result['valid'] = False
                result['errors'].append(
                    f"Missing dependencies: {', '.join(missing)}"
                )

            # Check required tools for all dependencies
            for template_id in order:
                tmpl = self.template_manager.get_template(template_id)
                if tmpl and tmpl.get('required_tools'):
                    result['warnings'].append(
                        f"{template_id} requires: {', '.join(tmpl['required_tools'])}"
                    )

        except ValueError as e:
            result['valid'] = False
            result['errors'].append(str(e))

        return result