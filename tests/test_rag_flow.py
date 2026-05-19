from fastapi.testclient import TestClient

from app.main import app


def test_upload_document_and_rag_query() -> None:
    sample = (
        "夜色降临时，母亲仍坐在窗前等待远行的孩子。\n"
        "这份等待不是简单的牵挂，而像一盏灯，照着家族记忆中最柔软的角落。\n"
        "孩子归来后，沉默比语言更先抵达，二人都明白岁月已经改变了他们。"
    )

    with TestClient(app) as client:
        upload_response = client.post(
            "/documents/upload",
            files={"file": ("sample.txt", sample.encode("utf-8"), "text/plain")},
        )
        assert upload_response.status_code == 200
        document = upload_response.json()
        assert document["status"] == "completed"
        assert document["chunk_count"] >= 1

        rag_response = client.post(
            "/rag/query",
            json={
                "document_id": document["id"],
                "query": "这段文字中的等待象征什么？",
            },
        )
        assert rag_response.status_code == 200
        payload = rag_response.json()
        assert payload["answer"]
        assert payload["citations"]
        assert "母亲" in payload["citations"][0]["content"]

        delete_response = client.delete(f"/documents/{document['id']}")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] is True

        list_response = client.get("/documents")
        assert list_response.status_code == 200
        document_ids = {item["id"] for item in list_response.json()["documents"]}
        assert document["id"] not in document_ids

        deleted_rag_response = client.post(
            "/rag/query",
            json={
                "document_id": document["id"],
                "query": "这段文字中的等待象征什么？",
            },
        )
        assert deleted_rag_response.status_code == 200
        assert deleted_rag_response.json()["citations"] == []

