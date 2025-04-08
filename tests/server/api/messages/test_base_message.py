import pytest
import json
from sinner.server.api.messages.BaseMessage import BaseMessage


class TestBaseMessage:
    """Tests for the BaseMessage abstract base class."""

    def test_init(self):
        """Test initialization with type and additional fields."""
        msg = BaseMessage(type_="TEST", field1="value1", field2=123)
        assert msg.type == "TEST"
        assert msg.field1 == "value1"
        assert msg.field2 == 123

    def test_getattr(self):
        """Test attribute access for fields."""
        msg = BaseMessage(type_="TEST", field1="value1")
        assert msg.field1 == "value1"

        # Test accessing non-existent attribute
        with pytest.raises(AttributeError):
            _ = msg.non_existent_field

    def test_setattr(self):
        """Test setting fields via attributes."""
        msg = BaseMessage(type_="TEST")
        msg.field1 = "value1"
        assert msg.field1 == "value1"

        # Test setting internal attribute
        msg._internal = "internal"
        assert msg._internal == "internal"

    def test_getitem(self):
        """Test dictionary-style access."""
        msg = BaseMessage(type_="TEST", field1="value1")
        assert msg["field1"] == "value1"

        # Test accessing non-existent key
        assert msg["non_existent_field"] is None

    def test_setitem(self):
        """Test dictionary-style assignment."""
        msg = BaseMessage(type_="TEST")
        msg["field1"] = "value1"
        assert msg.field1 == "value1"

    def test_type_property(self):
        """Test type property."""
        msg = BaseMessage(type_="TEST")
        assert msg.type == "TEST"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        msg = BaseMessage(type_="TEST", field1="value1", field2=123)
        result = msg.to_dict()
        assert result == {"type": "TEST", "field1": "value1", "field2": 123}

    def test_to_json(self):
        """Test serialization to JSON."""
        msg = BaseMessage(type_="TEST", field1="value1", field2=123)
        json_str = msg.to_json()
        # Parse the JSON string back to a dictionary for comparison
        result = json.loads(json_str)
        assert result == {"type": "TEST", "field1": "value1", "field2": 123}

    def test_from_json(self):
        """Test deserialization from JSON."""
        json_str = '{"type": "TEST", "field1": "value1", "field2": 123}'
        msg = BaseMessage.from_json(json_str)
        assert msg.type == "TEST"
        assert msg.field1 == "value1"
        assert msg.field2 == 123

    def test_from_json_missing_type(self):
        """Test deserialization from JSON with missing type."""
        json_str = '{"field1": "value1", "field2": 123}'
        with pytest.raises(TypeError, match="Type is not defined in JSON message"):
            BaseMessage.from_json(json_str)

    def test_from_json_invalid_json(self):
        """Test deserialization from invalid JSON."""
        json_str = '{invalid json'
        with pytest.raises(ValueError, match="Invalid JSON format"):
            BaseMessage.from_json(json_str)

    def test_serialize(self):
        """Test serialization to bytes."""
        msg = BaseMessage(type_="TEST", field1="value1")
        serialized = msg.serialize()
        assert isinstance(serialized, bytes)
        # The order of keys in the JSON string is not guaranteed
        assert json.loads(serialized.decode()) == {"type": "TEST", "field1": "value1"}

    def test_deserialize(self):
        """Test deserialization from bytes."""
        serialized = b'{"type": "TEST", "field1": "value1"}'
        msg = BaseMessage.deserialize(serialized)
        assert msg.type == "TEST"
        assert msg.field1 == "value1"

    def test_deserialize_invalid_encoding(self):
        """Test deserialization from bytes with invalid encoding."""
        # Create invalid UTF-8 bytes
        serialized = b'\xff\xfe' + b'{"type": "TEST"}'
        with pytest.raises(ValueError, match="Invalid message encoding"):
            BaseMessage.deserialize(serialized)

    def test_empty_type(self):
        """Test with empty type."""
        msg = BaseMessage(type_="")
        assert msg.type == ""

    def test_unicode_characters(self):
        """Test with Unicode characters."""
        msg = BaseMessage(type_="TEST", field="привет мир")
        serialized = msg.serialize()
        deserialized = BaseMessage.deserialize(serialized)
        assert deserialized.field == "привет мир"

    def test_large_message(self):
        """Test with a large message."""
        large_data = {"key" + str(i): "value" + str(i) for i in range(100)}
        msg = BaseMessage(type_="TEST", **large_data)
        serialized = msg.serialize()
        deserialized = BaseMessage.deserialize(serialized)
        assert deserialized.to_dict() == {**large_data, "type": "TEST"}

    def test_binary_data(self):
        """Test with binary data (encoded as hex string for JSON compatibility)."""
        binary_data = b'\x00\x01\x02\x03'
        msg = BaseMessage(type_="TEST", binary=binary_data.hex())
        serialized = msg.serialize()
        deserialized = BaseMessage.deserialize(serialized)
        assert bytes.fromhex(deserialized.binary) == binary_data

    def test_complex_data_types(self):
        """Test with complex data types (lists, dicts, nested structures)."""
        complex_data = {
            "list_field": [1, 2, 3],
            "dict_field": {"key1": "value1", "key2": 2},
            "nested_list": [[1, 2], [3, 4]],
            "nested_dict": {"subdict": {"key": "value"}}
        }

        msg = BaseMessage(type_="TEST", **complex_data)

        # Test attribute access
        assert msg.list_field == [1, 2, 3]
        assert msg.dict_field == {"key1": "value1", "key2": 2}

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = BaseMessage.deserialize(serialized)

        assert deserialized.list_field == [1, 2, 3]
        assert deserialized.dict_field == {"key1": "value1", "key2": 2}
        assert deserialized.nested_list == [[1, 2], [3, 4]]
        assert deserialized.nested_dict == {"subdict": {"key": "value"}}

    @pytest.mark.parametrize("field_value", [
        "string value",
        123,
        123.45,
        True,
        False,
        None,
        [1, 2, 3],
        {"key": "value"}
    ])
    def test_field_value_types(self, field_value):
        """Test with different types of field values."""
        msg = BaseMessage(type_="TEST", field=field_value)
        assert msg.field == field_value

        # Test serialization/deserialization
        serialized = msg.serialize()
        deserialized = BaseMessage.deserialize(serialized)
        assert deserialized.field == field_value

    def test_update_field(self):
        """Test updating a field value."""
        msg = BaseMessage(type_="TEST", field="value1")
        assert msg.field == "value1"

        msg.field = "value2"
        assert msg.field == "value2"

    def test_field_name_collision(self):
        """Test setting a field with name that matches a method."""
        msg = BaseMessage(type_="TEST", to_dict="collision")
        # The method should still be accessible
        assert callable(msg.to_dict)
        # The field should be accessible via dict-style access
        assert msg["to_dict"] == "collision"
        # And the field should be included in the serialized form
        serialized = msg.serialize()
        deserialized_dict = json.loads(serialized.decode())
        assert deserialized_dict["to_dict"] == "collision"
