from flaxon import Flaxon
from builder import builder_module

app = Flaxon("builder-demo", debug=True)
app.mount_module(builder_module, prefix="/builder")