# GraphQL API Example

This example demonstrates a complete Flaxon GraphQL API with:

- Queries
- Mutations
- Subscriptions
- GraphQL types
- Real-time events
- GraphiQL playground


## Running the Example

Create a new Flaxon project:

```bash
flaxon new graphql-example

cd graphql-example
```

Install dependencies:

```bash
pip install flaxon[graphql]
```

Create `app.py` with the code below.

Run:

```bash
flaxon run app:app --reload
```

---

# Application Code

## app.py

```python
from flaxon import Flaxon
from flaxon.graphql import (
    GraphQLSchema,
    ObjectType,
    Field,
    String,
    Int,
    List,
    MemorySubscriptionBackend,
    SubscriptionManager,
)

app = Flaxon(
    "graphql-example",
    debug=True
)


# --------------------
# Data Storage
# --------------------

users = []
posts = []

user_id_counter = 1
post_id_counter = 1


# --------------------
# GraphQL Types
# --------------------

class UserType(ObjectType):

    name = "User"

    id = Field(Int)
    name = Field(String)
    email = Field(String)
    posts = Field(List("Post"))


    @staticmethod
    def resolve_posts(parent, args, context, info):

        return [
            post
            for post in posts
            if post["author_id"] == parent["id"]
        ]



class PostType(ObjectType):

    name = "Post"

    id = Field(Int)
    title = Field(String)
    content = Field(String)
    author_id = Field(Int)
    author = Field(UserType)


    @staticmethod
    def resolve_author(parent, args, context, info):

        return next(
            (
                user
                for user in users
                if user["id"] == parent["author_id"]
            ),
            None
        )


# --------------------
# Queries
# --------------------

class Query(ObjectType):

    name = "Query"


    hello = Field(
        String,
        name=String(required=False)
    )

    users = Field(List(UserType))

    posts = Field(List(PostType))


    @staticmethod
    def resolve_hello(parent,args,context,info):

        return (
            f"Hello {args.get('name','World')}!"
        )


    @staticmethod
    def resolve_users(parent,args,context,info):

        return users


    @staticmethod
    def resolve_posts(parent,args,context,info):

        return posts



# --------------------
# Mutations
# --------------------

class Mutation(ObjectType):

    name = "Mutation"


    create_user = Field(
        UserType,
        name=String(required=True),
        email=String(required=True)
    )


    create_post = Field(
        PostType,
        title=String(required=True),
        content=String(required=True),
        author_id=Int(required=True)
    )


    @staticmethod
    async def resolve_create_user(
        parent,
        args,
        context,
        info
    ):

        global user_id_counter


        user = {
            "id": user_id_counter,
            "name": args["name"],
            "email": args["email"]
        }


        user_id_counter += 1

        users.append(user)

        return user



    @staticmethod
    async def resolve_create_post(
        parent,
        args,
        context,
        info
    ):

        global post_id_counter


        post = {

            "id": post_id_counter,
            "title": args["title"],
            "content": args["content"],
            "author_id": args["author_id"]

        }


        post_id_counter += 1

        posts.append(post)


        return post



# --------------------
# Subscriptions
# --------------------

class Subscription(ObjectType):

    name = "Subscription"


    user_created = Field(UserType)

    post_created = Field(PostType)



# --------------------
# GraphQL Setup
# --------------------

schema = GraphQLSchema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)


subscription_backend = (
    MemorySubscriptionBackend()
)


subscription_manager = (
    SubscriptionManager(
        subscription_backend
    )
)


app.enable_graphql(
    schema,
    subscription_backend=
    subscription_backend
)


app.state.subscription_manager = (
    subscription_manager
)



# --------------------
# Seed Data
# --------------------

users.append(
    {
        "id":1,
        "name":"Alice",
        "email":"alice@example.com"
    }
)


posts.extend(
    [
        {
            "id":1,
            "title":"First Post",
            "content":"Hello GraphQL",
            "author_id":1
        }
    ]
)



# --------------------
# Home Route
# --------------------

@app.get("/")
async def home():

    return {

        "message":
        "Welcome to Flaxon GraphQL",

        "endpoint":
        "/graphql",

        "playground":
        "/graphql/graphiql"

    }



```

Run the example with `flaxon run app:app --reload`.

---

# Testing the API

## GraphiQL Playground

Open:

```
http://localhost:8000/graphql/graphiql
```

---

# Queries

## Hello

```graphql
query {

  hello(name:"Flaxon")

}
```

---

## Get Users

```graphql
query {

 users {

   id
   name
   email

 }

}
```

---

## Get Posts

```graphql
query {

 posts {

   id
   title
   content

 }

}
```

---

# Mutations

## Create User

```graphql
mutation {

 createUser(
   name:"Bob",
   email:"bob@example.com"
 ){

   id
   name
   email

 }

}
```

---

## Create Post

```graphql
mutation {

 createPost(
   title:"New Post",
   content:"GraphQL Example",
   author_id:1
 ){

   id
   title

 }

}
```

---

# Subscriptions

## User Created Event

```graphql
subscription {

 userCreated {

   id
   name
   email

 }

}
```

---

## Post Created Event

```graphql
subscription {

 postCreated {

   id
   title
   content

 }

}
```

---

# Using curl

## Query

```bash
curl -X POST http://localhost:8000/graphql \
-H "Content-Type: application/json" \
-d '{"query":"{ hello(name:\"Flaxon\") }"}'
```

---

## Mutation

```bash
curl -X POST http://localhost:8000/graphql \
-H "Content-Type: application/json" \
-d '{"query":"mutation { createUser(name:\"Bob\",email:\"bob@example.com\"){id name} }"}'
```

---

# Production Improvements

Recommended next steps:

- Add GraphQL authentication
- Add database integration
- Add Redis subscription backend
- Add query complexity limits
- Add persisted queries
- Add custom scalar types
- Deploy with production ASGI server
