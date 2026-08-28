from __future__ import annotations

from pathlib import Path

from flaxon import Flaxon
from flaxon.graphql import Field, GraphQLSchema, List, ObjectType
from flaxon.jinax import Jinax


app = Flaxon("graphql-github-clone", debug=True)
BASE_DIR = Path(__file__).parent
app.use_templates(Jinax(BASE_DIR / "templates", auto_reload=True, strict_undefined=True))
app.mount_static("/static", BASE_DIR / "static")

users = [
    {"id": 1, "login": "ada", "name": "Ada Lovelace"},
    {"id": 2, "login": "grace", "name": "Grace Hopper"},
]
repositories = [
    {
        "id": 1,
        "name": "flaxon",
        "description": "A small framework for Python web applications.",
        "stars": 42,
        "owner_id": 1,
    },
]


user_type = ObjectType(
    "User",
    {
        "id": Field(int),
        "login": Field(str),
        "name": Field(str),
    },
)
repository_type = ObjectType(
    "Repository",
    {
        "id": Field(int),
        "name": Field(str),
        "description": Field(str),
        "stars": Field(int),
        "owner": Field(
            user_type,
            resolver=lambda repo, args, context, info: next(
                (user for user in users if user["id"] == repo["owner_id"]), None
            ),
        ),
    },
)


def resolve_viewer(parent, args, context, info):
    return users[0]


def resolve_repositories(parent, args, context, info):
    search = (args.get("search") or "").lower()
    return [
        repo
        for repo in repositories
        if not search
        or search in repo["name"].lower()
        or search in repo["description"].lower()
    ]


def resolve_repository(parent, args, context, info):
    return next((repo for repo in repositories if repo["id"] == args["id"]), None)


def resolve_create_repository(parent, args, context, info):
    repository = {
        "id": len(repositories) + 1,
        "name": args["name"],
        "description": args.get("description", ""),
        "stars": 0,
        "owner_id": 1,
    }
    repositories.append(repository)
    return repository


def resolve_star_repository(parent, args, context, info):
    repository = resolve_repository(parent, args, context, info)
    if repository is not None:
        repository["stars"] += 1
    return repository


query = ObjectType(
    "Query",
    {
        "viewer": Field(user_type, resolver=resolve_viewer),
        "repositories": Field(
            List(repository_type),
            args={"search": str},
            resolver=resolve_repositories,
        ),
        "repository": Field(
            repository_type,
            args={"id": int},
            resolver=resolve_repository,
        ),
    },
)
mutation = ObjectType(
    "Mutation",
    {
        "createRepository": Field(
            repository_type,
            args={"name": str, "description": str},
            resolver=resolve_create_repository,
        ),
        "starRepository": Field(
            repository_type,
            args={"id": int},
            resolver=resolve_star_repository,
        ),
    },
)

schema = GraphQLSchema(query=query, mutation=mutation)
app.enable_graphql(schema, url="/graphql", enable_playground=True)


@app.get("/")
async def home(request):
    return await request.render(
        "home.html",
        {
            "title": "Flaxon Forge",
            "graphql_endpoint": "/graphql",
            "graphiql_url": "/graphql/graphiql",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("examples.graphql_github_clone.app:app", host="127.0.0.1", port=8000, reload=True)
