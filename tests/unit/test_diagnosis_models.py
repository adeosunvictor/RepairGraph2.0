from repairgraph.models import DiagnosisReport, TriageResult


def test_triage_defaults_to_repair_intent() -> None:
    result = TriageResult(
        type="bug",
        severity="P2",
        component="service",
        summary="A reported defect",
        confidence=0.9,
    )
    assert result.intent == "repair"


def test_diagnosis_report_can_describe_healthy_repo() -> None:
    report = DiagnosisReport(
        overall_status="healthy",
        summary="No defect found.",
        files_reviewed=["app.py"],
        test_summary="Test suite passed",
    )
    assert report.overall_status == "healthy"
    assert report.findings == []
