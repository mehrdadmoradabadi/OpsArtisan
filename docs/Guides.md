# OpsArtisan Usage & Authoring Guides

This document collects best practices and workflows for both end users and template authors.

---

## For Users

- Use `opsartisan list` to discover available templates and filter by category or tag.
- Generate configurations interactively with `opsartisan new <template-id>`.
- Save your answers for reuse: `opsartisan save-preset <name> <template-id>`.
- Use shell completion for speed (`opsartisan completion install bash`).
- Validate your configs with `opsartisan validate-file` or enable `--validate` after generation.
- Prefer using the template marketplace for up-to-date, community-tested templates.
- For different environments, explore `opsartisan env create` and `opsartisan env compare`.

---

## For Template Authors

- Start with the [Template Authoring Guide](Template-Authoring.md).
- Use clear, descriptive prompts and document your outputs.
- Use environment defaults to help users generate safe configs for dev, staging, and prod.
- Add validators for all scripts and configs (syntax check, lint, etc).
- Use post-generation hooks for permissions, git setup, etc.
- Document next steps for users in the `next_steps` and generated README.
- Use conditions in prompts and outputs to reduce user confusion.
- Test your template for all supported environments and edge cases.
- Submit to the marketplace for visibility and user feedback.

---

## Common Workflows

### 1. Bootstrap a Dev Environment

```bash
opsartisan new docker-compose --out-dir ./dev-env --validate
```

### 2. Create a Secure User Account (as root)

```bash
opsartisan new user-setup --configuration-mode advanced --sudo-access --ssh-key-setup
```

### 3. Publish Your Own Template

- Create a directory with `descriptor.json` and a `templates/` subfolder.
- Test locally, then publish to GitHub.
- Share with:  
  ```bash
  opsartisan template install https://github.com/yourname/template-my-template.git
  ```

---

## Best Practices

- Always test generated scripts/configs on a safe environment first.
- Use presets for repetitive tasks.
- Keep your templates and presets up to date.
- Use `opsartisan stats` to see which templates are most used.
- Review generated scripts for security before running as root.

---

For more, see `opsartisan --help` or individual command help.
