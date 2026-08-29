import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app, app_state
from knowledge_base import load_knowledge_base, INITIATIVE_MAP
from personality_engine import PERSONAS, get_persona, get_random_persona

def test_load_knowledge_base(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("# Doc 1\nContent 1")
    (docs_dir / "doc2.md").write_text("# Doc 2\nContent 2")
    (docs_dir / "ignore.txt").write_text("Should be ignored")

    result = load_knowledge_base(str(docs_dir))

    assert "--- Document: doc1.md ---" in result
    assert "# Doc 1" in result
    assert "--- Document: doc2.md ---" in result
    assert "# Doc 2" in result
    assert "Should be ignored" not in result

def test_load_knowledge_base_phone_number_mapping(tmp_path):
    docs_dir = tmp_path / "docs"
    support_dir = docs_dir / "support"
    support_dir.mkdir(parents=True)
    (support_dir / "support.md").write_text("Support Hotline Info")
    (docs_dir / "root.md").write_text("General Info")

    # +18005550100 maps to 'support' subdirectory in INITIATIVE_MAP
    result_mapped = load_knowledge_base(str(docs_dir), phone_number="+18005550100")
    assert "Support Hotline Info" in result_mapped
    assert "General Info" not in result_mapped

    # Unmapped phone number falls back to root docs
    result_unmapped = load_knowledge_base(str(docs_dir), phone_number="+19999999999")
    assert "General Info" in result_unmapped

def test_load_knowledge_base_nonexistent():
    result = load_knowledge_base("nonexistent_directory_12345")
    assert result == ""

def test_personality_engine():
    assert len(PERSONAS) == 3
    assert "Warm and Empathetic" in PERSONAS
    assert "Crisp and Professional" in PERSONAS
    assert "Witty and Casual" in PERSONAS

    # Test random persona
    persona_name, instructions = get_random_persona()
    assert persona_name in PERSONAS
    assert instructions == PERSONAS[persona_name]

def test_personality_engine_phone_mapping():
    # +18005550100 is mapped to "Warm and Empathetic"
    name, instructions = get_persona("+18005550100")
    assert name == "Warm and Empathetic"
    assert instructions == PERSONAS["Warm and Empathetic"]

    # +18005550200 is mapped to "Crisp and Professional"
    name, instructions = get_persona("+18005550200")
    assert name == "Crisp and Professional"

    # Unmapped number picks persona randomly
    name_unmapped, _ = get_persona("+19999999999")
    assert name_unmapped in PERSONAS

def test_sms_webhook_success():
    with patch("main.LLMService") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_response.return_value = "Hello! Your return has been processed."
        mock_llm_cls.return_value = mock_llm_instance

        with TestClient(app) as client:
            response = client.post(
                "/webhook/sms",
                data={
                    "From": "+1234567890",
                    "To": "+18005550100", # Mapped to Support initiative
                    "Body": "Need help with support"
                }
            )

            assert response.status_code == 200
            json_resp = response.json()
            assert json_resp["sender"] == "+1234567890"
            assert json_resp["recipient"] == "+18005550100"
            assert json_resp["reply"] == "Hello! Your return has been processed."
            assert json_resp["persona"] == "Warm and Empathetic"

            # Verify generate_response call arguments
            mock_llm_instance.generate_response.assert_called_once()
            call_kwargs = mock_llm_instance.generate_response.call_args.kwargs
            assert call_kwargs["user_message"] == "Need help with support"
            assert "Customer Support Help" in call_kwargs["knowledge_context"]

def test_sms_webhook_empty_body():
    with TestClient(app) as client:
        response = client.post(
            "/webhook/sms",
            data={
                "From": "+1234567890",
                "To": "+0987654321",
                "Body": "   "
            }
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "SMS Body cannot be empty."

def test_sms_webhook_llm_error():
    with patch("main.LLMService") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_response.side_effect = Exception("LLM API Error")
        mock_llm_cls.return_value = mock_llm_instance

        with TestClient(app) as client:
            app_state["llm_service"] = mock_llm_instance
            response = client.post(
                "/webhook/sms",
                data={
                    "From": "+1234567890",
                    "To": "+0987654321",
                    "Body": "Hello"
                }
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "Failed to generate response."
