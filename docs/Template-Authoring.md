# OpsArtisan Template Authoring Guide

This guide will help you create, publish, and maintain advanced templates for OpsArtisan.

---

## Template Structure

A template is a directory containing:

- `descriptor.json` — main metadata, prompts, output files, hooks, etc.
- `templates/` — Jinja2 template files used to generate outputs
- (optional) `examples/` — sample answers or generated outputs

### Example Directory Layout

```
my-template/
├── descriptor.json
└── templates/
    ├── main.j2
    └── helper.j2
```

---

## `descriptor.json` Reference

This file describes everything about your template.

### Required Fields

| Field         | Type      | Description                                   |
|---------------|-----------|-----------------------------------------------|
| id            | string    | Unique identifier for your template           |
| title         | string    | Human-friendly title                          |
| description   | string    | Short description                             |
| outputs       | array     | List of outputs to generate                   |

### Optional Fields

| Field              | Type      | Description                                 |
|--------------------|-----------|---------------------------------------------|
| category           | string    | For grouping/searching                      |
| tags               | array     | Keywords for searching                      |
| prompts            | array     | Variables/questions to ask the user         |
| dependencies       | array     | List of template IDs required before this   |
| required_tools     | array     | CLI tools required (for validation)         |
| environment_defaults | object  | Default answers for specific environments   |
| validators         | array     | Validation commands to check output         |
| tests              | array     | Test commands to run after generation       |
| hooks              | object    | Pre/post-generation actions                 |
| next_steps         | array     | Instructions for the user after generation  |
| example_usage      | string    | Example CLI usage                           |
| documentation      | object    | Extra docs, links, best practices           |

---

## Prompts Example

```json
"prompts": [
  {
    "id": "username",
    "type": "string",
    "label": "System username",
    "default": "deploy",
    "validation": "^[a-z][a-z0-9_-]*$"
  },
  {
    "id": "shell",
    "type": "choice",
    "label": "Login shell",
    "choices": ["/bin/bash", "/bin/zsh"],
    "default": "/bin/bash"
  }
]
```
Supported prompt types: `string`, `choice`, `bool`, `integer`, `confirm`.

You can use `condition` to show prompts only if a previous answer matches.

---

## Outputs Example

```json
"outputs": [
  {
    "path": "scripts/create-user.sh",
    "template": "create-user.j2"
  },
  {
    "path": "README.md",
    "template": "readme.j2"
  }
]
```
You can use template variables in the output path, e.g. `"path": "{{ username }}.sh"`

---

## Validators & Tests

Validators run commands after generation to check output files:

```json
"validators": [
  {
    "command": "bash -n scripts/create-user.sh",
    "description": "Validate script syntax"
  }
]
```
Tests are similar but intended to check behavior, not just syntax.

---

## Hooks (Pre/Post Generation)

Hooks automate actions after files are generated:

```json
"hooks": {
  "post_generation": [
    {
      "type": "shell",
      "command": "chmod +x scripts/*.sh",
      "description": "Make scripts executable",
      "on_failure": "warn"
    }
  ]
}
```
Supported hook types: `shell`, `chmod`, `git`, `info`.

---

## Advanced Features

- **Dependencies:**  
  Use `dependencies` to require other templates before this one.
- **Environment Defaults:**  
  Provide different default answers for `dev`, `staging`, `prod`, etc.
- **Plugin Integration:**  
  Use custom validators/renderers by naming plugins in `validators`.

---

## Example: Minimal Template

```json
{
  "id": "hello-world",
  "title": "Hello World Script",
  "description": "Generate a simple hello world bash script.",
  "outputs": [
    {
      "path": "hello.sh",
      "template": "hello.j2"
    }
  ],
  "prompts": [
    {
      "id": "name",
      "type": "string",
      "label": "Name to greet",
      "default": "World"
    }
  ]
}
```
`templates/hello.j2`:
```bash
#!/bin/bash
echo "Hello, {{ name }}!"
```

---

## Publishing Your Template

1. Place your template directory in `~/.opsartisan/templates/` or your project’s `./templates/`
2. Test with:
   ```bash
   opsartisan new <your-template-id>
   ```
3. To share publicly, publish your template directory (with descriptor and templates) on GitHub and add to the marketplace!

---

## Troubleshooting

- Make sure all required fields are present in `descriptor.json`
- Validate your template with:
  ```bash
  opsartisan validate <your-template-id>
  ```
- Ensure your template directory has a `templates/` folder
- Use the `info` command to preview metadata and outputs

---

For more examples, see the `user-setup` template or community templates in the [marketplace](https://github.com/yourusername/opsartisan).
