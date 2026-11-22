# -*- coding: utf-8 -*-
import typing, strawberry
from strawberry.dataloader import DataLoader
from strawberry.types import Info
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter, BaseContext

DB_ORDERS = {i: [{"id": f"o{i}", "amount": 89.9, "item": "Livre Architecture"}] for i in range(1, 101)}
sql_naive_count = 0
sql_batch_count = 0

async def batch_orders(keys: typing.List[int]) -> typing.List[typing.List['Order']]:
    global sql_batch_count
    sql_batch_count += 1
    return [[Order(**o) for o in DB_ORDERS.get(k, [])] for k in keys]

class CustomContext(BaseContext):
    def __init__(self):
        super().__init__()
        self.order_loader = DataLoader(load_fn=batch_orders)

async def get_context() -> CustomContext:
    return CustomContext()

@strawberry.type
class Order:
    id: strawberry.ID
    amount: float
    item: str

@strawberry.type
class User:
    id: strawberry.ID
    name: str
    email: str

    @strawberry.field
    async def orders(self, info: Info[CustomContext, None], use_loader: bool = True) -> typing.List[Order]:
        global sql_naive_count
        if not use_loader:
            sql_naive_count += 1
            return [Order(**o) for o in DB_ORDERS.get(int(self.id), [])]
        return await info.context.order_loader.load(int(self.id))

@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID) -> typing.Optional[User]:
        return User(id=id, name="Alice Martin", email="alice@example.com")

    @strawberry.field
    def users(self, limit: int = 100) -> typing.List[User]:
        global sql_batch_count, sql_naive_count
        sql_batch_count += 1
        sql_naive_count += 1
        return [User(id=strawberry.ID(str(i)), name=f"User {i}", email=f"u{i}@test.com") for i in range(1, limit + 1)]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user_email(self, id: strawberry.ID, email: str) -> User:
        return User(id=id, name="Alice Martin", email=email)

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)

app = FastAPI(title="GraphQL API ENSIIE")
app.include_router(graphql_app, prefix="/graphql")

@app.get("/stats")
def stats():
    return {"sql_naive_count": sql_naive_count, "sql_batch_count": sql_batch_count}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
