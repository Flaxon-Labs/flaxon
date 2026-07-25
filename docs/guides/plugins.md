# Plugins

## Overview

Flaxon provides a plugin system that allows you to extend the framework with modular components. Plugins can add routes, middleware, CLI commands, health checks, and lifecycle hooks.

## Creating a Plugin

### Basic Plugin

```python
from flaxon.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "A custom Flaxon plugin"

    def setup(self, app):
        """Setup the plugin with the application."""
        @app.get("/plugin")
        async def plugin_route():
            return {"plugin": "MyPlugin"}

        # Add middleware
        app.add_middleware(MyPluginMiddleware)

        # Store state
        app.state.plugin_loaded = True

        Simple Plugin
python
from flaxon.plugins import SimplePlugin

def setup_plugin(app):
    @app.get("/simple")
    async def simple_route():
        return {"plugin": "Simple"}

plugin = SimplePlugin("simple-plugin", setup_plugin)
Plugin Lifecycle
python
class LifecyclePlugin(Plugin):
    name = "lifecycle-plugin"
    version = "1.0.0"

    def on_load(self):
        """Called when the plugin is loaded."""
        print("Plugin loaded")

    def setup(self, app):
        """Called during plugin setup."""
        print("Plugin setup")

    def on_startup(self):
        """Called during application startup."""
        print("Plugin startup")

    def on_shutdown(self):
        """Called during application shutdown."""
        print("Plugin shutdown")

    def on_unload(self):
        """Called when the plugin is unloaded."""
        print("Plugin unloaded")
Plugin Dependencies
python
class CorePlugin(Plugin):
    name = "core-plugin"
    version = "1.0.0"
    provides = ["database", "cache"]

class DatabasePlugin(Plugin):
    name = "database-plugin"
    version = "1.0.0"
    requires = ["core-plugin"]
    provides = ["postgres"]

class CachePlugin(Plugin):
    name = "cache-plugin"
    version = "1.0.0"
    requires = ["core-plugin"]
    provides = ["redis"]
Plugin Discovery
Auto-Discovery from Directory
python
from flaxon.plugins import PluginManager

manager = PluginManager(app)

# Load all plugins from the "plugins" directory
await manager.load_plugins_from_path("plugins")
Auto-Discovery from Module
python
# Load plugins from a module
await manager.load_plugins_from_module("myapp.plugins")

# Load all plugins from all sources
await manager.load_all_plugins()
Plugin Hooks
Defining Hooks
python
from flaxon.plugins import PluginHooks

class HookPlugin(Plugin):
    name = "hook-plugin"
    version = "1.0.0"

    def setup(self, app):
        # Register a hook handler
        app.plugin_hooks.register("before_response", self.before_response)

    def before_response(self, response):
        response.headers["X-Hook"] = "processed"
        return response
Triggering Hooks
python
# In your application code
await app.plugin_hooks.trigger_async("before_response", response)

# Or synchronously
app.plugin_hooks.trigger("before_response", response)
Complete Plugin Example
python
from flaxon import Flaxon
from flaxon.plugins import Plugin, PluginManager
from flaxon.middleware import Middleware
from flaxon.health import HealthCheck

class PluginMiddleware(Middleware):
    def __init__(self, app):
        super().__init__(app)
        self.header_name = "x-plugin"

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.header_name.encode(), b"active"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "A complete plugin example"
    author = "Flaxon Team"
    requires = []
    provides = ["custom-feature"]

    def __init__(self):
        self._routes = []
        self._middleware = []

    def setup(self, app):
        # Add routes
        @app.get("/plugin")
        async def plugin_route():
            return {
                "plugin": self.name,
                "version": self.version,
                "status": "active",
            }

        # Add middleware
        app.add_middleware(PluginMiddleware)

        # Add health check
        app.health.register(HealthCheck("plugin", self.check_health))

        # Store plugin data
        app.state.plugin = self

    def on_startup(self):
        print(f"Plugin {self.name} starting up...")

    def on_shutdown(self):
        print(f"Plugin {self.name} shutting down...")

    async def check_health(self):
        return {
            "status": "healthy",
            "plugin": self.name,
            "version": self.version,
        }
Using Plugins
python
# Create application
app = Flaxon("my-app")

# Create plugin manager
manager = PluginManager(app)

# Load individual plugin
plugin = MyPlugin()
await manager.load_plugin(plugin)

# Or discover and load all plugins
await manager.load_all_plugins()

# List loaded plugins
print(manager.list_plugins())
# ['my-plugin']

# Check if plugin is loaded
if manager.is_loaded("my-plugin"):
    print("Plugin is active")

# Get plugin instance
loaded_plugin = manager.get_plugin("my-plugin")
CLI Plugin Commands
python
from flaxon.cli import Command

class PluginCommand(Command):
    name = "plugin"
    help_text = "Plugin management commands"

    def __init__(self):
        super().__init__(
            name="plugin",
            handler=self._run,
            help_text="List and manage plugins",
        )

    def _add_arguments(self, parser):
        parser.add_argument("action", choices=["list", "load", "unload"])
        parser.add_argument("plugin", nargs="?")

    def _run(self, args, console):
        manager = PluginManager(app)
        if args.action == "list":
            for name in manager.list_plugins():
                console.info(f"  - {name}")
        return 0

# Register CLI command
app.cli.add_command(PluginCommand())
Plugin Health Checks
python
class HealthPlugin(Plugin):
    name = "health-plugin"

    def setup(self, app):
        app.health.register("plugin-health", self.check)

    async def check(self):
        return {
            "status": "healthy",
            "message": "Plugin is working",
        }
Plugin Configuration
python
class ConfigPlugin(Plugin):
    name = "config-plugin"

    def setup(self, app):
        # Access configuration
        debug = app.config.get("PLUGIN_DEBUG", False)
        api_key = app.config.get("PLUGIN_API_KEY")

        if not api_key:
            raise ValueError("PLUGIN_API_KEY is required")

        # Store configuration
        self.config = {
            "debug": debug,
            "api_key": api_key,
        }

        # Setup with configuration
        @app.get("/plugin/config")
        async def config_route():
            return self.config
Plugin Events
python
from flaxon.events import Event, EventListener

class EventPlugin(Plugin):
    name = "event-plugin"

    def setup(self, app):
        # Register event listener
        @app.events.listener("user.created")
        async def on_user_created(event):
            print(f"User created: {event.data['username']}")

        # Or using the EventListener class
        listener = EventListener("user.updated", self.on_user_updated)
        app.events.register(listener)

    def on_user_updated(self, event):
        print(f"User updated: {event.data['username']}")
Error Handling in Plugins
python
class RobustPlugin(Plugin):
    name = "robust-plugin"

    def setup(self, app):
        try:
            # Attempt to setup plugin
            self._setup_internal(app)
        except Exception as exc:
            # Log error and continue
            print(f"Plugin setup failed: {exc}")
            app.state.plugin_error = str(exc)

    def _setup_internal(self, app):
        # Risky setup code
        pass
Plugin Best Practices
1. Use Clear Names
python
class DatabasePlugin(Plugin):
    name = "database"
    # Not "db-plugin" or "my-database-plugin"
2. Document Dependencies
python
class AuthPlugin(Plugin):
    name = "auth"
    requires = ["database", "session"]
    provides = ["jwt", "oauth2"]
3. Handle Missing Dependencies
python
class DependentPlugin(Plugin):
    name = "dependent"
    requires = ["core"]

    def setup(self, app):
        if "core" not in app.state:
            raise RuntimeError("Core plugin is required")
4. Clean Up Resources
python
class ResourcePlugin(Plugin):
    name = "resource"

    def on_startup(self):
        self.pool = await create_pool()

    def on_shutdown(self):
        if hasattr(self, "pool"):
            await self.pool.close()
5. Version Compatibility
python
class CompatiblePlugin(Plugin):
    name = "compatible"
    version = "2.0.0"

    def setup(self, app):
        if app.version < (0, 2, 0):
            raise RuntimeError("Plugin requires Flaxon 0.2.0+")
Testing Plugins
python
import pytest
from flaxon import Flaxon
from flaxon.plugins import PluginManager

def test_plugin_loading():
    app = Flaxon("test-app")
    manager = PluginManager(app)

    plugin = MyPlugin()
    import asyncio
    asyncio.run(manager.load_plugin(plugin))

    assert manager.is_loaded("my-plugin") is True

def test_plugin_route():
    app = Flaxon("test-app")
    manager = PluginManager(app)

    plugin = MyPlugin()
    import asyncio
    asyncio.run(manager.load_plugin(plugin))

    from flaxon.testing import TestClient
    client = TestClient(app)
    response = client.get("/plugin")

    assert response.status_code == 200
    assert response.json()["plugin"] == "my-plugin"
Complete Plugin Example
python
# plugins/database_plugin.py
from flaxon.plugins import Plugin

class DatabasePlugin(Plugin):
    name = "database"
    version = "1.0.0"
    description = "Database connection management"

    def __init__(self):
        self.pool = None

    def setup(self, app):
        # Read configuration
        url = app.config.get("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL is required")

        # Setup connection pool
        @app.on_startup
        async def connect():
            self.pool = await create_pool(url)
            app.state.db = self.pool

        @app.on_shutdown
        async def disconnect():
            if self.pool:
                await self.pool.close()

        # Add health check
        @app.get("/health/db")
        async def db_health():
            if self.pool:
                return {"status": "healthy"}
            return {"status": "unhealthy"}

# main.py
from flaxon import Flaxon
from flaxon.plugins import PluginManager

app = Flaxon("my-app")
app.config.update({
    "DATABASE_URL": "postgresql://user:pass@localhost/db",
})

# Load plugin
manager = PluginManager(app)
import asyncio
asyncio.run(manager.load_plugins_from_path("plugins"))

# Use database
@app.get("/users")
async def get_users():
    async with app.state.db.acquire() as conn:
        return await conn.fetch("SELECT * FROM users")