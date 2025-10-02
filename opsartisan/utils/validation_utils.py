"""Enhanced validation utilities with better error messages and suggestions."""

import re
from typing import Dict, Any, List, Optional, Tuple


class ValidationError:
    """Represents a validation error with context and suggestions."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        doc_link: Optional[str] = None
    ):
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.suggestion = suggestion
        self.doc_link = doc_link

    def format(self) -> str:
        """Format the error message with context."""
        parts = []

        if self.file_path:
            location = self.file_path
            if self.line_number:
                location += f":{self.line_number}"
            parts.append(f"📄 {location}")

        parts.append(f"❌ {self.message}")

        if self.suggestion:
            parts.append(f"💡 Suggestion: {self.suggestion}")

        if self.doc_link:
            parts.append(f"📚 Documentation: {self.doc_link}")

        return "\n".join(parts)


class ValidationParser:
    """Parses validation output and provides enhanced error messages."""

    # Common error patterns and their documentation
    ERROR_PATTERNS = {
        'docker': [
            {
                'pattern': r'unknown instruction: (\w+)',
                'suggestion': 'Check Dockerfile instruction spelling. Common instructions: FROM, RUN, COPY, CMD, ENTRYPOINT, EXPOSE',
                'doc_link': 'https://docs.docker.com/engine/reference/builder/'
            },
            {
                'pattern': r'COPY failed: .* no such file or directory',
                'suggestion': 'Ensure the source file exists relative to the build context',
                'doc_link': 'https://docs.docker.com/engine/reference/builder/#copy'
            },
            {
                'pattern': r'failed to solve with frontend dockerfile.v0',
                'suggestion': 'Check Dockerfile syntax. Ensure proper instruction order (FROM must be first)',
                'doc_link': 'https://docs.docker.com/engine/reference/builder/'
            }
        ],
        'docker-compose': [
            {
                'pattern': r'version .* does not match any of the regexes',
                'suggestion': 'Use a valid docker-compose version (3.0-3.9, or omit version for latest)',
                'doc_link': 'https://docs.docker.com/compose/compose-file/compose-versioning/'
            },
            {
                'pattern': r'services.(\w+).(\w+) must be a',
                'suggestion': 'Check the data type for this service property',
                'doc_link': 'https://docs.docker.com/compose/compose-file/'
            },
            {
                'pattern': r'no configuration file provided',
                'suggestion': 'Ensure docker-compose.yml or docker-compose.yaml exists',
                'doc_link': 'https://docs.docker.com/compose/compose-file/'
            }
        ],
        'kubernetes': [
            {
                'pattern': r'error validating "(.*)": error validating data',
                'suggestion': 'Check resource specification against Kubernetes API schema',
                'doc_link': 'https://kubernetes.io/docs/reference/kubernetes-api/'
            },
            {
                'pattern': r'missing required field "(\w+)"',
                'suggestion': lambda m: f'Add required field: {m.group(1)}',
                'doc_link': 'https://kubernetes.io/docs/reference/kubernetes-api/'
            },
            {
                'pattern': r'Invalid value: "(.*)": (.+)',
                'suggestion': 'Check the value format and valid options for this field',
                'doc_link': 'https://kubernetes.io/docs/reference/kubernetes-api/'
            }
        ],
        'ansible': [
            {
                'pattern': r'ERROR! (.+) is not a valid attribute for a (Task|Play)',
                'suggestion': 'Check playbook syntax. Common attributes: name, hosts, tasks, vars, roles',
                'doc_link': 'https://docs.ansible.com/ansible/latest/reference_appendices/playbooks_keywords.html'
            },
            {
                'pattern': r"ERROR! Syntax Error while loading YAML",
                'suggestion': 'Fix YAML syntax. Check indentation (use spaces, not tabs) and special characters',
                'doc_link': 'https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html'
            }
        ],
        'terraform': [
            {
                'pattern': r'Error: Unsupported argument',
                'suggestion': 'Check the resource documentation for valid arguments',
                'doc_link': 'https://registry.terraform.io/browse/providers'
            },
            {
                'pattern': r'Error: Reference to undeclared (resource|variable)',
                'suggestion': 'Ensure the resource or variable is declared before referencing it',
                'doc_link': 'https://www.terraform.io/docs/language/expressions/references.html'
            }
        ],
        'systemd': [
            {
                'pattern': r'\[(.+\.service)\] Failed to parse (.+)',
                'suggestion': 'Check systemd unit file syntax and property names',
                'doc_link': 'https://www.freedesktop.org/software/systemd/man/systemd.service.html'
            },
            {
                'pattern': r'Unknown section \'(\w+)\'',
                'suggestion': 'Valid sections: [Unit], [Service], [Install]. Check section name spelling',
                'doc_link': 'https://www.freedesktop.org/software/systemd/man/systemd.service.html'
            }
        ],
        'yaml': [
            {
                'pattern': r'mapping values are not allowed here',
                'suggestion': 'Check YAML indentation. Ensure proper spacing (2 or 4 spaces)',
                'doc_link': 'https://yaml.org/spec/1.2/spec.html'
            },
            {
                'pattern': r'found undefined alias',
                'suggestion': 'Ensure anchors are defined before aliases reference them',
                'doc_link': 'https://yaml.org/spec/1.2/spec.html#id2785586'
            }
        ]
    }

    @staticmethod
    def parse_error(
        error_output: str,
        template_type: str,
        file_path: Optional[str] = None
    ) -> List[ValidationError]:
        """
        Parse validation error output and create enhanced error objects.
        """
        errors = []
        patterns = ValidationParser.ERROR_PATTERNS.get(template_type, [])

        for line in error_output.split('\n'):
            if not line.strip():
                continue

            # Try to match known patterns
            matched = False
            for pattern_info in patterns:
                match = re.search(pattern_info['pattern'], line)
                if match:
                    suggestion = pattern_info['suggestion']
                    if callable(suggestion):
                        suggestion = suggestion(match)

                    # Try to extract line number
                    line_match = re.search(r':(\d+):', line)
                    line_number = int(line_match.group(1)) if line_match else None

                    errors.append(ValidationError(
                        message=line.strip(),
                        file_path=file_path,
                        line_number=line_number,
                        suggestion=suggestion,
                        doc_link=pattern_info.get('doc_link')
                    ))
                    matched = True
                    break

            # If no pattern matched, create basic error
            if not matched and ('error' in line.lower() or 'failed' in line.lower()):
                errors.append(ValidationError(
                    message=line.strip(),
                    file_path=file_path
                ))

        return errors

    @staticmethod
    def get_quick_fixes(template_type: str) -> List[str]:
        """
        Get common quick fixes for a template type.
        """
        quick_fixes = {
            'docker': [
                'Ensure Dockerfile starts with FROM instruction',
                'Check that all COPY/ADD source files exist',
                'Use absolute paths for WORKDIR',
                'Combine RUN commands to reduce layers'
            ],
            'docker-compose': [
                'Validate YAML syntax (proper indentation)',
                'Use version 3+ format',
                'Ensure service names are unique',
                'Check that volume and network references exist'
            ],
            'kubernetes': [
                'Ensure apiVersion and kind are specified',
                'Validate resource names (lowercase, alphanumeric, hyphens)',
                'Check that namespace exists or will be created',
                'Ensure selectors match pod labels'
            ],
            'ansible': [
                'Use 2-space indentation consistently',
                'Quote strings with special characters',
                'Ensure tasks have name attributes',
                'Check module names are correct'
            ],
            'terraform': [
                'Run terraform fmt to fix formatting',
                'Ensure required providers are declared',
                'Check variable and resource naming',
                'Validate interpolation syntax'
            ],
            'systemd': [
                'Use correct section names: [Unit], [Service], [Install]',
                'Check property names (case-sensitive)',
                'Ensure ExecStart path is absolute',
                'Set Type appropriately (simple, forking, etc.)'
            ]
        }
        return quick_fixes.get(template_type, [])


class MultiFileValidator:
    """Validates multiple related files with context awareness."""

    def __init__(self):
        self.file_contexts: Dict[str, Any] = {}

    def add_file_context(self, file_path: str, content: Any):
        """Add a file to the validation context."""
        self.file_contexts[file_path] = content

    def validate_docker_compose_with_env(
        self,
        compose_content: str,
        env_content: Optional[str] = None
    ) -> List[ValidationError]:
        """
        Validate docker-compose with .env file context.
        """
        errors = []

        # Extract environment variable references
        env_refs = re.findall(r'\$\{?([A-Z_][A-Z0-9_]*)\}?', compose_content)

        if env_content:
            # Parse .env file
            defined_vars = set()
            for line in env_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    defined_vars.add(var_name)

            # Check for undefined variables
            for var in set(env_refs):
                if var not in defined_vars:
                    errors.append(ValidationError(
                        message=f"Environment variable ${var} is not defined in .env",
                        file_path='docker-compose.yml',
                        suggestion=f'Add {var}=<value> to your .env file',
                        doc_link='https://docs.docker.com/compose/environment-variables/'
                    ))

        elif env_refs:
            # .env file missing but variables referenced
            errors.append(ValidationError(
                message=f"Environment variables referenced but no .env file found: {', '.join(set(env_refs))}",
                suggestion='Create a .env file with required variables',
                doc_link='https://docs.docker.com/compose/environment-variables/'
            ))

        return errors

    def validate_kubernetes_resources(
        self,
        resources: List[Dict[str, Any]]
    ) -> List[ValidationError]:
        """
        Validate multiple Kubernetes resources for consistency.
        Checks cross-resource references like Services -> Deployments.
        """
        errors = []
        deployments = {}
        services = {}
        config_maps = {}
        secrets = {}

        # Catalog resources
        for resource in resources:
            kind = resource.get('kind')
            metadata = resource.get('metadata', {})
            name = metadata.get('name')

            if kind == 'Deployment':
                deployments[name] = resource
            elif kind == 'Service':
                services[name] = resource
            elif kind == 'ConfigMap':
                config_maps[name] = resource
            elif kind == 'Secret':
                secrets[name] = resource

        # Validate Service -> Deployment references
        for svc_name, service in services.items():
            spec = service.get('spec', {})
            selector = spec.get('selector', {})

            # Check if any deployment matches the selector
            matched = False
            for dep_name, deployment in deployments.items():
                dep_labels = deployment.get('spec', {}).get('template', {}).get('metadata', {}).get('labels', {})
                if all(dep_labels.get(k) == v for k, v in selector.items()):
                    matched = True
                    break

            if not matched and selector:
                errors.append(ValidationError(
                    message=f"Service '{svc_name}' selector doesn't match any Deployment labels",
                    file_path=f'{svc_name}-service.yaml',
                    suggestion=f"Ensure a Deployment has labels matching: {selector}",
                    doc_link='https://kubernetes.io/docs/concepts/services-networking/service/'
                ))

        # Validate ConfigMap/Secret references in Deployments
        for dep_name, deployment in deployments.items():
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])

            for container in containers:
                # Check envFrom references
                env_from = container.get('envFrom', [])
                for env_source in env_from:
                    if 'configMapRef' in env_source:
                        cm_name = env_source['configMapRef'].get('name')
                        if cm_name and cm_name not in config_maps:
                            errors.append(ValidationError(
                                message=f"Deployment '{dep_name}' references missing ConfigMap '{cm_name}'",
                                file_path=f'{dep_name}-deployment.yaml',
                                suggestion=f"Create ConfigMap '{cm_name}' or check the reference",
                                doc_link='https://kubernetes.io/docs/concepts/configuration/configmap/'
                            ))

                    if 'secretRef' in env_source:
                        secret_name = env_source['secretRef'].get('name')
                        if secret_name and secret_name not in secrets:
                            errors.append(ValidationError(
                                message=f"Deployment '{dep_name}' references missing Secret '{secret_name}'",
                                file_path=f'{dep_name}-deployment.yaml',
                                suggestion=f"Create Secret '{secret_name}' or check the reference",
                                doc_link='https://kubernetes.io/docs/concepts/configuration/secret/'
                            ))

        return errors