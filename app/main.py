from __future__ import annotations

import json
import uuid

from dotenv import load_dotenv

from app.graph import build_app, resume_command


def _print_json(label: str, payload) -> None:
    print(f"\n{label}:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def run_cli() -> None:
    load_dotenv()
    app = build_app()
    thread_id = str(uuid.uuid4())
    print("Ecom Founder OS (dry-run). Type your request.")
    user_input = input("> ").strip()

    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = app.invoke({"user_input": user_input}, config=config)
    except Exception as exc:
        if exc.__class__.__name__ in {"GraphInterrupt", "Interrupt"}:
            payload = getattr(exc, "value", None) or getattr(exc, "payload", None) or exc.args[0]
            _print_json("Approval Required", payload)
            approval = input("Approve? (yes/no): ").strip()
            result = app.invoke(resume_command(approval), config=config)
        else:
            raise

    if isinstance(result, dict) and "__interrupt__" in result:
        payload = result["__interrupt__"]
        _print_json("Approval Required", payload)
        approval = input("Approve? (yes/no): ").strip()
        result = app.invoke(resume_command(approval), config=config)

    if isinstance(result, dict):
        wrapup = result.get("wrapup_json") or result.get("wrapup")
        if wrapup:
            print("\nWrapup Summary:")
            print(wrapup)
        else:
            _print_json("Final State", result)


if __name__ == "__main__":
    run_cli()
