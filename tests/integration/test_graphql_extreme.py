from __future__ import annotations

from flaxon import Flaxon
from flaxon.graphql import Field, GraphQLSchema, List, ObjectType
from flaxon.testing import TestClient


def _graphql_app() -> tuple[Flaxon, GraphQLSchema, TestClient]:
    app = Flaxon("graphql-extreme", debug=True)
    users = [
        {"id": 1, "name": "Ada", "posts": [{"id": 10, "title": "Compilers"}]},
        {"id": 2, "name": "Grace", "posts": []},
    ]

    post_type = ObjectType(
        "Post",
        {
            "id": Field(int),
            "title": Field(str),
        },
    )
    user_type = ObjectType(
        "User",
        {
            "id": Field(int),
            "name": Field(str),
            "posts": Field(List(post_type)),
        },
    )

    def resolve_hello(parent, args, context, info):
        return f"Hello {args.get('name', 'World')}"

    def resolve_users(parent, args, context, info):
        return users

    def resolve_user(parent, args, context, info):
        return next((user for user in users if user["id"] == args["id"]), None)

    def resolve_create_user(parent, args, context, info):
        user = {"id": len(users) + 1, "name": args["name"], "posts": []}
        users.append(user)
        return user

    query = ObjectType(
        "Query",
        {
            "hello": Field(str, args={"name": str}, resolver=resolve_hello),
            "users": Field(List(user_type), resolver=resolve_users),
            "user": Field(user_type, args={"id": int}, resolver=resolve_user),
        },
    )
    mutation = ObjectType(
        "Mutation",
        {
            "createUser": Field(
                user_type,
                args={"name": str},
                resolver=resolve_create_user,
            ),
        },
    )
    schema = GraphQLSchema(query=query, mutation=mutation)
    app.enable_graphql(schema)
    return app, schema, TestClient(app)


def test_graphql_http_queries_nested_data_and_variables():
    _, _, client = _graphql_app()

    response = client.post(
        "/graphql",
        json_data={
            "query": "query Greeting($name: String) { hello(name: $name) }",
            "variables": {"name": "Flaxon"},
        },
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"hello": "Hello Flaxon"}}

    nested = client.post(
        "/graphql",
        json_data={"query": "{ users { id name posts { id title } } }"},
    )
    assert nested.status_code == 200
    assert nested.json()["data"]["users"][0] == {
        "id": 1,
        "name": "Ada",
        "posts": [{"id": 10, "title": "Compilers"}],
    }


def test_graphql_mutation_operation_name_and_stateful_result():
    _, _, client = _graphql_app()

    response = client.post(
        "/graphql",
        json_data={
            "query": "mutation Add($name: String) { createUser(name: $name) { id name } }",
            "variables": {"name": "Katherine"},
            "operationName": "Add",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"data": {"createUser": {"id": 3, "name": "Katherine"}}}

    following = client.post(
        "/graphql",
        json_data={"query": "{ user(id: 3) { id name } }"},
    )
    assert following.json() == {"data": {"user": {"id": 3, "name": "Katherine"}}}


def test_graphql_validation_and_request_errors_are_json():
    _, _, client = _graphql_app()

    invalid_query = client.post(
        "/graphql",
        json_data={"query": "{ missingField }"},
    )
    assert invalid_query.status_code == 200
    assert "errors" in invalid_query.json()

    malformed = client.post(
        "/graphql",
        content=b"not-json",
        headers={"content-type": "application/json"},
    )
    assert malformed.status_code == 500
    assert "errors" in malformed.json()


def test_graphql_playgrounds_introspection_and_query_load():
    _, schema, client = _graphql_app()

    playground = client.get("/graphql/graphiql")
    assert playground.status_code == 200
    assert "GraphiQL" in playground.text

    altair = client.get("/graphql/altair")
    assert altair.status_code == 200
    assert "altair.min.js" not in altair.text
    assert "AltairGraphQL.init" in altair.text
    assert "altair-static@5.2.1/build/dist/main.js" in altair.text

    introspection = client.get("/graphql")
    assert introspection.status_code == 200
    assert "GraphQL Playground" in introspection.text
    assert "Query" in (schema.get_types())

    responses = [
        client.post("/graphql", json_data={"query": "{ hello }"})
        for _ in range(200)
    ]
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json() == {"data": {"hello": "Hello World"}} for response in responses)
