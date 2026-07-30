
---

## docs/api/jinax.md

```markdown
# Jinax API

## Jinax

Jinax template engine.

### Constructor

```python
Jinax(template_directory: str | Path = "templates", *, auto_reload: bool = False, strict_undefined: bool = True, globals: dict[str, Any] | None = None, filters: dict[str, Callable[..., Any]] | None = None)

Methods
add_global
python
def add_global(name: str, value: Any) -> None
Add a global variable.

add_filter
python
def add_filter(name: str, func: Callable[..., Any]) -> None
Add a custom filter.

render
python
async def render(template_name: str, context: dict[str, Any] | None = None) -> str
Render a template.

render_response
python
async def render_response(template_name: str, context: dict[str, Any] | None = None, *, status_code: int = 200, headers: dict[str, str] | None = None) -> HTMLResponse
Render a template and return an HTML response.

Environment
Jinax environment.

Constructor
python
Environment(loader: Any, autoescape: bool = True, enable_async: bool = True, auto_reload: bool = False, strict_undefined: bool = False)
Methods
add_global
python
def add_global(name: str, value: Any) -> None
Add a global variable.

add_filter
python
def add_filter(name: str, func: Callable[..., Any]) -> None
Add a custom filter.

get_template
python
def get_template(name: str) -> Any
Get a template.

from_string
python
def from_string(source: str) -> Any
Create a template from a string.

Loader
Template loader.

Constructor
python
Loader(search_path: str | Path, encoding: str = "utf-8")
Methods
get_source
python
def get_source(environment: Any, template: str) -> tuple[str, str | None, Callable[[], bool] | None]
Get template source.

list_templates
python
def list_templates() -> list[str]
List all templates.

TemplateNotFound
Exception raised when a template is not found.

python
TemplateNotFound(template: str)
Attributes
Attribute	Type	Description
template	str	The template name
Filters
currency
python
currency(value: Any, code: str = "USD") -> str
Format a value as currency.

Built-in Filters
Filter	Description
capitalize	Capitalize a string
lower	Convert to lowercase
upper	Convert to uppercase
title	Convert to title case
trim	Trim whitespace
escape	Escape HTML
safe	Mark as safe
json	Convert to JSON
length	Get length
reverse	Reverse a string or list
join	Join a list
replace	Replace text
date	Format a date
datetime	Format a datetime
currency	Format as currency
truncate	Truncate text
default	Default value
first	First item
last	Last item
Functions
Built-in Functions
Function	Description
now()	Current datetime
date()	Current date
datetime()	Current datetime
range(n)	Range of numbers
length(value)	Get length
type(value)	Get type
str(value)	Convert to string
int(value)	Convert to integer
float(value)	Convert to float
bool(value)	Convert to boolean
list(value)	Convert to list
dict(value)	Convert to dictionary
json(value)	Convert to JSON
random()	Random float
random_int(min, max)	Random integer
random_choice(items)	Random choice
uuid()	Generate UUID
hash(value)	Hash a value
env(key, default)	Get environment variable