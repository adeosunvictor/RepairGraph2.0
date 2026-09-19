from repairgraph.models import Issue, RepairReport, SecurityResult


def test_security_result_can_be_constructed():
    result = SecurityResult(approved=True)

    assert result.approved is True
    assert result.risk_level == "low"


def test_repair_report_can_be_constructed():
    report = RepairReport(
        issue=Issue(
            id="001",
            title="Test issue",
            body="Test body",
        ),
        status="finished",
    )

    assert report.issue.id == "001"
    assert report.status == "finished"