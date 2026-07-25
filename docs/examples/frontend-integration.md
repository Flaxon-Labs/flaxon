# Frontend Integration Examples

This document demonstrates how Flaxon can be used as a backend for the top 5 JavaScript frameworks.

---

## 1. React

### Backend Setup

```python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("react-backend")

# Configure CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
)

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/products")
async def get_products():
    return [
        {"id": 1, "name": "Product A", "price": 29.99},
        {"id": 2, "name": "Product B", "price": 49.99},
    ]

@app.post("/api/orders")
async def create_order(request):
    data = await request.json()
    return {"order_id": 123, "status": "created", "items": data.get("items")}

@app.get("/api/users/<int:user_id>")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}


    React Client Code
javascript
// src/services/api.js
const API_URL = "http://localhost:8000/api";

export const api = {
  async getProducts() {
    const res = await fetch(`${API_URL}/products`);
    return res.json();
  },

  async createOrder(items) {
    const res = await fetch(`${API_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items }),
    });
    return res.json();
  },

  async getUser(id) {
    const res = await fetch(`${API_URL}/users/${id}`);
    return res.json();
  },
};
jsx
// src/App.jsx
import React, { useState, useEffect } from "react";
import { api } from "./services/api";

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProducts().then((data) => {
      setProducts(data);
      setLoading(false);
    });
  }, []);

  const handleOrder = async (productId) => {
    const result = await api.createOrder([{ productId, quantity: 1 }]);
    alert(`Order ${result.order_id} created!`);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Products</h1>
      {products.map((p) => (
        <div key={p.id}>
          <h3>{p.name}</h3>
          <p>${p.price}</p>
          <button onClick={() => handleOrder(p.id)}>Buy</button>
        </div>
      ))}
    </div>
  );
}

export default App;
2. Vue.js
Backend Setup
python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("vue-backend")

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:5173"],
    allow_credentials=True,
)

@app.get("/api/tasks")
async def get_tasks():
    return [
        {"id": 1, "title": "Task 1", "completed": False},
        {"id": 2, "title": "Task 2", "completed": True},
    ]

@app.post("/api/tasks")
async def create_task(request):
    data = await request.json()
    return {"id": 3, "title": data["title"], "completed": False}

@app.put("/api/tasks/<int:task_id>")
async def update_task(task_id: int, request):
    data = await request.json()
    return {"id": task_id, "title": data["title"], "completed": data.get("completed", False)}

@app.delete("/api/tasks/<int:task_id>")
async def delete_task(task_id: int):
    return {"deleted": True, "id": task_id}
Vue Client Code
vue
// src/services/api.js
const API_URL = "http://localhost:8000/api";

export default {
  async getTasks() {
    const res = await fetch(`${API_URL}/tasks`);
    return res.json();
  },

  async createTask(title) {
    const res = await fetch(`${API_URL}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    return res.json();
  },

  async updateTask(id, data) {
    const res = await fetch(`${API_URL}/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  async deleteTask(id) {
    const res = await fetch(`${API_URL}/tasks/${id}`, { method: "DELETE" });
    return res.json();
  },
};
vue
<!-- src/App.vue -->
<template>
  <div>
    <h1>Tasks</h1>
    <input v-model="newTask" @keyup.enter="addTask" placeholder="Add task..." />
    <ul>
      <li v-for="task in tasks" :key="task.id">
        <input type="checkbox" :checked="task.completed" @change="toggleTask(task)" />
        <span :class="{ done: task.completed }">{{ task.title }}</span>
        <button @click="removeTask(task.id)">Delete</button>
      </li>
    </ul>
  </div>
</template>

<script>
import api from "./services/api";

export default {
  data() {
    return {
      tasks: [],
      newTask: "",
    };
  },
  mounted() {
    this.loadTasks();
  },
  methods: {
    async loadTasks() {
      this.tasks = await api.getTasks();
    },
    async addTask() {
      if (this.newTask.trim()) {
        const task = await api.createTask(this.newTask);
        this.tasks.push(task);
        this.newTask = "";
      }
    },
    async toggleTask(task) {
      const updated = await api.updateTask(task.id, {
        ...task,
        completed: !task.completed,
      });
      Object.assign(task, updated);
    },
    async removeTask(id) {
      await api.deleteTask(id);
      this.tasks = this.tasks.filter((t) => t.id !== id);
    },
  },
};
</script>

<style>
.done { text-decoration: line-through; color: #888; }
</style>
3. Angular
Backend Setup
python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("angular-backend")

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:4200"],
    allow_credentials=True,
)

@app.get("/api/posts")
async def get_posts():
    return [
        {"id": 1, "title": "Post 1", "body": "Content 1", "author": "Alice"},
        {"id": 2, "title": "Post 2", "body": "Content 2", "author": "Bob"},
    ]

@app.get("/api/posts/<int:post_id>")
async def get_post(post_id: int):
    return {"id": post_id, "title": f"Post {post_id}", "body": f"Content {post_id}"}

@app.post("/api/posts")
async def create_post(request):
    data = await request.json()
    return {"id": 3, "title": data["title"], "body": data["body"]}

@app.get("/api/users")
async def get_users():
    return [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ]
Angular Client Code
typescript
// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Post {
  id: number;
  title: string;
  body: string;
  author?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getPosts(): Observable<Post[]> {
    return this.http.get<Post[]>(`${this.apiUrl}/posts`);
  }

  getPost(id: number): Observable<Post> {
    return this.http.get<Post>(`${this.apiUrl}/posts/${id}`);
  }

  createPost(post: { title: string; body: string }): Observable<Post> {
    return this.http.post<Post>(`${this.apiUrl}/posts`, post);
  }

  getUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/users`);
  }
}
typescript
// src/app/app.component.ts
import { Component, OnInit } from '@angular/core';
import { ApiService, Post } from './services/api.service';

@Component({
  selector: 'app-root',
  template: `
    <div>
      <h1>Posts</h1>
      <div *ngIf="loading">Loading...</div>
      <div *ngFor="let post of posts">
        <h3>{{ post.title }}</h3>
        <p>{{ post.body }}</p>
        <small>By: {{ post.author || 'Unknown' }}</small>
        <hr />
      </div>
      <h2>Create New Post</h2>
      <input [(ngModel)]="newPost.title" placeholder="Title" />
      <textarea [(ngModel)]="newPost.body" placeholder="Body"></textarea>
      <button (click)="addPost()">Create</button>
    </div>
  `
})
export class AppComponent implements OnInit {
  posts: Post[] = [];
  loading = true;
  newPost = { title: '', body: '' };

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadPosts();
  }

  async loadPosts() {
    this.loading = true;
    this.posts = await this.api.getPosts().toPromise();
    this.loading = false;
  }

  async addPost() {
    if (this.newPost.title && this.newPost.body) {
      const post = await this.api.createPost(this.newPost).toPromise();
      this.posts.push(post);
      this.newPost = { title: '', body: '' };
    }
  }
}
4. Svelte
Backend Setup
python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("svelte-backend")

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:5173"],
    allow_credentials=True,
)

@app.get("/api/notes")
async def get_notes():
    return [
        {"id": 1, "title": "Note 1", "content": "Content 1", "color": "yellow"},
        {"id": 2, "title": "Note 2", "content": "Content 2", "color": "blue"},
    ]

@app.post("/api/notes")
async def create_note(request):
    data = await request.json()
    return {"id": 3, "title": data["title"], "content": data["content"], "color": data.get("color", "white")}

@app.put("/api/notes/<int:note_id>")
async def update_note(note_id: int, request):
    data = await request.json()
    return {"id": note_id, "title": data["title"], "content": data["content"], "color": data.get("color", "white")}

@app.delete("/api/notes/<int:note_id>")
async def delete_note(note_id: int):
    return {"deleted": True, "id": note_id}
Svelte Client Code
javascript
// src/api.js
const API_URL = "http://localhost:8000/api";

export async function getNotes() {
  const res = await fetch(`${API_URL}/notes`);
  return res.json();
}

export async function createNote(note) {
  const res = await fetch(`${API_URL}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(note),
  });
  return res.json();
}

export async function updateNote(id, note) {
  const res = await fetch(`${API_URL}/notes/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(note),
  });
  return res.json();
}

export async function deleteNote(id) {
  const res = await fetch(`${API_URL}/notes/${id}`, { method: "DELETE" });
  return res.json();
}
svelte
<!-- src/App.svelte -->
<script>
  import { getNotes, createNote, deleteNote } from "./api";

  let notes = [];
  let newTitle = "";
  let newContent = "";
  let loading = true;

  async function loadNotes() {
    loading = true;
    notes = await getNotes();
    loading = false;
  }

  async function addNote() {
    if (newTitle && newContent) {
      const note = await createNote({
        title: newTitle,
        content: newContent,
        color: "yellow",
      });
      notes = [...notes, note];
      newTitle = "";
      newContent = "";
    }
  }

  async function removeNote(id) {
    await deleteNote(id);
    notes = notes.filter((n) => n.id !== id);
  }

  $: loadNotes();
</script>

<div>
  <h1>Notes</h1>

  {#if loading}
    <p>Loading...</p>
  {:else}
    <div class="notes">
      {#each notes as note}
        <div class="note" style="background: {note.color}">
          <h3>{note.title}</h3>
          <p>{note.content}</p>
          <button on:click={() => removeNote(note.id)}>Delete</button>
        </div>
      {/each}
    </div>
  {/if}

  <h2>New Note</h2>
  <input bind:value={newTitle} placeholder="Title" />
  <textarea bind:value={newContent} placeholder="Content" />
  <button on:click={addNote}>Add Note</button>
</div>

<style>
  .notes {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
  }
  .note {
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #ddd;
  }
  .note button {
    margin-top: 0.5rem;
  }
</style>

5. Next.js
Backend Setup
python
# app.py
from flaxon import Flaxon
from flaxon.middleware import CORSMiddleware

app = Flaxon("nextjs-backend")

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:3000"],
    allow_credentials=True,
)

@app.get("/api/blog/posts")
async def get_posts():
    return [
        {"id": 1, "title": "Post 1", "slug": "post-1", "excerpt": "Excerpt 1", "published_at": "2024-01-01"},
        {"id": 2, "title": "Post 2", "slug": "post-2", "excerpt": "Excerpt 2", "published_at": "2024-01-02"},
    ]

@app.get("/api/blog/posts/<slug:slug>")
async def get_post(slug: str):
    return {"id": 1, "title": "Post 1", "slug": slug, "content": "Full content here", "published_at": "2024-01-01"}

@app.post("/api/auth/login")
async def login(request):
    data = await request.json()
    return {"token": "jwt-token", "user": {"id": 1, "name": data.get("username", "User")}}

@app.get("/api/profile")
async def get_profile(request):
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    return {"id": 1, "name": "User", "email": "user@example.com"}
Next.js Client Code
typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchPosts() {
  const res = await fetch(`${API_URL}/blog/posts`);
  return res.json();
}

export async function fetchPost(slug: string) {
  const res = await fetch(`${API_URL}/blog/posts/${slug}`);
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function getProfile(token: string) {
  const res = await fetch(`${API_URL}/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}
tsx
// pages/index.tsx
import { GetServerSideProps } from "next";
import Link from "next/link";
import { fetchPosts } from "../lib/api";

interface Post {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  published_at: string;
}

interface HomeProps {
  posts: Post[];
}

export default function Home({ posts }: HomeProps) {
  return (
    <div>
      <h1>Blog</h1>
      {posts.map((post) => (
        <article key={post.id}>
          <h2>
            <Link href={`/blog/${post.slug}`}>
              <a>{post.title}</a>
            </Link>
          </h2>
          <p>{post.excerpt}</p>
          <small>Published: {post.published_at}</small>
        </article>
      ))}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps = async () => {
  const posts = await fetchPosts();
  return { props: { posts } };
};
tsx
// pages/blog/[slug].tsx
import { GetStaticPaths, GetStaticProps } from "next";
import { fetchPosts, fetchPost } from "../../lib/api";

interface PostPageProps {
  post: {
    id: number;
    title: string;
    slug: string;
    content: string;
    published_at: string;
  };
}

export default function PostPage({ post }: PostPageProps) {
  return (
    <div>
      <h1>{post.title}</h1>
      <small>Published: {post.published_at}</small>
      <div>{post.content}</div>
    </div>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await fetchPosts();
  const paths = posts.map((post: any) => ({ params: { slug: post.slug } }));
  return { paths, fallback: false };
};

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const post = await fetchPost(params?.slug as string);
  return { props: { post } };
};


Summary
Framework	Port	Features Used
React	5173	CORS, REST API, JSON responses
Vue	5173	CORS, REST API, CRUD operations
Angular	4200	CORS, REST API, Observables
Svelte	5173	CORS, REST API, Reactive state
Next.js	3000	CORS, SSR, API routes, Dynamic routing
All examples use CORS middleware to allow cross-origin requests from the frontend development servers. The backend provides RESTful JSON APIs that can be consumed by any of these frontend frameworks.