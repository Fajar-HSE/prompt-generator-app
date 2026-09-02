import json
import sys
from unittest import mock

import pytest

sys.path.insert(0, ".")

import app as app_module
from app import (
    LLM_API_KEY,
    build_prompt,
    demo_resolution,
    generate_demo_output,
    parse_output,
    validate_input,
)


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


VALID_DATA = {
    "programName": "Professional Data Analyst Certification",
    "competency": "data analytics, SQL, dashboarding",
    "targetAudience": "junior data analysts",
    "programType": "sertifikasi",
    "materialType": "poster",
    "platformFormat": "Instagram feed 1080x1350",
    "date": "15-17 Agustus 2026",
    "location": "Jakarta & Online",
    "price": "Rp 2.500.000",
    "brand": "TechCert Indonesia",
    "cta": "Daftar via WA 0812-3456-7890",
    "brandColors": "#1a73e8",
    "unit_kompetensi": "Excel, Dashboard, Python",
    "programBenefits": "Sertifikat resmi BNSP",
}


def test_validate_input_ok():
    assert validate_input(VALID_DATA) == []


def test_validate_input_missing_required():
    errors = validate_input({"programName": "X"})
    assert any("Topik / Kompetensi" in e for e in errors)
    assert any("Target Audience" in e for e in errors)


def test_validate_input_not_dict():
    errors = validate_input([])
    assert len(errors) == 1


def test_parse_output_sections():
    raw = (
        "## IMAGE PROMPT\nA professional photo.\n"
        "## NEGATIVE PROMPT\ncartoon, watermark\n"
        "## FORMAT & RESOLUTION\n1080x1350px\n"
        "## QUALITY SCORE\nOVERALL: 8/10\n"
    )
    sections = parse_output(raw)
    assert sections["IMAGE PROMPT"] == "A professional photo."
    assert sections["NEGATIVE PROMPT"] == "cartoon, watermark"
    assert sections["FORMAT & RESOLUTION"] == "1080x1350px"
    assert sections["QUALITY SCORE"] == "OVERALL: 8/10"


def test_parse_output_respects_order():
    raw = (
        "## QUALITY SCORE\n8/10\n"
        "## IMAGE PROMPT\nphoto\n"
    )
    sections = parse_output(raw)
    assert list(sections.keys())[0] == "IMAGE PROMPT"


def test_parse_output_ignores_leading_text():
    raw = "intro text\n## IMAGE PROMPT\nphoto\n"
    sections = parse_output(raw)
    assert "intro text" not in sections
    assert sections["IMAGE PROMPT"] == "photo"


def test_build_prompt_fills_all_fields():
    prompt = build_prompt(VALID_DATA)
    assert "Professional Data Analyst Certification" in prompt
    assert "data analytics, SQL, dashboarding" in prompt
    assert "15-17 Agustus 2026" in prompt
    assert "TechCert Indonesia" in prompt


def test_build_prompt_defaults_for_missing():
    prompt = build_prompt({"programName": "X", "competency": "Y", "targetAudience": "Z"})
    assert "N/A" in prompt  # date/location/price default


def test_demo_resolution_variants():
    assert "2480x3508px" in demo_resolution("poster", "Instagram feed")  # material-based A4
    assert "1748x2480px" in demo_resolution("flyer", "")
    assert "1200x627px" in demo_resolution("poster", "1200x627px (1.91:1) — LinkedIn / web banner")
    assert "1080x1080px" in demo_resolution("social_media", "")
    assert "1748x2480px" in demo_resolution("brosur", "")


def test_build_prompt_includes_material_brief():
    prompt = build_prompt({**VALID_DATA, "materialType": "brosur"})
    assert "jelaskan dan yakinkan" in prompt
    assert "GAYA BAHASA DESAIN" in prompt
    assert "STRUKTUR KONTEN" in prompt
    assert "Problem -> Solution -> Benefit -> Features -> Proof -> CTA" in prompt
    assert "Meyakinkan" in prompt
    assert "TEKNIK HOOK" in prompt
    assert "Hook brosur" in prompt

    flyer_prompt = build_prompt({**VALID_DATA, "materialType": "flyer"})
    assert "lihat, tertarik, bertindak" in flyer_prompt
    assert "Hook -> Offer/Benefit -> Key info -> CTA" in flyer_prompt
    assert "Hook flyer" in flyer_prompt

    unknown_prompt = build_prompt(VALID_DATA)
    assert "Poster" in unknown_prompt  # defaults to poster brief
    assert "Hook -> Main Benefit -> Proof -> CTA" in unknown_prompt
    assert "Hook poster" in unknown_prompt


def test_build_prompt_uses_unit_kompetensi_field():
    prompt = build_prompt({**VALID_DATA, "unit_kompetensi": "Excel, Dashboard"})
    assert "UNIT KOMPETENSI" in prompt
    assert "Excel, Dashboard" in prompt


def test_generate_demo_output_structure():
    sections = generate_demo_output(VALID_DATA)
    assert set(sections.keys()) == {
        "IMAGE PROMPT",
        "NEGATIVE PROMPT",
        "FORMAT & RESOLUTION",
        "QUALITY SCORE",
    }
    assert "TechCert Indonesia" in sections["IMAGE PROMPT"]


def test_generate_demo_output_material_aware():
    poster = generate_demo_output({**VALID_DATA, "materialType": "poster"})
    brosur = generate_demo_output({**VALID_DATA, "materialType": "brosur"})
    flyer = generate_demo_output({**VALID_DATA, "materialType": "flyer"})

    assert poster["IMAGE PROMPT"] != brosur["IMAGE PROMPT"]
    assert brosur["IMAGE PROMPT"] != flyer["IMAGE PROMPT"]

    assert "Problem -> Solution -> Benefit -> Features -> Proof -> CTA" in brosur["IMAGE PROMPT"]
    assert "Hook -> Offer/Benefit -> Key info -> CTA" in flyer["IMAGE PROMPT"]

    assert "2480x3508px" in poster["FORMAT & RESOLUTION"]
    assert "1748x2480px" in brosur["FORMAT & RESOLUTION"]
    assert "1748x2480px" in flyer["FORMAT & RESOLUTION"]


def test_api_status_reports_demo_mode(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "demo_mode" in data
    assert "model" in data


def test_generate_validation_error(client):
    resp = client.post("/api/generate", json={"programName": "X"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert data["fields"]


def test_generate_invalid_json(client):
    resp = client.post("/api/generate", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_generate_demo_mode_when_no_key(client, monkeypatch):
    if LLM_API_KEY:
        pytest.skip("LLM_API_KEY is set; testing demo path requires no key")
    resp = client.post("/api/generate", json=VALID_DATA)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["demo_mode"] is True
    assert set(data["sections"].keys()) == {
        "IMAGE PROMPT",
        "NEGATIVE PROMPT",
        "FORMAT & RESOLUTION",
        "QUALITY SCORE",
    }


@mock.patch.object(app_module, "LLM_API_KEY", "sk-test")
@mock.patch.object(app_module.requests.Session, "post")
def test_generate_success_parses_sections(mock_post, client, monkeypatch):
    monkeypatch.setattr(app_module, "LLM_API_KEY", "sk-test")
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": (
                        "## IMAGE PROMPT\nA poster.\n"
                        "## NEGATIVE PROMPT\ncartoon\n"
                        "## FORMAT & RESOLUTION\n1080x1350px\n"
                        "## QUALITY SCORE\nOVERALL: 9/10\n"
                    )
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    resp = client.post("/api/generate", json=VALID_DATA)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["demo_mode"] is False
    assert data["model"] == app_module.LLM_MODEL
    assert data["sections"]["IMAGE PROMPT"] == "A poster."


@mock.patch.object(app_module, "LLM_API_KEY", "sk-test")
@mock.patch.object(app_module.requests.Session, "post")
def test_generate_unauthorized(mock_post, client, monkeypatch):
    monkeypatch.setattr(app_module, "LLM_API_KEY", "sk-test")
    mock_response = mock.Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"error": {"message": "invalid key"}}
    mock_post.return_value = mock_response

    resp = client.post("/api/generate", json=VALID_DATA)
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@mock.patch.object(app_module, "LLM_API_KEY", "sk-test")
@mock.patch.object(app_module.requests.Session, "post")
def test_generate_rate_limited(mock_post, client, monkeypatch):
    monkeypatch.setattr(app_module, "LLM_API_KEY", "sk-test")
    mock_response = mock.Mock()
    mock_response.status_code = 429
    mock_response.raise_for_status = lambda: None
    mock_response.json.return_value = {"error": {"message": "rate limited"}}
    mock_post.return_value = mock_response

    resp = client.post("/api/generate", json=VALID_DATA)
    assert resp.status_code == 429
    assert resp.get_json()["success"] is False


def test_settings_get_empty(client):
    """Test that settings endpoint returns empty when no settings stored"""
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["baseUrl"] == ""
    assert data["model"] == ""
    assert data["apiKey"] == ""


def test_settings_post_success(client):
    """Test that settings can be saved via POST"""
    settings_data = {
        "baseUrl": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4",
        "apiKey": "sk-test-settings-123",
        "provider": "openai"
    }
    
    resp = client.post("/api/settings", json=settings_data)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_settings_post_missing_fields(client):
    """Test that settings endpoint returns error when fields are missing"""
    settings_data = {
        "baseUrl": "https://api.openai.com/v1/chat/completions"
    }
    
    resp = client.post("/api/settings", json=settings_data)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_settings_roundtrip(client):
    """Test that settings can be saved and retrieved"""
    settings_data = {
        "baseUrl": "https://api.custom.com/v1",
        "model": "custom-model",
        "apiKey": "sk-test-roundtrip",
        "provider": "custom"
    }
    
    # Save
    resp = client.post("/api/settings", json=settings_data)
    assert resp.status_code == 200
    
    # Retrieve
    resp = client.get("/api/settings")
    data = resp.get_json()
    assert data["baseUrl"] == settings_data["baseUrl"]
    assert data["model"] == settings_data["model"]
    assert data["apiKey"] == settings_data["apiKey"]


def test_generate_uses_settings_from_server(client, monkeypatch):
    """Test that generate uses settings from server session"""
    monkeypatch.setattr(app_module, "LLM_API_KEY", "")
    
    # Save settings to session
    settings_data = {
        "baseUrl": "https://api.custom.com/v1",
        "model": "custom-model",
        "apiKey": "sk-server-test"
    }
    resp = client.post("/api/settings", json=settings_data)
    assert resp.status_code == 200
    
    # Test that settings are stored in session
    with client.session_transaction() as session:
        assert session.get("llm_api_key") == "sk-server-test"
        assert session.get("llm_base_url") == "https://api.custom.com/v1"
        assert session.get("llm_model") == "custom-model"
