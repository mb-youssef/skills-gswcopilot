"""Tests for FastAPI activity management endpoints"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Verify all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_has_correct_structure(self, client):
        """Verify activity structure has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_participants_are_strings(self, client):
        """Verify participants list contains email strings"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_details in data.values():
            for participant in activity_details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        """Verify successful signup adds participant"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity}"
        
        # Verify participant was added
        check_response = client.get("/activities")
        participants = check_response.json()[activity]["participants"]
        assert email in participants

    def test_signup_duplicate_registration_fails(self, client):
        """Verify duplicate signup is rejected (tests bug fix)"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_invalid_activity_fails(self, client):
        """Verify signup to non-existent activity fails"""
        email = "newstudent@mergington.edu"
        activity = "Non-Existent Activity"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client):
        """Verify student can sign up for multiple different activities"""
        email = "student@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Art Studio"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        check_response = client.get("/activities")
        data = check_response.json()
        for activity in activities_to_join:
            assert email in data[activity]["participants"]

    def test_signup_updates_available_spots(self, client):
        """Verify signup decreases available spots"""
        activity = "Chess Club"
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()[activity]["participants"])
        
        client.post(
            f"/activities/{activity}/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        updated_response = client.get("/activities")
        updated_participants = len(updated_response.json()[activity]["participants"])
        
        assert updated_participants == initial_participants + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client):
        """Verify successful unregistration removes participant"""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity}"
        
        # Verify participant was removed
        check_response = client.get("/activities")
        participants = check_response.json()[activity]["participants"]
        assert email not in participants

    def test_unregister_non_participant_fails(self, client):
        """Verify unregistering a non-participant fails"""
        activity = "Chess Club"
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_invalid_activity_fails(self, client):
        """Verify unregister from non-existent activity fails"""
        activity = "Non-Existent Activity"
        email = "student@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_updates_available_spots(self, client):
        """Verify unregister increases available spots"""
        activity = "Chess Club"
        email = "michael@mergington.edu"
        
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()[activity]["participants"])
        
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        updated_response = client.get("/activities")
        updated_participants = len(updated_response.json()[activity]["participants"])
        
        assert updated_participants == initial_participants - 1


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    def test_signup_then_unregister_flow(self, client):
        """Verify signup followed by unregister works correctly"""
        activity = "Programming Class"
        email = "teststudent@mergington.edu"
        
        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify added
        check_response = client.get("/activities")
        assert email in check_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify removed
        final_response = client.get("/activities")
        assert email not in final_response.json()[activity]["participants"]

    def test_signup_unregister_then_signup_again(self, client):
        """Verify student can re-signup after unregistering"""
        activity = "Tennis Club"
        email = "student@mergington.edu"
        
        # First signup
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Unregister
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        # Signup again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify in activity
        check_response = client.get("/activities")
        assert email in check_response.json()[activity]["participants"]

    def test_participant_list_accuracy(self, client):
        """Verify participant list stays accurate through multiple operations"""
        activity = "Art Studio"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Signup all students
        for email in emails:
            client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
        
        # Verify all are present
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Remove first student
        client.delete(
            f"/activities/{activity}/unregister",
            params={"email": emails[0]}
        )
        
        # Verify only two remain
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] not in participants
        assert emails[1] in participants
        assert emails[2] in participants
