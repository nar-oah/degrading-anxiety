from datetime import date
from celery.exceptions import TimeoutError as CeleryTimeoutError
from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from degrading_anxiety_contracts.schedule import REvent, TaskList
from secrets import token_urlsafe
from tasks import add_course_task, add_exam_task, add_task

app = FastAPI(title="Degrading Anxiety API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
EXPORT_TIMEOUT = 30


def get_course_date(value: date) -> date:
    def get_error() -> date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course start date must be a Monday",
        )

    return value if value.weekday() == 0 else get_error()


@app.exception_handler(RequestValidationError)
def get_validation(_: Request, error: RequestValidationError) -> JSONResponse:
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


@app.post("/course", response_model=str, status_code=status.HTTP_202_ACCEPTED)
def add_course(token: str, date: date) -> str | None:
    return add_course_task(token, get_course_date(date)).id


@app.post("/exam", response_model=str, status_code=status.HTTP_202_ACCEPTED)
async def add_exam(token: str, file: UploadFile) -> str | None:
    return add_exam_task(token, await file.read()).id


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
