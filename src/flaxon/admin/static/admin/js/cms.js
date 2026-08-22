  const API_BASE = "__CMS_API_BASE__";

    function cmsApp() {
      return {
        title: "__CMS_TITLE__",
        types: [],
        stats: {},
        view: "dashboard",
        currentType: null,
        error: null,

        listItems: [],
        listMeta: { total: 0, page: 1, pages: 1, per_page: 20 },
        listQuery: { q: "" },
        selected: [],
        bulkAction: "",

        editingId: null,
        formData: {},

        async init() {
          await this.loadConfig();
          window.addEventListener("hashchange", () => this.route());
          this.route();
        },

        async api(path, options = {}) {
          try {
            const res = await fetch(API_BASE + path, {
              headers: { "Content-Type": "application/json" },
              ...options,
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
              this.error = data.message || data.error || `Request failed (${res.status})`;
              return null;
            }
            return data;
          } catch (e) {
            this.error = "Network error: " + e.message;
            return null;
          }
        },

        async loadConfig() {
          const config = await this.api("/config");
          if (config) {
            this.title = config.title;
            this.types = config.types;
          }
          const stats = await this.api("/stats");
          if (stats) this.stats = stats;
        },

        route() {
          const hash = window.location.hash.replace(/^#\/?/, "");
          const parts = hash.split("/").filter(Boolean);
          if (parts.length === 0) {
            this.view = "dashboard";
            this.currentType = null;
          } else if (parts.length === 1) {
            this.openList(parts[0], false);
          } else if (parts[1] === "new") {
            this.openCreate(parts[0], false);
          } else if (parts[2] === "edit") {
            this.openEdit(parts[0], parts[1], false);
          }
        },

        goHome() {
          window.location.hash = "";
        },

        findType(name) {
          return this.types.find((t) => t.name === name) || null;
        },

        async openList(typeName, pushHash = true) {
          this.currentType = this.findType(typeName);
          if (!this.currentType) return;
          this.view = "list";
          this.selected = [];
          this.bulkAction = "";
          this.listQuery = { q: "" };
          this.listMeta.page = 1;
          if (pushHash) window.location.hash = `#/${typeName}`;
          await this.fetchList();
        },

        async fetchList() {
          if (!this.currentType) return;
          const params = new URLSearchParams();
          if (this.listQuery.q) params.set("q", this.listQuery.q);
          Object.keys(this.listQuery).forEach((k) => {
            if (k.startsWith("filter_") && this.listQuery[k]) params.set(k, this.listQuery[k]);
          });
          params.set("page", this.listMeta.page);
          const data = await this.api(`/${this.currentType.name}/items?` + params.toString());
          if (data) {
            this.listItems = data.items;
            this.listMeta = { total: data.total, page: data.page, pages: data.pages, per_page: data.per_page };
          }
        },

        changePage(delta) {
          const next = this.listMeta.page + delta;
          if (next < 1 || next > this.listMeta.pages) return;
          this.listMeta.page = next;
          this.fetchList();
        },

        toggleSelectAll(evt) {
          this.selected = evt.target.checked ? this.listItems.map((i) => i.id) : [];
        },

        async runBulkAction() {
          if (!this.bulkAction || !this.selected.length) return;
          const ok = await this.api(`/${this.currentType.name}/actions/${this.bulkAction}`, {
            method: "POST",
            body: JSON.stringify({ ids: this.selected }),
          });
          if (ok) {
            this.selected = [];
            this.bulkAction = "";
            await this.fetchList();
            await this.loadConfig();
          }
        },

        async deleteItem(id) {
          if (!confirm("Delete this item?")) return;
          const ok = await this.api(`/${this.currentType.name}/items/${id}`, { method: "DELETE" });
          if (ok) {
            await this.fetchList();
            await this.loadConfig();
          }
        },

        openCreate(typeName, pushHash = true) {
          this.currentType = this.findType(typeName);
          if (!this.currentType) return;
          this.editingId = null;
          this.formData = { status: "draft", slug: "" };
          this.currentType.fields.forEach((f) => {
            this.formData[f.name] = f.type === "boolean" ? false : "";
          });
          this.view = "form";
          if (pushHash) window.location.hash = `#/${typeName}/new`;
        },

        async openEdit(typeName, itemId, pushHash = true) {
          this.currentType = this.findType(typeName);
          if (!this.currentType) return;
          const item = await this.api(`/${typeName}/items/${itemId}`);
          if (!item) return;
          this.editingId = itemId;
          this.formData = { ...item };
          this.view = "form";
          if (pushHash) window.location.hash = `#/${typeName}/${itemId}/edit`;
        },

        async saveItem() {
          const typeName = this.currentType.name;
          if (this.editingId) {
            const ok = await this.api(`/${typeName}/items/${this.editingId}`, {
              method: "PUT",
              body: JSON.stringify(this.formData),
            });
            if (ok) this.openList(typeName);
          } else {
            const ok = await this.api(`/${typeName}/items`, {
              method: "POST",
              body: JSON.stringify(this.formData),
            });
            if (ok) this.openList(typeName);
          }
          await this.loadConfig();
        },

        formatCell(value) {
          if (value === null || value === undefined) return "";
          if (typeof value === "string" && value.length > 60) return value.slice(0, 57) + "...";
          return value;
        },
      };
    }