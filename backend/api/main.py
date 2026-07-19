from datetime import date
from celery import Celery
from celery.result import AsyncResult
from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from degrading_anxiety_contracts.schedule import REvent, TaskList
from secrets import token_urlsafe

app = FastAPI(title="Degrading Anxiety API")
celery_app = Celery(
    "api",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def add_task(name: str, token: str, value: BaseModel | int | date) -> str:
    arg = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    result: AsyncResult = celery_app.send_task(
        name,
        args=[token, arg],
        queue="schedule",
    )
    return result.id


@app.exception_handler(RequestValidationError)
def get_validation(request: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(error.errors()),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.get("/token", response_model=str)
def get_token() -> str:
    return token_urlsafe(32)


@app.post("/add", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_event(token: str, event: REvent) -> str:
    return add_task("schedule.add", token, event)


@app.post("/delay", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def mod_schedule(token: str, minute: int) -> str:
    return add_task("schedule.delay", token, minute)


@app.post("/alloc", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_alloc(token: str, tasks: TaskList) -> str:
    return add_task("schedule.alloc", token, tasks)


@app.post("/export", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_export(token: str, date: date) -> str:
    return add_task("schedule.export", token, date)


@app.get("/export/{id}", responses={202: {"description": "Export pending"}})
def get_export(id: str) -> Response:
    result = AsyncResult(id, app=celery_app)
    return (
        Response(result.get(), media_type="text/calendar")
        if result.ready()
        else Response(status_code=status.HTTP_202_ACCEPTED)
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
