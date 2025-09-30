# OpsArtisan

**OpsArtisan** is a CLI-first assistant for sysadmins and DevOps engineers. It helps you generate **validated skeletons, configuration files, and infrastructure templates** quickly through interactive wizards or presets.  

> Save time, reduce errors, and standardize your DevOps workflows.

---

## Features

- **Interactive CLI** with optional defaults and saved presets.
- **Template-based generation** for high-value and secondary sysadmin/DevOps tasks.
- **Validation** of generated files or user-provided files against known templates.
- **Supports multiple environments**: Docker, Kubernetes, Ansible, systemd, Terraform, Prometheus, Nginx/Apache, CI/CD pipelines, and more.
- **Extensible**: add your own templates easily to user-level or project-level directories.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/opsartisan.git
cd opsartisan
```
2. Optional: install dependencies (for interactive prompts):
```bash
pip install -r requirements.txt
```
3. Make the CLI executable:
```bash
chmod +x opsartisan.py
sudo ln -s $(pwd)/opsartisan.py /usr/local/bin/opsartisan 
```
4. Verify installation:
```bash
opsartisan --version
```
## Usage
### List available templates
```bash
opsartisan list
```
Shows all templates with descriptions.

---
### Generate a new project or configuration
```bash
opsartisan new <template-id> [options]
```
### Options:
* `--yes` — use default answers without prompting
* `--preset <name>` — use a saved preset
* `--out-dir <dir>` — output directory
* `--validate` — run validators after generation
* `--test` — run functional tests after generation
### Example:
```bash
opsartisan new docker-compose --out-dir ./my-stack --validate
```
### Add a new template
```bash
opsartisan add-template <path-to-template-dir>
```
Adds a custom template to user templates (`~/.opsartisan/templates/`).
### Save and reuse presets
```bash
opsartisan save-preset <name> <template-id>
```
Save answers to prompts for later use.
```bash
opsartisan new docker-compose --preset mystack
```
### Validate a user-provided file
```bash
opsartisan validate-file <template-id> <file-path>
```
#### Example:
```bash
opsartisan validate-file docker-compose ./docker-compose.yml
```
Checks syntax and structure against the selected template.

------
## Templates
### MVP Templates (High-Value)
* Dockerfile
* Docker Compose (multi-service stack)
* Kubernetes (Deployment, Service, optional Ingress)
* Ansible playbook / role
* OpenSSL / CSR / self-signed certificates
* systemd unit
* Nginx / Apache vhost
* Deploy kit (Docker image + Compose + systemd script)
* CI pipelines (GitHub Actions / GitLab CI)
* Terraform snippets (EC2, S3, VPC, Security Groups)
### Secondary Templates (Post-MVP)
* Docker healthcheck + monitoring probe
* Cron job / systemd timer
* Logrotate configuration
* Firewall rules (UFW / iptables / nftables)
* Prometheus scrape job / alert rule
* HAProxy configuration
* Database migration / schema template
* User account & sudo setup script
* Backup script (rsync / borg / rclone)
* Certificate renewal automation (ACME / certbot wrapper)

------
### Configuration Paths
* User templates: `~/.opsartisan/templates/`
* Project templates: `./templates/`
* Presets: `~/.opsartisan/presets.json`

------
### Configuration Paths
