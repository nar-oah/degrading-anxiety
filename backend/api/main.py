from datetime import date
from celery import Celery
from celery.result import AsyncResult
from flask import Flask, Response, jsonify
from flask.typing import ResponseReturnValue as ReturnValue
from pydantic import BaseModel, ValidationError
from degrading_anxiety_contracts.schedule import REvent, TaskList
from secrets import token_urlsafe

app = Flask(__name__)
celery_app = Celery(
    "api",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def add_task(name: str, token: str, value: BaseModel | int | date) -> ReturnValue:
    arg = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    result: AsyncResult = celery_app.send_task(
        name,
        args=[token, arg],
        queue="schedule",
    )
    return jsonify(result.id), 202


@app.errorhandler(ValidationError)
def get_validation(error: ValidationError) -> Response:
    return app.response_class(
        error.json(include_url=False),
        status=400,
        mimetype="application/json",
    )


@app.get("/token")
def create_token() -> str:
    return token_urlsafe(32)


@app.post("/add")
def add_event(token: str, event: REvent) -> ReturnValue:
    return add_task("schedule.add", token, event)


@app.post("/delay")
def mod_schedule(token: str, minute: int) -> ReturnValue:
    return add_task("schedule.delay", token, minute)


@app.post("/alloc")
def add_alloc(token: str, tasks: TaskList) -> ReturnValue:
    return add_task("schedule.alloc", token, tasks)


@app.post("/export")
def get_export(token: str, date: date) -> ReturnValue:
    return add_task("schedule.add", token, date)


def main() -> None:
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
