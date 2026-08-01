
---

### `docs/api/admin.md`

```markdown
# Admin API Reference

::: flaxon.admin.AdminDashboard
    options:
        members:
            - __init__
            - register
            - unregister
            - index
            - list_view
            - add_view
            - detail_view
            - edit_view
            - delete_view
            - get_urls

::: flaxon.admin.AdminConfig
    options:
        members:
            - __init__
            - to_dict

::: flaxon.admin.Registry
    options:
        members:
            - register
            - unregister
            - get
            - get_by_model
            - get_all
            - clear

::: flaxon.admin.AdminModel
    options:
        members:
            - __init__
            - get_name
            - get_verbose_name
            - get_verbose_name_plural
            - add_action
            - get_actions

::: flaxon.admin.views.AdminView
    options:
        members:
            - __init__
            - render

::: flaxon.admin.views.ChangeListView
    options:
        members:
            - render

::: flaxon.admin.views.DetailView
    options:
        members:
            - render

::: flaxon.admin.views.CreateView
    options:
        members:
            - render

::: flaxon.admin.views.UpdateView
    options:
        members:
            - render

::: flaxon.admin.views.DeleteView
    options:
        members:
            - render

::: flaxon.admin.decorators.admin_model
    options:
        show_source: false

::: flaxon.admin.decorators.admin_action
    options:
        show_source: false

::: flaxon.admin.decorators.admin_display
    options:
        show_source: false

::: flaxon.admin.exceptions.AdminError
::: flaxon.admin.exceptions.ModelNotFoundError
::: flaxon.admin.exceptions.PermissionDeniedError
::: flaxon.admin.exceptions.ValidationError