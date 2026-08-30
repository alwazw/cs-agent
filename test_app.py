import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from main import app, app_state
from knowledge_base import load_knowledge_base, INITIATIVE_MAP
from personality_engine import PERSONAS, get_persona, get_random_persona
from session_manager import get_chat_history, save_turn, reset_session, get_session_state, set_session_state

@pytest.mark.anyio
async def test_session_manager_history():
    customer = "+15550001111"
    await reset_session(customer)

    history_empty = await get_chat_history(customer)
    assert history_empty == []

    await save_turn(customer, "User message 1", "Bot reply 1")
    history = await get_chat_history(customer)
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "User message 1"}
    assert history[1] == {"role": "assistant", "content": "Bot reply 1"}

    await reset_session(customer)

@pytest.mark.anyio
async def test_session_state():
    customer = "+15550002222"
    await reset_session(customer)

    state = await get_session_state(customer)
    assert state == "BOT_ACTIVE"

    await set_session_state(customer, "HUMAN_REQUESTED")
    state_updated = await get_session_state(customer)
    assert state_updated == "HUMAN_REQUESTED"

    await reset_session(customer)

def test_load_knowledge_base(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("# Doc 1\nContent 1")
    (docs_dir / "doc2.md").write_text("# Doc 2\nContent 2")

    result = load_knowledge_base(str(docs_dir))

    assert "--- Document: doc1.md ---" in result
    assert "# Doc 1" in result
    assert "--- Document: doc2.md ---" in result

def test_load_knowledge_base_phone_number_mapping(tmp_path):
    docs_dir = tmp_path / "docs"
    support_dir = docs_dir / "support"
    support_dir.mkdir(parents=True)
    (support_dir / "support.md").write_text("Support Hotline Info")
    (docs_dir / "root.md").write_text("General Info")

    result_mapped = load_knowledge_base(str(docs_dir), phone_number="+18005550100")
    assert "Support Hotline Info" in result_mapped

def test_personality_engine_phone_mapping():
    name, instructions = get_persona("+18005550100")
    assert name == "Warm and Empathetic"
    assert instructions == PERSONAS["Warm and Empathetic"]

def test_sms_webhook_success():
    with patch("main.LLMService") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_response = AsyncMock(return_value="Hello! Your return has been processed.")
        mock_llm_cls.return_value = mock_llm_instance

        with TestClient(app) as client:
            response = client.post(
                "/webhook/sms",
                data={
                    "From": "+15551234567",
                    "To": "+18005550100",
                    "Body": "How do I return an item?"
                }
            )

            assert response.status_code == 200
            json_resp = response.json()
            assert json_resp["sender"] == "+15551234567"
            assert json_resp["recipient"] == "+18005550100"
            assert json_resp["reply"] == "Hello! Your return has been processed."
            assert json_resp["state"] == "BOT_ACTIVE"

def test_sms_webhook_twiml_format():
    with patch("main.LLMService") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_response = AsyncMock(return_value="TwiML response text.")
        mock_llm_cls.return_value = mock_llm_instance

        with TestClient(app) as client:
            response = client.post(
                "/webhook/sms",
                data={
                    "From": "+15551234567",
                    "To": "+18005550100",
                    "Body": "Hello"
                },
                headers={"Accept": "application/xml"}
            )

            assert response.status_code == 200
            assert "application/xml" in response.headers["content-type"]
            assert "<Response><Message>TwiML response text.</Message></Response>" in response.text

def test_sms_webhook_optout():
    with TestClient(app) as client:
        response = client.post(
            "/webhook/sms",
            data={
                "From": "+15559998888",
                "To": "+18005550100",
                "Body": "STOP"
            }
        )

        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["state"] == "OPTED_OUT"
        assert "unsubscribed" in json_resp["reply"].lower()

def test_sms_webhook_hitl_escalation():
    customer = "+15558887777"
    with TestClient(app) as client:
        # Trigger human escalation keyword
        response = client.post(
            "/webhook/sms",
            data={
                "From": customer,
                "To": "+18005550100",
                "Body": "I need to talk to a human agent please"
            }
        )

        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["state"] == "HUMAN_REQUESTED"
        assert "transferred your request to a human support agent" in json_resp["reply"]

        # Agent replies via agent endpoint
        agent_resp = client.post(
            "/agent/reply",
            json={
                "customer_number": customer,
                "message": "Hello, I am Agent Smith. How can I assist you today?"
            }
        )

        assert agent_resp.status_code == 200
        assert agent_resp.json()["state"] == "AGENT_CONNECTED"

@pytest.mark.anyio
async def test_calendar_service_override():
    from calendar_service import schedule_appointment_override
    res = await schedule_appointment_override(
        customer_phone="+15551112222",
        customer_name="Alice Smith",
        appointment_time="2026-12-01T10:00:00",
        service_name="VIP Consultation"
    )
    assert res["status"] == "success"
    assert res["event"]["payment_status"] == "BOOKED_UNPAID_OVERRIDE"
    assert "Alice Smith" in res["event"]["summary"]
    assert "https://meet.google.com/override-" in res["sms_confirmation"]

def test_c2_router_file_management():
    with TestClient(app) as client:
        # 1. List files
        list_resp = client.get("/api/c2/files")
        assert list_resp.status_code == 200
        assert isinstance(list_resp.json(), list)

        # 2. Write file
        write_resp = client.post(
            "/api/c2/files/write",
            json={"filepath": "test_c2_doc.md", "content": "# C2 Test Document"}
        )
        assert write_resp.status_code == 200
        assert write_resp.json()["status"] == "success"

        # 3. Read file
        read_resp = client.get("/api/c2/files/read?filepath=test_c2_doc.md")
        assert read_resp.status_code == 200
        assert read_resp.json()["content"] == "# C2 Test Document"

def test_c2_router_calendar_override():
    with TestClient(app) as client:
        override_resp = client.post(
            "/api/c2/calendar/override",
            json={
                "customer_phone": "+15553334444",
                "customer_name": "Bob Jones",
                "appointment_time": "2026-12-02T14:30:00",
                "service_name": "General Maintenance"
            }
        )
        assert override_resp.status_code == 200
        json_resp = override_resp.json()
        assert json_resp["status"] == "success"
        assert json_resp["event"]["payment_status"] == "BOOKED_UNPAID_OVERRIDE"
