from fastapi.testclient import TestClient

from app.main import app


def test_agent_workflow_runs_evidence_pipeline() -> None:
    sample = (
        "夜色降临时，母亲仍坐在窗前等待远行的孩子。\n"
        "这份等待不是简单的牵挂，而像一盏灯，照着家族记忆中最柔软的角落。\n"
        "孩子归来后，沉默比语言更先抵达，二人都明白岁月已经改变了他们。"
    )

    with TestClient(app) as client:
        upload_response = client.post(
            "/documents/upload",
            files={"file": ("agent-sample.txt", sample.encode("utf-8"), "text/plain")},
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["id"]

        response = client.post(
            "/agent/run",
            json={
                "document_id": document_id,
                "task": "分析等待这一意象如何连接人物情感和家庭记忆",
                "top_k": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["answer"]
    step_types = [step["step_type"] for step in payload["steps"]]
    assert step_types == [
        "plan",
        "retrieve",
        "reader_analysis",
        "critic_analysis",
        "verification",
        "final",
    ]


def test_agent_workflow_reports_insufficient_evidence() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/agent/run",
            json={
                "document_id": "missing-document",
                "task": "分析这部作品的核心主题",
                "top_k": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert "证据不足" in payload["answer"]
    step_types = [step["step_type"] for step in payload["steps"]]
    assert "verification" in step_types
    verifier_step = next(step for step in payload["steps"] if step["step_type"] == "verification")
    assert "证据不足" in verifier_step["output_text"]



def test_agent_workflow_fast_mode_runs_short_pipeline() -> None:
    sample = (
        "床前明月光\n"
        "疑是地上霜\n"
        "举头望明月\n"
        "低头思故乡"
    )

    with TestClient(app) as client:
        upload_response = client.post(
            "/documents/upload",
            files={"file": ("fast-agent-poem.txt", sample.encode("utf-8"), "text/plain")},
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["id"]

        response = client.post(
            "/agent/run",
            json={
                "document_id": document_id,
                "task": "这首诗如何表达思乡？",
                "top_k": 3,
                "mode": "fast",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["mode"] == "fast"
    step_types = [step["step_type"] for step in payload["steps"]]
    assert step_types == ["retrieve", "fast_answer"]
