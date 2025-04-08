from sinner.server.api.messages.NotificationMessage import NotificationMessage


class TestNotificationMessage:
    """Tests for the NotificationMessage class."""

    def test_init(self):
        """Test initialization."""
        msg = NotificationMessage(type_=NotificationMessage.NTF_FRAME, field1="value1")
        assert msg.type == NotificationMessage.NTF_FRAME
        assert msg.field1 == "value1"

    def test_class_constants(self):
        """Test class constants."""
        assert NotificationMessage.NTF_FRAME == "NTF_FRAME"

    def test_inheritance(self):
        """Test inheritance from BaseMessage."""
        msg = NotificationMessage(type_="TEST", field1="value1")
        assert msg.field1 == "value1"
        assert msg.to_dict() == {"type": "TEST", "field1": "value1"}

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = NotificationMessage.deserialize(serialized)
        assert deserialized.type == "TEST"
        assert deserialized.field1 == "value1"

    def test_frame_notification(self):
        """Test creating a frame notification."""
        msg = NotificationMessage(type_=NotificationMessage.NTF_FRAME, index=1, time=0.5, fps=30)
        assert msg.type == NotificationMessage.NTF_FRAME
        assert msg.index == 1
        assert msg.time == 0.5
        assert msg.fps == 30

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = NotificationMessage.deserialize(serialized)
        assert deserialized.type == NotificationMessage.NTF_FRAME
        assert deserialized.index == 1
        assert deserialized.time == 0.5
        assert deserialized.fps == 30
