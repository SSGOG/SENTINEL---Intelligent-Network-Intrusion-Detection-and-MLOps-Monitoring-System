from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


DASHBOARD_PATH = Path(__file__).resolve().parents[1] / "src" / "sentinel" / "dashboard.py"
NAVIGATION_PAGES = [
    ("3. Batch CSV Threat Analysis", "Batch Flow CSV Inspection & Threat Triage"),
    ("4. Model Performance & Evaluation", "Champion Model Performance & Holdout Evaluation"),
    ("5. Explainability (SHAP)", "Responsible AI: Feature Attribution via SHAP"),
    ("7. Lineage & MLflow Provenance", "End-to-End MLOps Lineage & Provenance"),
]


@pytest.mark.parametrize(("page", "heading"), NAVIGATION_PAGES)
def test_navigation_page_renders(page, heading):
    app = AppTest.from_file(str(DASHBOARD_PATH), default_timeout=20).run()
    app.radio[0].set_value(page).run()

    assert not app.exception
    assert heading in [item.value for item in app.header]

    if page.startswith("3."):
        batch_button = next(
            button for button in app.button
            if button.label == "⚡ Run Full Batch Threat Classification"
        )
        batch_button.click().run()
        assert not app.exception
        assert "Total Flows Analyzed" in [metric.label for metric in app.metric]
