
---

### `docs/examples/graphql-api.md`

```markdown
# GraphQL API Example

This example demonstrates a complete Flaxon GraphQL API with queries, mutations, and subscriptions.

## Running the Example

```bash
# Create a new Flaxon project
flaxon new graphql-example
cd graphql-example

# Install dependencies
pip install flaxon

# Create app.py with the code below
# Run the app
flaxon run app:app --reload


Full Example Code
app.py
python
from flaxon import Flaxon
from flaxon.graphql import (
    GraphQLSchema,
    ObjectType,
    Field,
    String,
    Int,
    List,
    NonNull,
    graphql_query,
    graphql_mutation,
    graphql_subscription,
    MemorySubscriptionBackend,
    SubscriptionManager,
)

app = Flaxon("graphql-example", debug=True)

# --- Data Layer ---
users = []
posts = []
user_id_counter = 1
post_id_counter = 1

# --- GraphQL Types ---

class UserType(ObjectType):
    """User object type."""
    name = "User"
    id = Field(Int)
    name = Field(String)
    email = Field(String)
    posts = Field(List("Post"))

    @staticmethod
    def resolve_posts(parent, args, context, info):
        return [p for p in posts if p["author_id"] == parent["id"]]

class PostType(ObjectType):
    """Post object type."""
    name = "Post"
    id = Field(Int)
    title = Field(String)
    content = Field(String)
    author_id = Field(Int)
    author = Field("User")

    @staticmethod
    def resolve_author(parent, args, context, info):
        return next((u for u in users if u["id"] == parent["author_id"]), None)

# --- Root Query ---

class Query(ObjectType):
    """Root Query type."""
    name = "Query"

    hello = Field(String, name=String(required=False))
    user = Field(UserType, id=Int(required=True))
    users = Field(List(UserType))
    post = Field(PostType, id=Int(required=True))
    posts = Field(List(PostType))

    @staticmethod
    def resolve_hello(parent, args, context, info) -> str:
        name = args.get("name", "World")
        return f"Hello, {name}!"

    @staticmethod
    def resolve_user(parent, args, context, info) -> dict | None:
        return next((u for u in users if u["id"] == args["id"]), None)

    @staticmethod
    def resolve_users(parent, args, context, info) -> list:
        return users

    @staticmethod
    def resolve_post(parent, args, context, info) -> dict | None:
        return next((p for p in posts if p["id"] == args["id"]), None)

    @staticmethod
    def resolve_posts(parent, args, context, info) -> list:
        return posts

# --- Root Mutation ---

class Mutation(ObjectType):
    """Root Mutation type."""
    name = "Mutation"

    create_user = Field(UserType, name=String(required=True), email=String(required=True))
    create_post = Field(PostType, title=String(required=True), content=String(required=True), author_id=Int(required=True))

    @staticmethod
    async def resolve_create_user(parent, args, context, info) -> dict:
        global user_id_counter
        user = {
            "id": user_id_counter,
            "name": args["name"],
            "email": args["email"],
        }
        user_id_counter += 1
        users.append(user)

        # Publish subscription event
        subscription_manager = context.get("subscription_manager")
        if subscription_manager:
            await subscription_manager.publish("user_created", user)

        return user

    @staticmethod
    async def resolve_create_post(parent, args, context, info) -> dict:
        global post_id_counter
        post = {
            "id": post_id_counter,
            "title": args["title"],
            "content": args["content"],
            "author_id": args["author_id"],
        }
        post_id_counter += 1
        posts.append(post)

        # Publish subscription event
        subscription_manager = context.get("subscription_manager")
        if subscription_manager:
            await subscription_manager.publish("post_created", post)

        return post

# --- Root Subscription ---

class Subscription(ObjectType):
    """Root Subscription type."""
    name = "Subscription"

    user_created = Field(UserType)
    post_created = Field(PostType)

    @staticmethod
    async def resolve_user_created(parent, args, context, info):
        subscription_manager = context.get("subscription_manager")
        if subscription_manager:
            async for event in subscription_manager.next(context.get("subscription_id")):
                yield event

    @staticmethod
    async def resolve_post_created(parent, args, context, info):
        subscription_manager = context.get("subscription_manager")
        if subscription_manager:
            async for event in subscription_manager.next(context.get("subscription_id")):
                yield event

# --- Schema and Setup ---

# Create schema
schema = GraphQLSchema(query=Query, mutation=Mutation, subscription=Subscription)

# Setup subscription backend
subscription_backend = MemorySubscriptionBackend()
subscription_manager = SubscriptionManager(subscription_backend)

# Enable GraphQL with custom context
app.enable_graphql(
    schema,
    subscription_backend=subscription_backend,
)

# Store subscription manager in app state
app.state.subscription_manager = subscription_manager

# --- Seed Data ---

import asyncio

async def seed_data():
    # Create a test user
    user = {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
    }
    users.append(user)

    # Create test posts
    posts.append({
        "id": 1,
        "title": "First Post",
        "content": "Hello, GraphQL!",
        "author_id": 1,
    })
    posts.append({
        "id": 2,
        "title": "Second Post",
        "content": "GraphQL is awesome!",
        "author_id": 1,
    })

asyncio.run(seed_data())

# --- Welcome Route ---

@app.get("/")
async def home(request):
    return {
        "message": "Welcome to the GraphQL API Example!",
        "graphql_endpoint": "/graphql",
        "playground": "/graphql/graphiql",
        "queries": [
            "query { hello(name: \"Flaxon\") }",
            "query { users { id name email posts { title } } }",
            "query { user(id: 1) { name email posts { title content } } }",
        ],
        "mutations": [
            "mutation { createUser(name: \"Bob\", email: \"bob@example.com\") { id name } }",
            "mutation { createPost(title: \"New Post\", content: \"Content...\", author_id: 1) { id title } }",
        ],
        "subscriptions": [
            "subscription { userCreated { id name email } }",
            "subscription { postCreated { id title content } }",
        ],
    }

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, reload=True)
Testing the API
1. Using GraphiQL
Visit /graphql/graphiql to use the GraphiQL playground.

2. Example Queries
Hello Query:

graphql
query {
  hello(name: "Flaxon")
}
List Users:

graphql
query {
  users {
    id
    name
    email
    posts {
      title
      content
    }
  }
}
Get User with Posts:

graphql
query {
  user(id: 1) {
    name
    email
    posts {
      title
      content
    }
  }
}

3. Example Mutations
Create User:

graphql
mutation {
  createUser(name: "Bob", email: "bob@example.com") {
    id
    name
    email
  }
}
Create Post:

graphql
mutation {
  createPost(title: "New Post", content: "Content...", author_id: 1) {
    id
    title
    content
  }
}

4. Example Subscriptions
Subscribe to User Creation:

graphql
subscription {
  userCreated {
    id
    name
    email
  }
}
Subscribe to Post Creation:

graphql
subscription {
  postCreated {
    id
    title
    content
    author {
      name
    }
  }
}


Using with curl
bash
# Query
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { hello(name: \"Flaxon\") }"}'

# Mutation
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { createUser(name: \"Bob\", email: \"bob@example.com\") { id name } }"}'


Next Steps
Add authentication to GraphQL

Implement Redis for real subscriptions in production

Add query complexity limits

Implement persisted queries for production

Add custom scalar types

Deploy to production