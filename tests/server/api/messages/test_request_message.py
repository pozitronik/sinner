from sinner.server.api.messages.RequestMessage import RequestMessage


class TestRequestMessage:
    """Tests for the RequestMessage class."""

    def test_init(self):
        """Test initialization."""
        msg = RequestMessage(type_=RequestMessage.GET_STATUS, field1="value1")
        assert msg.type == RequestMessage.GET_STATUS
        assert msg.field1 == "value1"

    def test_class_constants(self):
        """Test class constants."""
        assert RequestMessage.GET_STATUS == "GET_STATUS"
        assert RequestMessage.GET_SOURCE == "GET_SOURCE"
        assert RequestMessage.SET_SOURCE == "SET_SOURCE"
        assert RequestMessage.GET_TARGET == "GET_TARGET"
        assert RequestMessage.SET_TARGET == "SET_TARGET"
        assert RequestMessage.GET_QUALITY == "GET_QUALITY"
        assert RequestMessage.SET_QUALITY == "SET_QUALITY"
        assert RequestMessage.GET_POSITION == "GET_POSITION"
        assert RequestMessage.SET_POSITION == "SET_POSITION"
        assert RequestMessage.GET_FRAME == "GET_FRAME"
        assert RequestMessage.GET_METADATA == "GET_METADATA"
        assert RequestMessage.SET_SOURCE_FILE == "SET_SOURCE_FILE"
        assert RequestMessage.SET_TARGET_FILE == "SET_TARGET_FILE"
        assert RequestMessage.CMD_START_PROCESSING == "CMD_START_PROCESSING"
        assert RequestMessage.CMD_STOP_PROCESSING == "CMD_STOP_PROCESSING"
        assert RequestMessage.CMD_FRAME_PROCESSED == "CMD_FRAME_PROCESSED"

    def test_inheritance(self):
        """Test inheritance from BaseMessage."""
        msg = RequestMessage(type_="TEST", field1="value1")
        assert msg.field1 == "value1"
        assert msg.to_dict() == {"type": "TEST", "field1": "value1"}

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = RequestMessage.deserialize(serialized)
        assert deserialized.type == "TEST"
        assert deserialized.field1 == "value1"

    def test_get_status_request(self):
        """Test GET_STATUS request."""
        msg = RequestMessage(RequestMessage.GET_STATUS)
        assert msg.type == RequestMessage.GET_STATUS

    def test_set_source_request(self):
        """Test SET_SOURCE request."""
        msg = RequestMessage(RequestMessage.SET_SOURCE, source_path="/path/to/source")
        assert msg.type == RequestMessage.SET_SOURCE
        assert msg.source_path == "/path/to/source"

    def test_set_target_request(self):
        """Test SET_TARGET request."""
        msg = RequestMessage(RequestMessage.SET_TARGET, target_path="/path/to/target")
        assert msg.type == RequestMessage.SET_TARGET
        assert msg.target_path == "/path/to/target"

    def test_set_position_request(self):
        """Test SET_POSITION request."""
        msg = RequestMessage(RequestMessage.SET_POSITION, position=42)
        assert msg.type == RequestMessage.SET_POSITION
        assert msg.position == 42

    def test_get_frame_request(self):
        """Test GET_FRAME request."""
        msg = RequestMessage(RequestMessage.GET_FRAME, position=42)
        assert msg.type == RequestMessage.GET_FRAME
        assert msg.position == 42

    def test_frame_processed_request(self):
        """Test CMD_FRAME_PROCESSED request."""
        msg = RequestMessage(RequestMessage.CMD_FRAME_PROCESSED, position=42)
        assert msg.type == RequestMessage.CMD_FRAME_PROCESSED
        assert msg.position == 42
