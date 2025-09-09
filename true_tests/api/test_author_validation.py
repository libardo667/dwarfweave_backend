"""Tests for author API input validation."""

import pytest
import requests
from fastapi import HTTPException
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from src.models.schemas import SuggestReq, GenerateStoryletRequest, WorldDescription

BASE_URL = "http://localhost:8000"


class TestAuthorInputValidation:
    """Test suite for author API input validation (Task: author-002)."""
    
    def test_suggest_req_valid_n_parameter(self):
        """Test SuggestReq accepts valid n values."""
        # Valid values within range
        valid_requests = [
            SuggestReq(n=1),
            SuggestReq(n=10), 
            SuggestReq(n=20)
        ]
        
        for req in valid_requests:
            assert req.n >= 1
            assert req.n <= 20
    
    def test_suggest_req_invalid_n_parameter(self):
        """Test SuggestReq rejects invalid n values."""
        # Test n too small
        with pytest.raises(ValueError) as exc_info:
            SuggestReq(n=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            SuggestReq(n=-5)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)
        
        # Test n too large
        with pytest.raises(ValueError) as exc_info:
            SuggestReq(n=25)
        assert "ensure this value is less than or equal to 20" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            SuggestReq(n=100)
        assert "ensure this value is less than or equal to 20" in str(exc_info.value)
    
    def test_generate_storylet_request_valid_count(self):
        """Test GenerateStoryletRequest accepts valid count values."""
        valid_requests = [
            GenerateStoryletRequest(count=1),
            GenerateStoryletRequest(count=8),
            GenerateStoryletRequest(count=15)
        ]
        
        for req in valid_requests:
            assert req.count >= 1
            assert req.count <= 15
    
    def test_generate_storylet_request_invalid_count(self):
        """Test GenerateStoryletRequest rejects invalid count values."""
        # Test count too small
        with pytest.raises(ValueError) as exc_info:
            GenerateStoryletRequest(count=0)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            GenerateStoryletRequest(count=-3)
        assert "ensure this value is greater than or equal to 1" in str(exc_info.value)
        
        # Test count too large
        with pytest.raises(ValueError) as exc_info:
            GenerateStoryletRequest(count=20)
        assert "ensure this value is less than or equal to 15" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            GenerateStoryletRequest(count=50)
        assert "ensure this value is less than or equal to 15" in str(exc_info.value)
    
    def test_world_description_storylet_count_validation(self):
        """Test WorldDescription storylet_count validation (already implemented)."""
        # Test valid values
        valid_world = WorldDescription(
            description="A magical fantasy realm with ancient mysteries",
            theme="fantasy",
            storylet_count=25
        )
        assert valid_world.storylet_count == 25
        
        # Test invalid values
        with pytest.raises(ValueError) as exc_info:
            WorldDescription(
                description="A magical fantasy realm",
                theme="fantasy", 
                storylet_count=3  # Too small
            )
        assert "ensure this value is greater than or equal to 5" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            WorldDescription(
                description="A magical fantasy realm",
                theme="fantasy",
                storylet_count=75  # Too large
            )
        assert "ensure this value is less than or equal to 50" in str(exc_info.value)
    
    def test_populate_endpoint_target_count_validation(self):
        """Test /author/populate endpoint validates target_count parameter using real server."""
        valid_responses = []
        for target_count in [1, 50, 100]:
            try:
                response = requests.post(f"{BASE_URL}/author/populate?target_count={target_count}", timeout=3)
            except requests.ConnectionError:
                pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
            if response.status_code != 400:
                valid_responses.append(response.status_code)
        assert all(code != 400 for code in valid_responses), "Valid target_count values should not return 400"
        # Test invalid target_count values - too small
        response = requests.post(f"{BASE_URL}/author/populate?target_count=0", timeout=3)
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "target_count must be at least 1" in error_detail
        response = requests.post(f"{BASE_URL}/author/populate?target_count=-5", timeout=3)
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "target_count must be at least 1" in error_detail
        # Test invalid target_count values - too large
        response = requests.post(f"{BASE_URL}/author/populate?target_count=150", timeout=3)
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "target_count cannot exceed 100" in error_detail
        response = requests.post(f"{BASE_URL}/author/populate?target_count=500", timeout=3)
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "target_count cannot exceed 100" in error_detail
    
    def test_suggest_endpoint_with_invalid_n(self):
        """Test /author/suggest endpoint rejects invalid n values using real server."""
        invalid_payload = {
            "n": 25,  # Too large
            "themes": ["adventure"],
            "bible": {}
        }
        try:
            response = requests.post(f"{BASE_URL}/author/suggest", json=invalid_payload, timeout=3)
        except requests.ConnectionError:
            pytest.fail("Server is not running at http://localhost:8000. Please start the FastAPI server before running this test.")
        assert response.status_code == 422  # Validation error
        error_detail = response.json()
        assert "validation error" in str(error_detail).lower()
    
    def test_default_values_are_valid(self):
        """Test that all default values pass validation."""
        # Test SuggestReq defaults
        suggest_req = SuggestReq()
        assert suggest_req.n == 3
        assert 1 <= suggest_req.n <= 20
        
        # Test GenerateStoryletRequest defaults  
        generate_req = GenerateStoryletRequest()
        assert generate_req.count == 3
        assert 1 <= generate_req.count <= 15
        
        # Test WorldDescription defaults
        world_desc = WorldDescription(
            description="A test world description that meets minimum length",
            theme="fantasy"
        )
        assert world_desc.storylet_count == 15
        assert 5 <= world_desc.storylet_count <= 50
    
    def test_edge_case_boundary_values(self):
        """Test boundary values are handled correctly."""
        # Test minimum valid values
        min_suggest = SuggestReq(n=1)
        assert min_suggest.n == 1
        
        min_generate = GenerateStoryletRequest(count=1)
        assert min_generate.count == 1
        
        min_world = WorldDescription(
            description="Minimum length description for testing",
            theme="test",
            storylet_count=5
        )
        assert min_world.storylet_count == 5
        
        # Test maximum valid values
        max_suggest = SuggestReq(n=20)
        assert max_suggest.n == 20
        
        max_generate = GenerateStoryletRequest(count=15)
        assert max_generate.count == 15
        
        max_world = WorldDescription(
            description="Maximum storylet count description for comprehensive testing",
            theme="test",
            storylet_count=50
        )
        assert max_world.storylet_count == 50
