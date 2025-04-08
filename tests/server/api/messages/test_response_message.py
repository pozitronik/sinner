import json

from sinner.server.api.messages.ResponseMessage import ResponseMessage


class TestResponseMessage:
    """Tests for the ResponseMessage class."""

    def test_init_with_default_status(self):
        """Test initialization with default status."""
        msg = ResponseMessage(type_=ResponseMessage.GENERAL, field1="value1")
        assert msg.type == ResponseMessage.GENERAL
        assert msg.status == ResponseMessage.STATUS_OK
        assert msg.field1 == "value1"

    def test_init_with_custom_status(self):
        """Test initialization with custom status."""
        msg = ResponseMessage(status=ResponseMessage.STATUS_ERROR, type_=ResponseMessage.GENERAL, field1="value1")
        assert msg.status == ResponseMessage.STATUS_ERROR

    def test_class_constants(self):
        """Test class constants."""
        assert ResponseMessage.STATUS_OK == "ok"
        assert ResponseMessage.STATUS_ERROR == "error"
        assert ResponseMessage.GENERAL == "GENERAL"
        assert ResponseMessage.METADATA == "METADATA"
        assert ResponseMessage.FRAME == "FRAME"

    def test_ok_response_factory(self):
        """Test ok_response factory method."""
        msg = ResponseMessage.ok_response(type_=ResponseMessage.METADATA, field1="value1")
        assert msg.type == ResponseMessage.METADATA
        assert msg.status == ResponseMessage.STATUS_OK
        assert msg.field1 == "value1"

    def test_error_response_factory(self):
        """Test error_response factory method."""
        msg = ResponseMessage.error_response(type_=ResponseMessage.METADATA, field1="value1")
        assert msg.type == ResponseMessage.METADATA
        assert msg.status == ResponseMessage.STATUS_ERROR
        assert msg.field1 == "value1"

    def test_is_ok_method(self):
        """Test is_ok method."""
        msg = ResponseMessage.ok_response()
        assert msg.is_ok() is True

        msg = ResponseMessage.error_response()
        assert msg.is_ok() is False

    def test_inheritance(self):
        """Test inheritance from BaseMessage."""
        msg = ResponseMessage(type_="TEST", field1="value1")
        assert msg.field1 == "value1"
        assert msg.to_dict() == {"type": "TEST", "status": "ok", "field1": "value1"}

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = ResponseMessage.deserialize(serialized)
        assert deserialized.type == "TEST"
        assert deserialized.status == "ok"
        assert deserialized.field1 == "value1"

    def test_status_field_always_included(self):
        """Test that status field is always included in serialized message."""
        msg = ResponseMessage(type_=ResponseMessage.GENERAL)
        serialized = msg.serialize()
        deserialized_dict = json.loads(serialized.decode())
        assert "status" in deserialized_dict
        assert deserialized_dict["status"] == ResponseMessage.STATUS_OK

    def test_metadata_response(self):
        """Test creating a metadata response."""
        metadata = {
            "resolution": (1920, 1080),
            "fps": 30,
            "frames_count": 100,
            "render_resolution": (960, 540)
        }
        msg = ResponseMessage.ok_response(type_=ResponseMessage.METADATA, **metadata)
        assert msg.type == ResponseMessage.METADATA
        assert msg.status == ResponseMessage.STATUS_OK
        assert msg.resolution == (1920, 1080)
        assert msg.fps == 30
        assert msg.frames_count == 100
        assert msg.render_resolution == (960, 540)

    def test_frame_response(self):
        """Test creating a frame response."""
        frame_data = {
            "frame": "base64_encoded_frame_data",
            "shape": (1080, 1920, 3)
        }
        msg = ResponseMessage.ok_response(type_=ResponseMessage.FRAME, **frame_data)
        assert msg.type == ResponseMessage.FRAME
        assert msg.status == ResponseMessage.STATUS_OK
        assert msg.frame == "base64_encoded_frame_data"
        assert msg.shape == (1080, 1920, 3)
