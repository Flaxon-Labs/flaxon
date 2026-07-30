
---

## docs/installation.md

```markdown
# Installation

## Requirements

- Python 3.11 or higher
- pip (Python package installer)

## Installing Flaxon

### Basic Installation

```bash
pip install flaxon

This installs the core framework with no optional dependencies.

Installation with Features
bash
# Standard installation with recommended features
pip install flaxon[standard]

# With ASGI server
pip install flaxon[server]

# With template support (Jinax)
pip install flaxon[templates]

# With development tools
pip install flaxon[dev]

# With all features
pip install flaxon[standard,dev,server]
Optional Dependency Groups
Group	Description
server	Uvicorn ASGI server
templates	Jinja2 for Jinax templates
standard	Server + Templates
dev	Pytest, Ruff, MyPy, and development tools
docs	MkDocs for documentation
Verifying Installation
bash
python -c "import flaxon; print(flaxon.__version__)"
Development Installation
For contributing to Flaxon:

bash
git clone https://github.com/aldanedev-create/Flaxon-Backend-Framework.git
cd Flaxon-Backend-Framework
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[standard,dev]"
pytest
Next Steps
Quick Start — Build your first application

Philosophy — Understand the design principles