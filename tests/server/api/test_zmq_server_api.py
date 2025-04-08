import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import zmq
from zmq import ZMQError

from sinner.server.api.messages.NotificationMessage import NotificationMessage
from sinner.server.api.messages.RequestMessage import RequestMessage
from sinner.server.api.messages.ResponseMessage import ResponseMessage
from sinner.server.api.ZMQServerAPI import ZMQServerAPI


class TestZMQServerAPI:
    """Tests for the ZMQServerAPI class."""

    @pytest.fixture
    def mock_zmq_asyncio_context(self):
        """Mock ZMQ asyncio context and socket."""
        with patch('zmq.asyncio.Context') as mock_asyncio_context:
            # Mock REP socket
            mock_rep_socket = AsyncMock()
            mock_asyncio_context.return_value.socket.return_value = mock_rep_socket

            yield mock_asyncio_context, mock_rep_socket

    @pytest.fixture
    def mock_zmq_context(self):
        """Mock regular ZMQ context and socket for publish operations."""
        with patch('zmq.Context.instance') as mock_context:
            # Mock PUB socket
            mock_pub_socket = Mock()
            mock_context.return_value.socket.return_value = mock_pub_socket

            yield mock_context, mock_pub_socket

    @pytest.fixture
    def request_handler(self):
        """Mock request handler function."""
        handler = Mock()
        handler.return_value = ResponseMessage.ok_response(message="Handled")
        return handler

    @pytest.fixture
    def server_api(self, mock_zmq_asyncio_context, mock_zmq_context, request_handler):
        """Create an instance of ZMQServerAPI with mocked ZMQ."""
        server = ZMQServerAPI(
            handler=request_handler,
            reply_endpoint="tcp://localhost:5555",
            publish_endpoint="tcp://localhost:5556",
        )

        yield server

        # Clean up
        server.stop()

    @pytest.mark.skip("Test can't be run in Github CI")
    @patch('platform.system')
    @patch('asyncio.set_event_loop_policy')
    def test_init_windows(self, mock_set_policy, mock_system, mock_zmq_asyncio_context, mock_zmq_context):
        """Test initialization on Windows platform."""
        # Mock Windows platform
        mock_system.return_value = "Windows"

        # Create server with default parameters
        ZMQServerAPI()

        # Verify event loop policy is set
        mock_set_policy.assert_called_once()

    @patch('platform.system')
    @patch('asyncio.set_event_loop_policy')
    def test_init_non_windows(self, mock_set_policy, mock_system, mock_zmq_asyncio_context, mock_zmq_context):
        """Test initialization on non-Windows platform."""
        # Mock non-Windows platform
        mock_system.return_value = "Linux"

        # Create server
        ZMQServerAPI()

        # Verify event loop policy is not set
        mock_set_policy.assert_not_called()

    def test_init(self, mock_zmq_asyncio_context, mock_zmq_context):
        """Test initialization."""
        mock_asyncio_context, mock_rep_socket = mock_zmq_asyncio_context
        mock_context, mock_pub_socket = mock_zmq_context

        # Test with default parameters
        server = ZMQServerAPI()
        assert server._reply_endpoint == "tcp://127.0.0.1:5555"
        assert server._publish_endpoint == "tcp://127.0.0.1:5556"
        assert server._request_handler is None
        assert server._server_running is False

        # Test with custom parameters
        handler = Mock()
        server = ZMQServerAPI(
            handler=handler,
            reply_endpoint="tcp://localhost:5000",
            publish_endpoint="tcp://localhost:5001",
        )
        assert server._reply_endpoint == "tcp://localhost:5000"
        assert server._publish_endpoint == "tcp://localhost:5001"
        assert server._request_handler is handler

        # Verify socket initialization
        mock_asyncio_context.assert_called()
        mock_asyncio_context.return_value.socket.assert_called_with(zmq.REP)

        mock_context.assert_called()
        mock_context.return_value.socket.assert_called_with(zmq.PUB)
        mock_pub_socket.setsockopt.assert_called_with(zmq.LINGER, 0)

    @pytest.mark.asyncio
    async def test_start_success(self):
        """Test successful server start using a simplified approach."""
        # Create mock sockets
        mock_rep_socket = AsyncMock()
        mock_pub_socket = Mock()

        # Create mocks for contexts
        mock_asyncio_context = Mock()
        mock_asyncio_context.socket.return_value = mock_rep_socket

        mock_context = Mock()
        mock_context.socket.return_value = mock_pub_socket

        # Create an async message handler that can be awaited
        async def mock_handler():
            # We'll make this exit immediately to avoid hanging
            return

        # Create a fresh server instance with our mocked contexts
        with patch('zmq.asyncio.Context', return_value=mock_asyncio_context), \
                patch('zmq.Context.instance', return_value=mock_context), \
                patch('platform.system', return_value='Linux'):
            server = ZMQServerAPI()
            server._message_handler = mock_handler

            # Test the start method
            result = await server.start()

            assert result is True
            assert server._server_running is True
            mock_rep_socket.bind.assert_called_once()
            mock_pub_socket.bind.assert_called_once()

    def test_stop(self, server_api, mock_zmq_asyncio_context, mock_zmq_context):
        """Test server stop."""
        _, mock_rep_socket = mock_zmq_asyncio_context
        _, mock_pub_socket = mock_zmq_context

        # Set server as running
        server_api._server_running = True

        server_api.stop()

        assert server_api._server_running is False
        mock_rep_socket.close.assert_called_once()
        mock_pub_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_handler_simple_message(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with simple message (no payload)."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to return one message then exit
        request = RequestMessage(RequestMessage.GET_STATUS)
        mock_rep_socket.recv_multipart.side_effect = [
            [request.serialize()],  # First call returns a single-part message
            ZMQError("Server stopped")  # Second call raises error to exit loop
        ]

        # Set up handler to return success response
        response = ResponseMessage.ok_response(message="Status OK")
        server_api._request_handler.return_value = response

        # Set server as running, then stop after handling message
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler process one message
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # Verify handler called and response sent
        server_api._request_handler.assert_called_once()
        mock_rep_socket.send.assert_awaited_once_with(response.serialize())

    @pytest.mark.skip("Tested API isn't implemented")
    @pytest.mark.asyncio
    async def test_message_handler_binary_message(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with binary message (with payload)."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to return one binary message then exit
        request = RequestMessage(RequestMessage.SET_SOURCE_FILE, filename="test.jpg")
        payload = b"binary file content"
        mock_rep_socket.recv_multipart.side_effect = [
            [request.serialize(), payload],  # Binary message with two parts
            ZMQError("Server stopped")  # Exit loop
        ]

        # Set up handler to return success response
        response = ResponseMessage.ok_response(message="File received")
        server_api._request_handler.return_value = response

        # Set server as running, then stop after handling message
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler process one message
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # Verify handler called with request and payload
        server_api._request_handler.assert_called_once_with(request, payload)
        mock_rep_socket.send.assert_awaited_once_with(response.serialize())

    @pytest.mark.asyncio
    async def test_message_handler_invalid_format(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with invalid message format."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to return invalid message then exit
        mock_rep_socket.recv_multipart.side_effect = [
            [b"part1", b"part2", b"part3"],  # Invalid format (3 parts)
            ZMQError("Server stopped")  # Exit loop
        ]

        # Set server as running, then stop after handling message
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler process one message
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # Verify error response sent
        sent_response = ResponseMessage.deserialize(mock_rep_socket.send.call_args[0][0])
        assert sent_response.status == ResponseMessage.STATUS_ERROR
        assert "Invalid message format" in sent_response.message

    @pytest.mark.asyncio
    async def test_message_handler_zmq_error_timeout(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with ZMQ timeout error."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to raise ZMQ timeout error then exit
        error = ZMQError("Timeout")
        error.errno = zmq.EAGAIN
        mock_rep_socket.recv_multipart.side_effect = [
            error,  # Timeout error
            ZMQError("Server stopped")  # Exit loop
        ]

        # Set server as running, then stop after handling error
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler handle one error
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # Verify sleep was called for timeout error
        # No assertions needed - we just verify it doesn't crash

    @pytest.mark.asyncio
    async def test_message_handler_zmq_error_other(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with other ZMQ error."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to raise ZMQ error then exit
        error = ZMQError("Connection lost")
        error.errno = zmq.ETERM
        mock_rep_socket.recv_multipart.side_effect = [
            error,  # ZMQ error
            ZMQError("Server stopped")  # Exit loop
        ]

        # Set server as running, then stop after handling error
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler handle one error
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # No assertions needed - we just verify it doesn't crash

    @pytest.mark.asyncio
    async def test_message_handler_general_exception(self, server_api, mock_zmq_asyncio_context):
        """Test message handler with general exception."""
        _, mock_rep_socket = mock_zmq_asyncio_context

        # Configure mock to raise exception then exit
        mock_rep_socket.recv_multipart.side_effect = [
            Exception("Unexpected error"),  # General exception
            ZMQError("Server stopped")  # Exit loop
        ]

        # Set server as running, then stop after handling error
        server_api._server_running = True

        async def stop_server():
            await asyncio.sleep(0.1)  # Let message handler handle one error
            server_api._server_running = False

        # Run message handler in background
        asyncio.create_task(stop_server())
        await server_api._message_handler()

        # No assertions needed - we just verify it doesn't crash

    def test_notify(self, server_api, mock_zmq_context):
        """Test notification sending."""
        _, mock_pub_socket = mock_zmq_context

        # Create notification
        notification = NotificationMessage(NotificationMessage.NTF_FRAME, index=1, time=0.1, fps=30)

        # Send notification
        server_api.notify(notification)

        # Verify notification sent
        mock_pub_socket.send.assert_called_once_with(notification.serialize(), zmq.NOBLOCK)

    def test_notify_error(self, server_api, mock_zmq_context):
        """Test notification sending with error."""
        _, mock_pub_socket = mock_zmq_context

        # Configure mock to raise exception
        mock_pub_socket.send.side_effect = Exception("Send error")

        # Create notification
        notification = NotificationMessage(NotificationMessage.NTF_FRAME)

        # Send notification - should not raise exception
        server_api.notify(notification)

    def test_handle_request_no_handler(self, server_api):
        """Test handle_request with no handler."""
        # Clear handler
        server_api._request_handler = None

        # Create request
        request = RequestMessage(RequestMessage.GET_STATUS)

        # Handle request
        response = server_api._handle_request(request)

        # Verify error response
        assert response.status == ResponseMessage.STATUS_ERROR
        assert "Handler is not defined" in response.message

    def test_handle_request_with_handler(self, server_api, request_handler):
        """Test handle_request with handler."""
        # Create request
        request = RequestMessage(RequestMessage.GET_STATUS)

        # Expected response
        expected_response = ResponseMessage.ok_response(message="Handled")
        request_handler.return_value = expected_response

        # Handle request
        response = server_api._handle_request(request)

        # Verify handler called and response returned
        request_handler.assert_called_once_with(request, None)
        assert response is expected_response

    def test_handle_request_with_payload(self, server_api, request_handler):
        """Test handle_request with payload."""
        # Create request and payload
        request = RequestMessage(RequestMessage.SET_SOURCE_FILE)
        payload = b"binary data"

        # Expected response
        expected_response = ResponseMessage.ok_response(message="File handled")
        request_handler.return_value = expected_response

        # Handle request
        response = server_api._handle_request(request, payload)

        # Verify handler called with payload and response returned
        request_handler.assert_called_once_with(request, payload)
        assert response is expected_response
