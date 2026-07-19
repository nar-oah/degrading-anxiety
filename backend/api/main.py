from datetime import date
from celery import Celery
from celery.exceptions import TimeoutError as CeleryTimeoutError
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, Response, status
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
EXPORT_TIMEOUT = 30


def add_task(name: str, token: str, value: BaseModel | int | str) -> AsyncResult:
    arg = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return celery_app.send_task(
        name,
        args=[token, arg],
        queue="schedule",
    )


@app.exception_handler(RequestValidationError)
def get_validation(error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(error.errors()),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.get("/token", response_model=str)
def get_token() -> str:
    return token_urlsafe(32)


@app.post("/add", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_event(token: str, event: REvent) -> str | None:
    return add_task("schedule.add", token, event).id


@app.post("/delay", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def mod_schedule(token: str, minute: int) -> str | None:
    return add_task("schedule.delay", token, minute).id


@app.post("/alloc", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_alloc(token: str, tasks: TaskList) -> str | None:
    return add_task("schedule.alloc", token, tasks).id


@app.get("/export", responses={504: {"description": "Export timed out"}})
def get_export(token: str, date: date) -> Response:
    result = add_task("schedule.export", token, date.isoformat())
    try:
        content = result.get(timeout=EXPORT_TIMEOUT)
    except CeleryTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Calendar export timed out",
        ) from error
    result.forget()
    return Response(
        content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="schedule-{date}.ics"',
            "Cache-Control": "no-store",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
