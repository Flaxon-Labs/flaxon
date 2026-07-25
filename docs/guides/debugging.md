# Debugging

## Overview

Flaxon provides a comprehensive debugging system that helps you identify and fix issues quickly. The debugger explains failures in plain language with request context, redacted sensitive data, and clear error codes.

## Debug Mode

### Enabling Debug Mode

```python
from flaxon import Flaxon

# Enable debug mode
app = Flaxon("my-app", debug=True)

# Or via configuration
app = Flaxon("my-app", config={"DEBUG": True})

# Debugging

## Overview

Flaxon provides a comprehensive debugging system that helps you identify and fix issues quickly. The debugger explains failures in plain language with request context, redacted sensitive data, and clear error codes.

## Debug Mode

### Enabling Debug Mode

```python
from flaxon import Flaxon

# Enable debug mode
app = Flaxon("my-app", debug=True)

# Or via configuration
app = Flaxon("my-app", config={"DEBUG": True})