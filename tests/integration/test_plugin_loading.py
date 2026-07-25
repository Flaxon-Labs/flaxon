import tempfile
from pathlib import Path

import pytest

from flaxon import Flaxon
from flaxon.plugins import Plugin, PluginManager, SimplePlugin
from flaxon.testing import TestClient


class TestPlugin(Plugin):
    name = "test-plugin"
    version = "1.0.0"
    description = "A test plugin"

    def __init__(self):
        self.setup_called = False
        self.load_called = False
        self.unload_called = False

    def setup(self, app):
        self.setup_called = True
        app.state.plugin_loaded = True

    def on_load(self):
        self.load_called = True

    def on_unload(self):
        self.unload_called = True


def test_plugin_load():
    app = Flaxon("test-plugin-app")
    plugin = TestPlugin()

    manager = PluginManager(app)
    import asyncio
    asyncio.run(manager.load_plugin(plugin))

    assert plugin.load_called is True
    assert plugin.setup_called is True
    assert app.state.plugin_loaded is True
    assert manager.is_loaded("test-plugin") is True


def test_plugin_unload():
    app = Flaxon("test-plugin-app")
    plugin = TestPlugin()

    manager = PluginManager(app)
    import asyncio
    asyncio.run(manager.load_plugin(plugin))
    asyncio.run(manager.unload_plugin("test-plugin"))

    assert plugin.unload_called is True
    assert manager.is_loaded("test-plugin") is False


def test_plugin_requires():
    class DependentPlugin(Plugin):
        name = "dependent-plugin"
        version = "1.0.0"
        requires = ["test-plugin"]

        def setup(self, app):
            pass

    app = Flaxon("test-requires")
    manager = PluginManager(app)

    dependent = DependentPlugin()

    import asyncio
    with pytest.raises(Exception):
        asyncio.run(manager.load_plugin(dependent))


def test_plugin_discovery_from_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)

        plugin_file = path / "test_plugin.py"
        plugin_file.write_text("""
from flaxon.plugins import SimplePlugin

def setup(app):
    app.state.discovered = True

plugin = SimplePlugin("discovered-plugin", setup)
""")

        app = Flaxon("test-discovery")
        manager = PluginManager(app)

        import asyncio
        asyncio.run(manager.load_plugins_from_path(str(path)))

        assert manager.is_loaded("discovered-plugin") is True
        assert app.state.discovered is True


def test_plugin_hooks():
    app = Flaxon("test-hooks")
    manager = PluginManager(app)

    hook_called = False

    def after_load_handler(plugin):
        nonlocal hook_called
        hook_called = True

    manager.hooks.register("after_load", after_load_handler)

    plugin = TestPlugin()
    import asyncio
    asyncio.run(manager.load_plugin(plugin))

    assert hook_called is True