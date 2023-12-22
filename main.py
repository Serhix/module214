import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import contacts, auth, users

from fastapi_limiter import FastAPILimiter

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
    It's a good place to initialize things that are needed by your app,
    such as connecting to databases or initializing caches.

    :return: A dictionary with the following structure
    :doc-author: Trelent
    """
    r = redis.Redis(host='localhost', port=6379, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.get("/")
def read_root():
    """
    The read_root function is a GET request that returns the root of the API.
    It will return a JSON object with one key, 'messege', and its value will be
    a string containing information about this API.

    :return: A dictionary with the key 'message' and value 'contact api'
    :doc-author: Trelent
    """
    return {'messege': 'Contact api'}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
