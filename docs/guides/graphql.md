# GraphQL

## Overview

Flaxon includes an optional GraphQL implementation for building modern APIs.

It supports:

- Queries
- Mutations
- Subscriptions
- Async resolvers
- Schema validation
- Introspection
- GraphiQL
- Altair
- Query complexity analysis
- Query depth limiting
- Persisted queries
- Subscription backends

Flaxon's GraphQL implementation is designed to integrate naturally with existing Flaxon applications while remaining flexible enough for production workloads.

---

# Features

- Async-first execution
- GraphQL queries
- GraphQL mutations
- GraphQL subscriptions
- Context support
- Built-in GraphiQL
- Built-in Altair
- Schema validation
- Middleware support
- Extension system
- Redis subscription backend
- In-memory subscription backend
- Query complexity analysis
- Query depth limiting
- Persisted queries

---

# Installation

GraphQL support is included with Flaxon.

Install Flaxon:

```bash
pip install flaxon
```

---

# Quick Start

## 1. Import GraphQL

```python
from flaxon import Flaxon

from flaxon.graphql import (
    GraphQLSchema,
    ObjectType,
    Field,
    String,
    Int,
    List
)
```

---

## 2. Create Your Application

```python
app = Flaxon(
    "graphql-demo"
)
```

---

## 3. Define a Schema

Create your root query object.

```python
class Query(ObjectType):

    hello = Field(
        String,
        name=String(required=False)
    )


    @staticmethod
    def resolve_hello(
        parent,
        args,
        context,
        info
    ) -> str:

        name = args.get(
            "name",
            "World"
        )

        return f"Hello, {name}!"
```

---

## 4. Create the GraphQL Schema

```python
schema = GraphQLSchema(
    query=Query
)
```

---

## 5. Enable GraphQL

Enable GraphQL using the schema.

```python
app.enable_graphql(
    schema
)
```

> **Important**
>
> `enable_graphql()` expects a `GraphQLSchema` instance.
>
> **Correct**
>
> ```python
> app.enable_graphql(schema)
> ```
>
> **Incorrect**
>
> ```python
> app.enable_graphql(Query)
> ```

---

## 6. Run the Application

```bash
flaxon run app:app --reload
```

Open:

```
http://localhost:8000/graphql
```

---

# Your First Query

```graphql
query {

    hello(
        name: "Flaxon"
    )

}
```

Response:

```json
{
    "data": {
        "hello": "Hello, Flaxon!"
    }
}
```

---

# Understanding Resolvers

Resolvers return data for GraphQL fields.

Every resolver receives four parameters.

| Parameter | Description |
|------------|-------------|
| `parent` | Parent object |
| `args` | GraphQL field arguments |
| `context` | Request context |
| `info` | GraphQL field metadata |

---

# Resolver Signature

```python
def resolver(
    parent,
    args,
    context,
    info
):

    return data
```

---

# Synchronous Resolver

```python
class Query(ObjectType):

    hello = Field(
        String
    )


    @staticmethod
    def resolve_hello(
        parent,
        args,
        context,
        info
    ):

        return "Hello World"
```

---

# Asynchronous Resolver

Async resolvers are recommended whenever I/O is involved.

```python
class Query(ObjectType):

    user = Field(
        UserType,
        id=Int(required=True)
    )


    @staticmethod
    async def resolve_user(
        parent,
        args,
        context,
        info
    ):

        user = await db.fetch_user(
            args["id"]
        )

        return user
```

---

# Using Context

Context allows resolvers to access information about the current request.

```python
class Query(ObjectType):

    me = Field(
        UserType
    )


    @staticmethod
    async def resolve_me(
        parent,
        args,
        context,
        info
    ):

        request = context.get(
            "request"
        )

        user_id = request.session.get(
            "user_id"
        )

        return await db.fetch_user(
            user_id
        )
```

---

# Field Arguments

Fields can accept arguments.

```python
class Query(ObjectType):

    greeting = Field(
        String,
        name=String(required=True)
    )


    @staticmethod
    def resolve_greeting(
        parent,
        args,
        context,
        info
    ):

        return (
            f"Hello {args['name']}"
        )
```

Query:

```graphql
query {

    greeting(
        name: "Alice"
    )

}
```

Response:

```json
{
    "data": {
        "greeting": "Hello Alice"
    }
}
```

---

# Returning Objects

Resolvers can return dictionaries or model objects.

```python
class Query(ObjectType):

    user = Field(
        UserType
    )


    @staticmethod
    async def resolve_user(
        parent,
        args,
        context,
        info
    ):

        return {

            "id": 1,

            "name": "Alice",

            "email": "alice@example.com"

        }
```

---

# Accessing Headers

The request is available through the context.

```python
class Query(ObjectType):

    headers = Field(
        String
    )


    @staticmethod
    def resolve_headers(
        parent,
        args,
        context,
        info
    ):

        request = context["request"]

        return request.headers.get(
            "User-Agent"
        )
```

---

# Accessing Authentication

Authentication information is also available.

```python
class Query(ObjectType):

    current_user = Field(
        UserType
    )


    @staticmethod
    async def resolve_current_user(
        parent,
        args,
        context,
        info
    ):

        request = context["request"]

        return getattr(
            request,
            "user",
            None
        )
```

---

# Best Practices for Resolvers

For better performance and maintainability:

- Prefer asynchronous resolvers for database and network operations.
- Keep resolver logic focused on a single responsibility.
- Avoid unnecessary database queries.
- Validate field arguments before using them.
- Use DataLoader or batching techniques to reduce N+1 query problems when applicable.
- Return structured errors instead of exposing internal exceptions.


---

# Mutations

Mutations modify data in your application.

They are defined similarly to queries but are attached to the `mutation` root type.

---

## Creating a Mutation

```python
from flaxon.graphql import (
    ObjectType,
    Field,
    String
)


class Mutation(ObjectType):

    create_user = Field(
        UserType,
        name=String(required=True),
        email=String(required=True)
    )


    @staticmethod
    async def resolve_create_user(
        parent,
        args,
        context,
        info
    ):

        user = await db.create_user(
            args["name"],
            args["email"]
        )

        return user
```

---

## Register the Mutation

```python
schema = GraphQLSchema(

    query=Query,

    mutation=Mutation

)
```

---

## Execute a Mutation

```graphql
mutation {

  createUser(

    name: "Alice",

    email: "alice@example.com"

  ) {

    id

    name

    email

  }

}
```

Example response:

```json
{
    "data": {
        "createUser": {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com"
        }
    }
}
```

---

# Using Mutation Decorators

Flaxon also supports decorators.

```python
from flaxon.graphql import graphql_mutation


@graphql_mutation("createUser")
async def create_user(
    args,
    context
):

    user = await db.create_user(
        args["name"],
        args["email"]
    )

    return {

        "id": user.id,

        "name": user.name

    }
```

---

# Subscriptions

Subscriptions allow clients to receive real-time updates.

They use WebSockets underneath and are useful for:

- Chat applications
- Live dashboards
- Notifications
- Stock prices
- Multiplayer games
- Monitoring systems

---

# Creating a Subscription

```python
class Subscription(ObjectType):

    message = Field(

        MessageType,

        channel=String(required=True)

    )


    @staticmethod
    async def resolve_message(

        parent,

        args,

        context,

        info

    ):

        channel = args["channel"]


        async for message in message_bus.subscribe(
            channel
        ):

            yield message
```

---

## Register the Subscription

```python
schema = GraphQLSchema(

    query=Query,

    mutation=Mutation,

    subscription=Subscription

)
```

---

# Subscription Backends

Flaxon supports multiple subscription backends.

---

## Memory Backend

Recommended for development.

```python
from flaxon.graphql import (
    MemorySubscriptionBackend
)


backend = MemorySubscriptionBackend()


app.enable_graphql(

    schema,

    subscription_backend=backend

)
```

---

## Redis Backend

Recommended for production deployments.

```python
from flaxon.graphql import (
    RedisSubscriptionBackend
)


backend = RedisSubscriptionBackend(

    redis_url="redis://localhost:6379/0",

    prefix="graphql:subscriptions"

)


app.enable_graphql(

    schema,

    subscription_backend=backend

)
```

Redis allows subscriptions to work across multiple application processes and servers.

---

# Publishing Events

Applications can publish events that are sent to subscribed clients.

```python
@app.post("/webhook")
async def webhook(request):

    data = await request.json()

    await app.state.subscription_manager.publish(

        "message",

        data

    )

    return {

        "status": "published"

    }
```

---

# GraphQL Types

Types define the structure of your API.

---

## Object Types

```python
from flaxon.graphql import (

    ObjectType,

    Field,

    String,

    Int,

    List

)


class UserType(ObjectType):

    id = Field(Int)

    name = Field(String)

    email = Field(String)

    posts = Field(List("Post"))



class PostType(ObjectType):

    id = Field(Int)

    title = Field(String)

    content = Field(String)

    author = Field("User")


    @staticmethod
    async def resolve_author(

        parent,

        args,

        context,

        info

    ):

        return await db.fetch_user(

            parent["author_id"]

        )
```

---

# Scalar Types

Flaxon includes several built-in scalar types.

| Type | Description |
|------|-------------|
| String | UTF-8 text |
| Int | 32-bit integer |
| Float | Floating-point number |
| Boolean | True or False |
| ID | Unique identifier |
| DateTime | ISO 8601 timestamp |
| Decimal | Decimal number |
| JSON | JSON object |
| UUID | UUID value |
| URL | URL string |
| Email | Email address |

---

# Custom Scalars

Custom scalars allow you to define your own data types.

```python
from datetime import datetime

from flaxon.graphql import Scalar


class Date(Scalar):

    def __init__(self):

        super().__init__(
            "Date",
            "Date scalar"
        )


    def serialize(
        self,
        value
    ):

        if hasattr(
            value,
            "isoformat"
        ):
            return value.isoformat()

        return str(value)


    def parse_value(
        self,
        value
    ):

        return datetime.fromisoformat(
            value
        )
```

Using the scalar:

```python
class UserType(ObjectType):

    created_at = Field(Date)
```

---

# Lists

Lists represent collections.

```python
class Query(ObjectType):

    users = Field(
        List(UserType)
    )
```

---

# Non-Null Types

Fields can be marked as required.

```python
from flaxon.graphql import NonNull


class Query(ObjectType):

    name = Field(

        NonNull(String)

    )
```

---

# Combining Lists and Non-Null

```python
class Query(ObjectType):

    tags = Field(

        List(

            NonNull(String)

        )

    )
```

Required list:

```python
class Query(ObjectType):

    users = Field(

        NonNull(

            List(UserType)

        )

    )
```

---

# Query Variables

Variables make queries reusable.

Example query:

```graphql
query GetUser($id: Int!) {

    user(id: $id) {

        id

        name

        email

    }

}
```

Variables:

```json
{
    "id": 1
}
```

Executing manually:

```python
variables = {

    "id": 1

}


result = await schema.execute(

    query,

    variables=variables

)
```

---

# Organizing Large Schemas

For larger projects, organize your schema into multiple files.

Example structure:

```text
graphql/

├── schema.py
├── query.py
├── mutation.py
├── subscription.py
├── types/
│   ├── user.py
│   ├── post.py
│   └── comment.py
├── scalars/
│   ├── datetime.py
│   └── uuid.py
└── resolvers/
    ├── users.py
    ├── posts.py
    └── auth.py
```

This structure keeps GraphQL code modular and easier to maintain as your application grows.
---

# Developer Tools

Flaxon includes built-in developer tools for exploring and testing your GraphQL API.

---

# GraphQL Endpoint

Once GraphQL is enabled, the default endpoint is:

```
http://localhost:8000/graphql
```

---

# GraphiQL

GraphiQL is an interactive IDE for executing GraphQL queries.

Open:

```
http://localhost:8000/graphql/graphiql
```

Features include:

- Interactive query editor
- Schema explorer
- Documentation browser
- Auto-completion
- Syntax highlighting
- Query history

---

# Altair

Altair is an advanced GraphQL client included with Flaxon.

Open:

```
http://localhost:8000/graphql/altair
```

Features include:

- Tabs
- Environment variables
- Headers editor
- Query collections
- Variables editor
- Response explorer

---

# Playground URLs

| URL | Purpose |
|------|---------|
| `/graphql` | GraphQL endpoint |
| `/graphql/graphiql` | GraphiQL IDE |
| `/graphql/altair` | Altair IDE |

---

# Extensions

Extensions allow additional functionality without modifying your schema.

---

# Query Complexity Analysis

Complexity analysis helps prevent expensive GraphQL queries.

```python
from flaxon.graphql.extensions import (
    ComplexityExtension
)

app.enable_graphql(

    schema,

    extensions=[
        ComplexityExtension(
            max_complexity=100
        )
    ]

)
```

Assign custom costs:

```python
ext = ComplexityExtension(
    max_complexity=100
)

ext.set_costs({

    "users": 5,

    "posts": 10,

    "comments": 2

})

app.enable_graphql(
    schema,
    extensions=[ext]
)
```

---

# Depth Limiting

Prevent excessively nested queries.

```python
from flaxon.graphql.extensions import (
    DepthLimitExtension
)

app.enable_graphql(

    schema,

    extensions=[
        DepthLimitExtension(
            max_depth=5
        )
    ]

)
```

---

# Persisted Queries

Persisted queries improve security and performance.

```python
from flaxon.graphql.extensions import (
    PersistedQueriesExtension
)

queries = {

    "abc123":
        "query { hello }",

    "def456":
        """
        query {
            user(id: 1) {
                name
            }
        }
        """

}

ext = PersistedQueriesExtension(
    storage=queries
)

app.enable_graphql(

    schema,

    extensions=[ext]

)
```

Loading from a file:

```python
ext.load_persisted_queries(
    "persisted_queries.json"
)
```

---

# Middleware

Middleware executes before and after GraphQL operations.

```python
from flaxon.graphql import (
    GraphQLMiddleware
)

class LoggingMiddleware:

    async def before(
        self,
        context
    ):

        print(
            context.get("query")
        )


    async def after(
        self,
        context,
        result
    ):

        print(
            result.get("data")
        )


middleware = GraphQLMiddleware(app)

middleware.add(
    LoggingMiddleware()
)
```

---

# Error Handling

Errors follow the GraphQL specification.

Example response:

```json
{
    "errors": [
        {
            "message": "Field 'unknown' not found",
            "locations": [
                {
                    "line": 2,
                    "column": 3
                }
            ]
        }
    ]
}
```

---

# Custom GraphQL Errors

Create reusable exceptions.

```python
from flaxon.graphql import (
    GraphQLError
)


class NotFoundError(GraphQLError):

    def __init__(
        self,
        resource,
        resource_id
    ):

        super().__init__(
            f"{resource} {resource_id} not found."
        )

        self.extensions = {

            "code": "NOT_FOUND"

        }
```

Using the error:

```python
async def resolve_user(

    parent,

    args,

    context,

    info

):

    user = await db.fetch_user(
        args["id"]
    )

    if user is None:

        raise NotFoundError(
            "User",
            args["id"]
        )

    return user
```

Example response:

```json
{
    "errors": [
        {
            "message": "User 10 not found.",
            "extensions": {
                "code": "NOT_FOUND"
            }
        }
    ]
}
```

---

# Security

For production deployments:

- Require authentication for protected fields.
- Use authorization checks in resolvers.
- Disable introspection if not required.
- Enable persisted queries.
- Limit query complexity.
- Limit query depth.
- Validate all user input.
- Apply rate limiting.
- Use HTTPS.
- Monitor GraphQL traffic.

---

# Performance Tips

For the best performance:

- Prefer asynchronous resolvers.
- Avoid blocking operations.
- Batch database queries.
- Cache frequently requested data.
- Reuse database connections.
- Use Redis for subscriptions.
- Avoid unnecessary nested queries.
- Return only requested fields.

---

# Best Practices

Recommended practices for production applications:

- Keep schemas organized into multiple files.
- Keep resolvers focused on one responsibility.
- Use descriptive type names.
- Use custom scalars when appropriate.
- Avoid business logic inside resolvers.
- Validate all inputs.
- Return structured errors.
- Use pagination for large collections.
- Use DataLoader or batching techniques where appropriate.
- Protect sensitive fields with authorization.

---

# Recommended Project Structure

```text
graphql/

├── schema.py
├── query.py
├── mutation.py
├── subscription.py
├── middleware.py
├── extensions.py
├── loaders.py
├── scalars/
│   ├── datetime.py
│   ├── decimal.py
│   └── uuid.py
├── types/
│   ├── user.py
│   ├── post.py
│   ├── comment.py
│   └── auth.py
├── resolvers/
│   ├── users.py
│   ├── posts.py
│   ├── comments.py
│   └── auth.py
└── subscriptions/
    └── messages.py
```

---

# Debugging

When running in debug mode, GraphQL requests can also be inspected using Flaxon's built-in debugger.

Open:

```
http://localhost:8000/__debug__
```

The debugger records:

- GraphQL execution errors
- Resolver exceptions
- Validation failures
- Request information
- Stack traces
- Execution time
- Error history

Sensitive information such as passwords, tokens, secrets, and API keys is automatically redacted.

---

# API Reference

See the GraphQL API Reference for complete documentation of:

- GraphQLSchema
- ObjectType
- Field
- Scalar
- List
- NonNull
- GraphQLMiddleware
- GraphQLError
- ComplexityExtension
- DepthLimitExtension
- PersistedQueriesExtension
- Subscription backends

---

# Examples

Additional example applications are available in the Flaxon repository:

- Basic GraphQL API
- Authentication
- PostgreSQL
- MongoDB
- Redis Subscriptions
- Real-time Chat
- CRUD API
- Blog API

---

# Next Steps

Continue with:

- Authentication
- Databases
- Security
- Performance
- Debugging
- Deployment
- Architecture
