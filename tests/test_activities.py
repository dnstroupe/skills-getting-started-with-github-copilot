import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Chess Club"
FIRST_STUDENT = "alex@example.edu"
SECOND_STUDENT = "jordan@example.edu"


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 3,
            "participants": [FIRST_STUDENT, SECOND_STUDENT],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_signup_updates_activity_listing(client):
    # Arrange
    new_student = "casey@example.edu"

    # Act
    signup_response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": new_student},
    )
    listing_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == (
        f"Signed up {new_student} for {ACTIVITY_NAME}"
    )
    assert listing_response.status_code == 200
    assert listing_response.json()[ACTIVITY_NAME]["participants"] == [
        FIRST_STUDENT,
        SECOND_STUDENT,
        new_student,
    ]


def test_duplicate_signup_is_rejected(client):
    # Arrange
    existing_participants = [FIRST_STUDENT, SECOND_STUDENT]

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": FIRST_STUDENT},
    )
    listing_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"{FIRST_STUDENT} is already signed up for {ACTIVITY_NAME}"
    )
    assert listing_response.json()[ACTIVITY_NAME]["participants"] == existing_participants


def test_removal_updates_listing_and_preserves_other_participants(client, monkeypatch):
    # Arrange
    removed_student = FIRST_STUDENT
    remaining_students = [SECOND_STUDENT, "taylor@example.edu"]
    monkeypatch.setitem(
        app_module.activities[ACTIVITY_NAME],
        "participants",
        [removed_student, *remaining_students],
    )

    # Act
    removal_response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": removed_student},
    )
    listing_response = client.get("/activities")

    # Assert
    assert removal_response.status_code == 200
    assert removal_response.json()["message"] == (
        f"Removed {removed_student} from {ACTIVITY_NAME}"
    )
    assert listing_response.status_code == 200
    assert listing_response.json()[ACTIVITY_NAME]["participants"] == remaining_students


def test_signup_rejects_missing_activity(client):
    # Arrange
    missing_activity = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{missing_activity}/signup",
        params={"email": FIRST_STUDENT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_removal_rejects_missing_activity(client):
    # Arrange
    missing_activity = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{missing_activity}/signup",
        params={"email": FIRST_STUDENT},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_removal_rejects_missing_participant(client):
    # Arrange
    missing_student = "not-signed-up@example.edu"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": missing_student},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        f"{missing_student} is not signed up for {ACTIVITY_NAME}"
    )