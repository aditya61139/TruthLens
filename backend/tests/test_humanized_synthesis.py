import pytest
import asyncio
from app.services.synthesis_service import SynthesisService

@pytest.mark.asyncio
async def test_humanized_settled_fact_synthesis():
    """Verify that settled knowledge generates natural, conversational briefings."""
    settled_info = {
        "is_settled_fact": True,
        "truth_value": "True",
        "fact_type": "Universal Scientific Principle",
        "confidence": 98.0,
        "explanation": "Water boiling point at 100°C under standard pressure.",
        "summary": "This claim aligns with established scientific reality.",
        "evidence_note": "Thermodynamic principle",
        "reference_sources": ["NIST Standards"]
    }

    result = await SynthesisService.synthesize(
        claim_text="water boils at 100 degrees celsius",
        evidence_list=[],
        red_flags={"red_flag_score": 0.0, "flags": []},
        settled_fact_info=settled_info,
        allow_gemini_call=False
    )

    assert result["truth_value"] == "True"
    assert "plain_english_takeaway" in result
    takeaway = result["plain_english_takeaway"]
    assert len(takeaway) > 10
    # Must not contain robotic strings
    assert "similarity score" not in takeaway.lower()
    assert "stance: entails" not in takeaway.lower()
    assert "retrieved document array" not in takeaway.lower()

@pytest.mark.asyncio
async def test_humanized_contradiction_synthesis():
    """Verify that contradictory evidence generates a clear plain-English takeaway."""
    evidence = [{
        "source_name": "Reuters",
        "source_site": "reuters.com",
        "source_url": "https://reuters.com/article/1",
        "title": "Sun Rises in East, Scientists Reiterate",
        "raw_rating": "False",
        "normalized_verdict": "False",
        "stance": "CONTRADICTS",
        "stance_reason": "Directly contradicts the assertion.",
        "confidence_contribution": 90.0,
        "explanation": "Reuters verified evidence."
    }]

    result = await SynthesisService.synthesize(
        claim_text="the sun rises in the west",
        evidence_list=evidence,
        red_flags={"red_flag_score": 20.0, "flags": []},
        settled_fact_info=None,
        allow_gemini_call=False
    )

    assert result["truth_value"] == "False"
    assert "plain_english_takeaway" in result
    takeaway = result["plain_english_takeaway"]
    assert "Bottom Line:" in takeaway or "false" in takeaway.lower()
    assert "STANCE:" not in takeaway
    assert "CONTRADICTS" not in takeaway  # should use clean wording, not raw enum

@pytest.mark.asyncio
async def test_humanized_360_briefing_prose():
    """Verify that 360° briefing paragraphs read naturally without robotic placeholders."""
    briefing = SynthesisService.generate_360_briefing(
        claim_text="Heavy rainfall causes river breach in downstream valley",
        truth_value="True",
        knowledge_certainty="Emerging / Current Event",
        category="Natural Disaster",
        evidence_list=[{"source_name": "AP News", "stance": "ENTAILS"}],
        settled_fact_info=None,
        mode="Claim Verification"
    )

    what_happened = briefing["what_happened"]
    key_takeaway = briefing["key_takeaway"]

    assert len(what_happened) > 30
    assert "assess this claim as TRUE" not in what_happened
    assert "Bottom Line:" in key_takeaway or "Verified" in key_takeaway
