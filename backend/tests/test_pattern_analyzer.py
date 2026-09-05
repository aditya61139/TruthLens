import pytest
from app.services.pattern_analyzer import MisinformationPatternAnalyzer

def test_clean_objective_text():
    text = "The European Space Agency launched the Euclid telescope to map the dark universe."
    result = MisinformationPatternAnalyzer.analyze(text)
    assert result["red_flag_score"] < 25.0
    assert result["risk_color"] in ["green", "yellow"]
    assert result["checklist"]["clickbait_detected"] is False

def test_sensationalist_misinformation_text():
    text = "URGENT WARNING: SHOCKING secret truth big pharma is hiding from you! Miracle cure for all cancer discovered! Scientists say 1000% recovery! SHARE BEFORE TAKEN DOWN!!!"
    result = MisinformationPatternAnalyzer.analyze(text)
    assert result["red_flag_score"] >= 60.0
    assert result["risk_color"] == "red"
    assert result["checklist"]["clickbait_detected"] is True
    assert result["checklist"]["conspiracy_cues"] is True
    assert result["checklist"]["dubious_statistics"] is True
    assert result["checklist"]["excessive_sensationalism"] is True

def test_vague_attribution_detection():
    text = "Scientists say drinking lemon water removes all body toxins immediately."
    result = MisinformationPatternAnalyzer.analyze(text)
    assert result["checklist"]["vague_sourcing"] is True
