import pytest
import os
from backend.services.ai_service import AIService

def test_generate_executive_summary_mock():
    # Save original keys
    orig_gemini = os.environ.get("GEMINI_API_KEY")
    orig_openai = os.environ.get("OPENAI_API_KEY")
    
    try:
        # Clear API keys to test mock fallback behavior
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
            
        service = AIService()
        
        mock_data = {
            "incidents": {
                "total_incidents": 150,
                "mttr_hours": 3.5
            },
            "slas": {
                "compliance_rate_percent": 96.5
            },
            "problems": {
                "problem_backlog": 12
            }
        }
        
        summary = service.generate_executive_summary(mock_data)
        
        assert "stable" in summary
        assert "150" in summary
        assert "3.5 hours" in summary
        assert "96.5%" in summary
        assert "12" in summary
        
        # Test at risk
        mock_data["slas"]["compliance_rate_percent"] = 80.0
        summary_risk = service.generate_executive_summary(mock_data)
        assert "at risk" in summary_risk
    finally:
        if orig_gemini is not None:
            os.environ["GEMINI_API_KEY"] = orig_gemini
        if orig_openai is not None:
            os.environ["OPENAI_API_KEY"] = orig_openai

def test_normalize_ops_narrative():
    from backend.services.ai_service import normalize_ops_narrative
    
    # Test stripping canned introductory filler
    raw_1 = "Based on the provided data, incident volume increased by 12% across payment channels."
    clean_1 = normalize_ops_narrative(raw_1)
    assert clean_1 == "incident volume increased by 12% across payment channels."
    
    raw_2 = "Certainly! Here is an analysis: SLA compliance dropped to 92.4% on Core Database."
    clean_2 = normalize_ops_narrative(raw_2)
    assert clean_2 == "SLA compliance dropped to 92.4% on Core Database."
    
    # Test em-dash normalization
    raw_3 = "Payment Gateway — elevated timeouts — investigated."
    clean_3 = normalize_ops_narrative(raw_3)
    assert " - " in clean_3
    assert "—" not in clean_3

