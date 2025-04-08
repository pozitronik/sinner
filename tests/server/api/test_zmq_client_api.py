import pytest
from unittest.mock import Mock, patch
import zmq
from zmq import ZMQError
from sinner.server.api.messages.NotificationMessage import NotificationMessage
from sinner.server.api.messages.RequestMessage import RequestMessage
from sinner.server.api.messages.ResponseMessage import ResponseMessage
from sinner.server.api.ZMQClientAPI import ZMQClientAPI


class TestZMQClientAPI:
    """Tests for the ZMQClientAPI class."""

    @pytest.fixture
    def mock_zmq_context(self):
        """Mock ZMQ context and sockets."""
        with patch('zmq.Context') as mock_context:
            # Mock REQ socket
            mock_req_socket = Mock()
            mock_context.return_value.socket.return_value = mock_req_socket

            # Configure the mock socket to handle send/recv operations
            mock_req_socket.recv.return_value = ResponseMessage.ok_response().serialize()

            yield mock_context, mock_req_socket

    @pytest.fixture
    def client_api(self, mock_zmq_context):
        """Create an instance of ZMQClientAPI with mocked ZMQ."""
        _, mock_req_socket = mock_zmq_context

        # Configure successful connection response
        mock_req_socket.recv.return_value = ResponseMessage.ok_response().serialize()

        client = ZMQClientAPI(
            reply_endpoint="tcp://localhost:5555",
            sub_endpoint="tcp://localhost:5556",
            timeout=1000
        )

        yield client

        # Clean up
        client.disconnect()

    def test_init(self, mock_zmq_context):
        """Test initialization."""
        mock_context, mock_socket = mock_zmq_context

        # Test with default parameters
        client = ZMQClientAPI()
        assert client._endpoint == "tcp://127.0.0.1:5555"
        assert client._sub_endpoint == "tcp://127.0.0.1:5556"
        assert client._timeout == 5000
        assert client._connected is False
        assert client._notification_handler is None

        # Test with custom parameters
        notification_handler = Mock()
        client = ZMQClientAPI(
            notification_handler=notification_handler,
            reply_endpoint="tcp://localhost:5000",
            sub_endpoint="tcp://localhost:5001",
            timeout=2000
        )
        assert client._endpoint == "tcp://localhost:5000"
        assert client._sub_endpoint == "tcp://localhost:5001"
        assert client._timeout == 2000
        assert client._notification_handler is notification_handler

        # Verify socket initialization
        mock_context.assert_called()
        mock_context.return_value.socket.assert_called_with(zmq.REQ)
        mock_socket.setsockopt.assert_called_with(zmq.RCVTIMEO, client._timeout)

    def test_connect_success(self, client_api, mock_zmq_context):
        """Test successful connection."""
        _, mock_socket = mock_zmq_context

        # Configure mock for successful connection
        mock_socket.recv.return_value = ResponseMessage.ok_response().serialize()

        # Patch start_notification_listener to avoid actual threading
        with patch.object(client_api, 'start_notification_listener', return_value=True):
            result = client_api.connect()

            assert result is True
            assert client_api.connected is True
            mock_socket.connect.assert_called_with(client_api._endpoint)
            client_api.start_notification_listener.assert_called_once()

    def test_connect_failure_zmq_error(self, client_api, mock_zmq_context):
        """Test connection failure due to ZMQ error."""
        _, mock_socket = mock_zmq_context

        # Configure mock for connection failure
        mock_socket.connect.side_effect = ZMQError("Connection refused")

        result = client_api.connect()

        assert result is False
        assert client_api.connected is False

    def test_connect_failure_status_error(self, client_api, mock_zmq_context):
        """Test connection failure due to error status response."""
        _, mock_socket = mock_zmq_context

        # Configure mock for status error response
        mock_socket.recv.return_value = ResponseMessage.error_response().serialize()

        result = client_api.connect()

        assert result is False
        assert client_api.connected is False

    def test_disconnect(self, client_api):
        """Test disconnection."""
        # Patch methods to avoid actual threading
        with patch.object(client_api, 'stop_notification_listener') as mock_stop:
            client_api.disconnect()

            assert client_api.connected is False
            mock_stop.assert_called_once()

    def test_send_request_success(self, client_api, mock_zmq_context):
        """Test sending request with successful response."""
        _, mock_socket = mock_zmq_context

        # Configure mock for successful response
        mock_socket.recv.return_value = ResponseMessage.ok_response(field1="value1").serialize()

        request = RequestMessage(RequestMessage.GET_STATUS)
        response = client_api.send_request(request)

        assert response.is_ok() is True
        assert response.field1 == "value1"
        mock_socket.send.assert_called_with(request.serialize())

    def test_send_request_timeout(self, client_api, mock_zmq_context):
        """Test sending request with timeout."""
        _, mock_socket = mock_zmq_context

        # Configure mock for timeout
        error = ZMQError("Timeout")
        error.errno = zmq.EAGAIN
        mock_socket.send.side_effect = None
        mock_socket.recv.side_effect = error

        # Patch _recreate_socket to avoid actual recreation
        with patch.object(client_api, '_recreate_socket') as mock_recreate:
            response = client_api.send_request(RequestMessage(RequestMessage.GET_STATUS))

            assert response.is_ok() is False
            mock_recreate.assert_called_once()

    def test_send_request_zmq_error(self, client_api, mock_zmq_context):
        """Test sending request with ZMQ error."""
        _, mock_socket = mock_zmq_context

        # Configure mock for ZMQ error
        error = ZMQError("Connection lost")
        error.errno = zmq.ETERM
        mock_socket.send.side_effect = error

        # Patch _recreate_socket to avoid actual recreation
        with patch.object(client_api, '_recreate_socket') as mock_recreate:
            response = client_api.send_request(RequestMessage(RequestMessage.GET_STATUS))

            assert response.is_ok() is False
            mock_recreate.assert_called_once()

    def test_send_request_general_exception(self, client_api, mock_zmq_context):
        """Test sending request with general exception."""
        _, mock_socket = mock_zmq_context

        # Configure mock for general exception
        mock_socket.send.side_effect = Exception("Unexpected error")

        response = client_api.send_request(RequestMessage(RequestMessage.GET_STATUS))

        assert response.is_ok() is False

    def test_recreate_socket(self, client_api, mock_zmq_context):
        """Test socket recreation after error."""
        mock_context, old_socket = mock_zmq_context

        # Create a new mock for the recreated socket
        new_socket = Mock()
        mock_context.return_value.socket.return_value = new_socket

        client_api._recreate_socket()

        # Verify old socket closed and new one created
        old_socket.close.assert_called_with(linger=0)
        mock_context.return_value.socket.assert_called_with(zmq.REQ)
        new_socket.setsockopt.assert_called_with(zmq.RCVTIMEO, client_api._timeout)
        new_socket.connect.assert_called_with(client_api._endpoint)

    @patch('threading.Thread')
    def test_start_notification_listener(self, mock_thread, client_api):
        """Test starting notification listener thread."""
        # Ensure SUB socket doesn't exist
        client_api._sub_socket = None

        # Create a mock for SUB socket
        mock_sub_socket = Mock()

        # Configure context to return our mock SUB socket
        client_api._context = Mock()
        client_api._context.socket.return_value = mock_sub_socket

        result = client_api.start_notification_listener()

        assert result is True
        assert client_api._notification_running is True
        client_api._context.socket.assert_called_with(zmq.SUB)
        mock_sub_socket.setsockopt_string.assert_called_with(zmq.SUBSCRIBE, "")
        mock_sub_socket.connect.assert_called_with(client_api._sub_endpoint)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    @patch('threading.Thread')
    def test_start_notification_listener_zmq_error(self, mock_thread, client_api):
        """Test starting notification listener with ZMQ error."""
        # Ensure SUB socket doesn't exist
        client_api._sub_socket = None

        # Create a mock for SUB socket that raises error on connect
        mock_sub_socket = Mock()
        mock_sub_socket.connect.side_effect = ZMQError("Connection refused")

        # Configure context to return our mock SUB socket
        client_api._context = Mock()
        client_api._context.socket.return_value = mock_sub_socket

        result = client_api.start_notification_listener()

        assert result is False
        mock_sub_socket.close.assert_called_once()
        assert client_api._sub_socket is None
        mock_thread.assert_not_called()

    def test_stop_notification_listener(self, client_api):
        """Test stopping notification listener thread."""
        # Setup notification thread mock
        mock_thread = Mock()
        client_api._notification_thread = mock_thread
        client_api._notification_running = True

        # Store the mock socket in a local variable
        mock_socket = Mock()
        client_api._sub_socket = mock_socket

        client_api.stop_notification_listener()

        assert client_api._notification_running is False
        mock_thread.join.assert_called_with(timeout=1.0)
        mock_socket.close.assert_called_once()
        assert client_api._sub_socket is None

    def test_notification_handling(self, client_api):
        """Test handling of notifications received by the listener thread."""
        # Create a notification message
        notification = NotificationMessage(NotificationMessage.NTF_FRAME, index=1, time=0.1, fps=30)

        # Setup notification handler mock
        mock_handler = Mock()
        client_api._notification_handler = mock_handler

        # Call the handler method directly
        client_api._handle_notification(notification)

        # Verify notification handler was called with correct message
        mock_handler.assert_called_once_with(notification)

    @patch('threading.Thread')
    def test_notification_listener_thread_creation(self, mock_thread, client_api):
        """Test that the notification listener thread is created and started correctly."""
        # Mock the SUB socket
        client_api._sub_socket = Mock()
        client_api._notification_running = False

        # Call method to start listener thread
        client_api.start_notification_listener()

        # Verify thread was created with correct arguments
        mock_thread.assert_called_once_with(
            target=client_api._notification_listener,
            daemon=True
        )
        mock_thread.return_value.start.assert_called_once()
        assert client_api._notification_running is True

    def test_notification_handling_no_handler(self, client_api):
        """Test handling notifications with no handler."""
        # Create a notification message
        notification = NotificationMessage(NotificationMessage.NTF_FRAME)

        # No notification handler
        client_api._notification_handler = None

        # Call the handler method directly - should not raise exception
        client_api._handle_notification(notification)

    def test_notification_handling_exception(self, client_api):
        """Test handling notifications when the handler raises an exception."""
        # Create a notification message
        notification = NotificationMessage(NotificationMessage.NTF_FRAME)

        # Set up handler that raises an exception
        mock_handler = Mock()
        mock_handler.side_effect = Exception("Handler error")
        client_api._notification_handler = mock_handler

        # Call the handler method directly - should not raise exception
        client_api._handle_notification(notification)

        # Verify handler was called
        mock_handler.assert_called_once_with(notification)

    def test_handle_notification(self, client_api):
        """Test handle_notification method."""
        # Create a notification message
        notification = NotificationMessage(NotificationMessage.NTF_FRAME, index=1)

        # Test with handler
        mock_handler = Mock()
        client_api._notification_handler = mock_handler

        client_api._handle_notification(notification)

        mock_handler.assert_called_once_with(notification)

        # Test with handler that raises exception
        mock_handler.side_effect = Exception("Handler error")

        # Should not raise exception
        client_api._handle_notification(notification)

        # Test with no handler
        client_api._notification_handler = None

        # Should not raise exception
        client_api._handle_notification(notification)
