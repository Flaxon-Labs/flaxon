# Admin API Reference

## Admin Dashboard

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

---

## Admin Configuration

::: flaxon.admin.AdminConfig
    options:
        members:
            - __init__
            - to_dict

---

## Registry

::: flaxon.admin.Registry
    options:
        members:
            - register
            - unregister
            - get
            - get_by_model
            - get_all
            - clear

---

## Admin Model

::: flaxon.admin.AdminModel
    options:
        members:
            - __init__
            - get_name
            - get_verbose_name
            - get_verbose_name_plural
            - add_action
            - get_actions

---

# Admin Views

## Base View

::: flaxon.admin.views.AdminView
    options:
        members:
            - __init__
            - render

---

## Change List View

::: flaxon.admin.views.ChangeListView
    options:
        members:
            - render

---

## Detail View

::: flaxon.admin.views.DetailView
    options:
        members:
            - render

---

## Create View

::: flaxon.admin.views.CreateView
    options:
        members:
            - render

---

## Update View

::: flaxon.admin.views.UpdateView
    options:
        members:
            - render

---

## Delete View

::: flaxon.admin.views.DeleteView
    options:
        members:
            - render

---

# Decorators

## admin_model

::: flaxon.admin.decorators.admin_model
    options:
        show_source: false

---

## admin_action

::: flaxon.admin.decorators.admin_action
    options:
        show_source: false

---

## admin_display

::: flaxon.admin.decorators.admin_display
    options:
        show_source: false

---

# Exceptions

## AdminError

::: flaxon.admin.exceptions.AdminError

---

## ModelNotFoundError

::: flaxon.admin.exceptions.ModelNotFoundError

---

## PermissionDeniedError

::: flaxon.admin.exceptions.PermissionDeniedError

---

## ValidationError

::: flaxon.admin.exceptions.ValidationError