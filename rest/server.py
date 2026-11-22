# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Response, Header
import json

app = FastAPI(title="API REST Utilisateurs ENSIIE")
DB = {42: {"id": 42, "name": "Alice Martin", "email": "alice@example.com", "v": 1}}

def get_etag(user: dict) -> str:
    return f'W/"user-{user["id"]}-v{user["v"]}"'

@app.post("/users", status_code=201)
def create_user(u: dict, response: Response):
    new_id = max(DB.keys()) + 1
    DB[new_id] = {**u, "id": new_id, "v": 1}
    response.headers["Location"] = f"/users/{new_id}"
    return {k: v for k, v in DB[new_id].items() if k != "v"}

@app.get("/users/{user_id}")
def get_user(user_id: int, if_none_match: str | None = Header(None)):
    if user_id not in DB:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    etag = get_etag(DB[user_id])
    if if_none_match == etag:
        return Response(status_code=304)
    body = json.dumps({k: v for k, v in DB[user_id].items() if k != "v"}, separators=(',', ':'))
    return Response(
        content=body,
        media_type="application/json",
        headers={"ETag": etag, "Cache-Control": "public, max-age=0, must-revalidate"}
    )

@app.put("/users/{user_id}")
def update_user(user_id: int, u: dict):
    if user_id not in DB:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    DB[user_id] = {**u, "id": user_id, "v": DB[user_id]["v"] + 1}
    return Response(status_code=204)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
