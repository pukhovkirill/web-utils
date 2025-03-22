import socket
import pytest
from unittest.mock import patch, MagicMock
from network import Ping, Response


def mock_to_ip():
    return "192.168.1.1"


def mock_calculate_checksum():
    return 0


def mock_socket():
    mock_sock = MagicMock()
    mock_sock.recvfrom.return_value = (b'\x00' * 28, ('192.168.1.1', 1))
    return mock_sock


@pytest.fixture
def ping_instance():
    with patch("network.icmp.ping_utils.to_ip", side_effect=mock_to_ip), \
            patch("network.icmp.ping_utils.calculate_checksum", side_effect=mock_calculate_checksum):
        return Ping(destination="example.com", packet_size=64, timeout=1)


def test_ping_init(ping_instance):
    # Arrange
    expected_destination = "example.com"
    expected_packet_size = 64
    expected_timeout = 1

    # Act & Assert
    assert ping_instance._destination == expected_destination
    assert ping_instance._packet_size == expected_packet_size
    assert ping_instance._timeout == expected_timeout


def test_ping_start_success(ping_instance):
    # Arrange
    packet_count = 3
    with patch("socket.socket", side_effect=mock_socket):
        # Act
        response = ping_instance.start(packet_count=packet_count)

        # Assert
        assert isinstance(response, Response)


def test_ping_packet_loss(ping_instance):
    # Arrange
    packet_count = 3
    with patch("socket.socket", side_effect=mock_socket) as mock_sock:
        mock_sock.return_value.recvfrom.side_effect = socket.timeout

        # Act
        response = ping_instance.start(packet_count=packet_count)

        # Assert
        assert response.received_package_count == 0
        assert response.packet_loss_rate == 100


def test_create_packet(ping_instance):
    # Arrange
    sequence = 1
    expected_length = ping_instance._packet_size + 8

    # Act
    packet = ping_instance._create_packet(sequence=sequence)

    # Assert
    assert isinstance(packet, bytes)
    assert len(packet) == expected_length
