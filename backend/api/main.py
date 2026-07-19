from celery import Celery
from celery.result import AsyncResult
from flask import Flask, Response, jsonify, request
from pydantic import BaseModel, ValidationError
from degrading_anxiety_contracts.schedule import REvent, TaskList

app = Flask(__name__)
celery_app = Celery(
    "api",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
)


def get_token() -> str:
    return request.headers["Authorization"].removeprefix("Bearer ")


def add_task(name: str, value: BaseModel) -> tuple[Response, int]:
    result: AsyncResult = celery_app.send_task(
        name,
        args=[get_token(), value.model_dump(mode="json")],
        queue="schedule",
    )
    return jsonify({"task_id": result.id}), 202


@app.errorhandler(ValidationError)
def get_validation(error: ValidationError) -> Response:
    return app.response_class(
        error.json(include_url=False),
        status=400,
        mimetype="application/json",
    )


@app.post("/schedule/add")
def add_event() -> tuple[Response, int]:
    return add_task("schedule.add", REvent.model_validate(request.get_json()))


@app.post("/schedule/alloc")
def add_alloc() -> tuple[Response, int]:
    return add_task("schedule.alloc", TaskList.model_validate(request.get_json()))


def main() -> None:
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
