from fastapi import FastAPI

import api.assistant

app = FastAPI()



app.include_router(api.assistant.router)
