import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


def test_root_redirects_to_static():
    response = client.get("/")
    # FastAPI RedirectResponse defaults to 307 Temporary Redirect
    assert response.status_code in (307, 302)
    # Location header should point to static index
    assert response.headers.get("location") == "/static/index.html"


def test_get_activities_returns_data():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    # Ensure known activity exists and has expected keys
    assert "Basketball Team" in data
    activity = data["Basketball Team"]
    for key in ("description", "schedule", "max_participants", "participants"):
        assert key in activity
    assert isinstance(activity["participants"], list)


def test_signup_and_unregister_flow():
    test_activity = "Programming Class"
    test_email = "newstudent@mergington.edu"

    # Ensure clean slate: if already present, remove first
    if test_email in activities[test_activity]["participants"]:
        activities[test_activity]["participants"].remove(test_email)

    # Sign up the user
    signup_resp = client.post(f"/activities/{test_activity}/signup", params={"email": test_email})
    assert signup_resp.status_code == 200, signup_resp.text
    assert test_email in activities[test_activity]["participants"]

    # Duplicate signup should fail
    dup_resp = client.post(f"/activities/{test_activity}/signup", params={"email": test_email})
    assert dup_resp.status_code == 400
    assert dup_resp.json()["detail"] == "Student already signed up for this activity"

    # Unregister the user
    del_resp = client.delete(f"/activities/{test_activity}/signup", params={"email": test_email})
    assert del_resp.status_code == 200, del_resp.text
    assert test_email not in activities[test_activity]["participants"]

    # Unregistering again should 404
    del_again_resp = client.delete(f"/activities/{test_activity}/signup", params={"email": test_email})
    assert del_again_resp.status_code == 404
    assert del_again_resp.json()["detail"] == "Student not registered for this activity"


def test_signup_nonexistent_activity():
    resp = client.post("/activities/Nonexistent Club/signup", params={"email": "a@b.com"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"
