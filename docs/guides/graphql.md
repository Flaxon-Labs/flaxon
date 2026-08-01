
---

### `docs/guides/graphql.md`

```markdown
# GraphQL

Flaxon includes a built-in GraphQL implementation with support for queries, mutations, subscriptions, and real-time data streaming.

## Overview

Flaxon's GraphQL implementation provides:

- Full GraphQL specification support
- Queries, Mutations, and Subscriptions
- Async resolver support
- Schema validation
- Introspection
- Playgrounds (GraphiQL and Altair)
- Subscription support with Redis or in-memory backends
- Query complexity analysis
- Persisted queries
- Depth limiting

## Quick Start

### 1. Define a Schema

```python
from flaxon import Flaxon
from flaxon.graphql import GraphQLSchema, ObjectType, Field, String, Int, List
from flaxon.graphql import graphql_query

app = Flaxon("my-app")

# Define a GraphQL Object Type
class Query(ObjectType):
    """Root Query type."""
    hello = Field(String, name=String(required=False))

    @staticmethod
    def resolve_hello(parent, args, context, info) -> str:
        name = args.get("name", "World")
        return f"Hello, {name}!"

# Create schema
schema = GraphQLSchema(query=Query)


2. Enable GraphQL
python
# IMPORTANT: enable_graphql() takes a GraphQLSchema, NOT a bare ObjectType
app.enable_graphql(schema)  # ✅ Correct

# ❌ Wrong - this will fail
# app.enable_graphql(Query)
3. Use the GraphQL Endpoint
Start your app and visit /graphql:

bash
flaxon run app:app --reload
Try a query:

graphql
query {
  hello(name: "Flaxon")
}
Response:

json
{
  "data": {
    "hello": "Hello, Flaxon!"
  }
}
Resolvers
Resolvers are methods that fetch data for fields. They receive four arguments:

Argument	Type	Description
parent	Any	The parent object being resolved
args	dict	Field arguments
context	Any	Request context (request, scope, etc.)
info	Any	Field information (name, parent type, etc.)
Resolver Signature
python
def resolver(parent, args, context, info):
    # parent: The parent object
    # args: Field arguments
    # context: Request context
    # info: Field metadata
    return data
Async Resolvers
python
class Query(ObjectType):
    user = Field(UserType, id=Int(required=True))

    @staticmethod
    async def resolve_user(parent, args, context, info):
        # Async database fetch
        user = await db.fetch_user(args["id"])
        return user
Using Context
python
class Query(ObjectType):
    me = Field(UserType)

    @staticmethod
    async def resolve_me(parent, args, context, info):
        # Access request from context
        request = context.get("request")
        user_id = request.session.get("user_id")
        return await db.fetch_user(user_id)
Mutations
Mutations are defined the same way as queries but use the mutation field.

python
from flaxon.graphql import graphql_mutation

class Mutation(ObjectType):
    create_user = Field(UserType, name=String(required=True), email=String(required=True))

    @staticmethod
    async def resolve_create_user(parent, args, context, info):
        user = await db.create_user(args["name"], args["email"])
        return user

# Add mutation to schema
schema = GraphQLSchema(query=Query, mutation=Mutation)
Using Decorators
python
@graphql_mutation("createUser")
async def create_user(args, context) -> dict:
    user = await db.create_user(args["name"], args["email"])
    return {"id": user.id, "name": user.name}
Subscriptions
Subscriptions enable real-time data streaming.

Defining a Subscription
python
from flaxon.graphql import SubscriptionManager, MemorySubscriptionBackend

class Subscription(ObjectType):
    message = Field(MessageType, channel=String(required=True))

    @staticmethod
    async def resolve_message(parent, args, context, info):
        # This is the subscription source
        # Returns an async generator or subscribes to a channel
        channel = args["channel"]
        async for message in message_bus.subscribe(channel):
            yield message

# Add subscription to schema
schema = GraphQLSchema(query=Query, mutation=Mutation, subscription=Subscription)
Subscription Backends
Memory Backend (Development)
python
from flaxon.graphql import MemorySubscriptionBackend

schema = GraphQLSchema(query=Query, subscription=Subscription)
app.enable_graphql(schema, subscription_backend=MemorySubscriptionBackend())
Redis Backend (Production)
python
from flaxon.graphql import RedisSubscriptionBackend

# Redis backend for multi-process/multi-server deployments
backend = RedisSubscriptionBackend(
    redis_url="redis://localhost:6379/0",
    prefix="graphql:subscription"
)

app.enable_graphql(schema, subscription_backend=backend)
Publishing Events
python
@app.post("/webhook")
async def webhook(request):
    data = await request.json()
    # Publish to all subscribers
    await app.state.subscription_manager.publish("message", data)
    return {"status": "published"}
GraphQL Types
Object Types
python
from flaxon.graphql import ObjectType, Field, String, Int, List

class UserType(ObjectType):
    name = "User"
    id = Field(Int)
    name = Field(String)
    email = Field(String)
    posts = Field(List("Post"))

class PostType(ObjectType):
    name = "Post"
    id = Field(Int)
    title = Field(String)
    content = Field(String)
    author = Field("User")

    @staticmethod
    def resolve_author(parent, args, context, info):
        return db.fetch_user(parent["author_id"])
Scalar Types
Scalar	Description
String	UTF-8 string
Int	32-bit integer
Float	Double-precision float
Boolean	True/False
ID	Unique identifier
DateTime	ISO 8601 datetime
Decimal	Decimal number
JSON	JSON object
UUID	UUID string
URL	URL string
Email	Email address string

Custom Scalars
python
from flaxon.graphql import Scalar

class Date(Scalar):
    def __init__(self):
        super().__init__("Date", "Date scalar")

    def serialize(self, value):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def parse_value(self, value):
        return datetime.fromisoformat(value) if isinstance(value, str) else value

# Use in types
class UserType(ObjectType):
    created_at = Field(Date)
Lists and Non-Null
python
from flaxon.graphql import List, NonNull

class Query(ObjectType):
    # Non-null string (required)
    name = Field(NonNull(String))

    # List of non-null strings
    tags = Field(List(NonNull(String)))

    # Non-null list of strings (list itself is required)
    items = Field(NonNull(List(String)))
Queries with Variables
graphql
query GetUser($id: Int!) {
  user(id: $id) {
    name
    email
  }
}
python
# Variables
variables = {"id": 1}
result = await schema.execute(query, variables=variables)
Playgrounds
Flaxon includes two GraphQL playgrounds:

GraphiQL
Visit /graphql/graphiql for the GraphiQL IDE.

html
<!-- Built-in GraphiQL interface -->
Altair
Visit /graphql/altair for the Altair GraphQL client.

html
<!-- Built-in Altair interface -->
Playground Index
Visit /graphql for the playground selection screen.

Extensions
Complexity Analysis
Limit query complexity to prevent expensive operations:

python
from flaxon.graphql.extensions import ComplexityExtension

app.enable_graphql(schema, extensions=[
    ComplexityExtension(max_complexity=100)
])
Set custom field costs:

python
ext = ComplexityExtension(max_complexity=100)
ext.set_costs({
    "users": 5,    # Users field costs 5 points
    "posts": 10,   # Posts field costs 10 points
})
app.enable_graphql(schema, extensions=[ext])
Depth Limiting
Limit query depth to prevent deeply nested queries:

python
from flaxon.graphql.extensions import DepthLimitExtension

app.enable_graphql(schema, extensions=[
    DepthLimitExtension(max_depth=5)
])
Persisted Queries
Pre-register queries for security and performance:

python
from flaxon.graphql.extensions import PersistedQueriesExtension

# Pre-register queries
queries = {
    "abc123": "query { hello }",
    "def456": "query { user(id: 1) { name } }",
}

ext = PersistedQueriesExtension(storage=queries)
app.enable_graphql(schema, extensions=[ext])

# Or load from file
ext.load_persisted_queries("persisted_queries.json")
Middleware
Add custom middleware to GraphQL requests:

python
from flaxon.graphql import GraphQLMiddleware

class LoggingMiddleware:
    async def before(self, context):
        print(f"Executing query: {context.get('query')}")

    async def after(self, context, result):
        print(f"Query completed: {result.get('data')}")

middleware = GraphQLMiddleware(app)
middleware.add(LoggingMiddleware())
Error Handling
GraphQL errors are returned in the response:

json
{
  "errors": [
    {
      "message": "Field 'unknown' not found",
      "locations": [{"line": 2, "column": 3}]
    }
  ]
}

Custom Error Types
python
from flaxon.graphql import GraphQLError

class NotFoundError(GraphQLError):
    def __init__(self, resource: str, id: int):
        super().__init__(f"Resource {resource} with id {id} not found")
        self.extensions = {"code": "NOT_FOUND"}

# Use in resolvers
async def resolve_user(parent, args, context, info):
    user = await db.fetch_user(args["id"])
    if not user:
        raise NotFoundError("User", args["id"])
    return user

API Reference
See the GraphQL API Reference for detailed class and method documentation.

Examples
See the GraphQL API Example for a complete working application.