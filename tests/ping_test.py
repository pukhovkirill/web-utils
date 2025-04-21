import socket
import struct
import pytest
from unittest.mock import patch, MagicMock
from network.icmp import Ping, PingResponse


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
    with patch("network.icmp.icmp_utils.to_ip", side_effect=mock_to_ip), \
            patch("network.icmp.icmp_utils.calculate_checksum", side_effect=mock_calculate_checksum):
        return Ping(destination="8.8.8.8", packet_size=64, timeout=1)


def mock_socket(*args, **kwargs):
    """Mock socket for successful ping response."""
    mock_sock = MagicMock()

    # Correct ICMP Echo Reply (тип 0, код 0, идентификатор = 1234, seq = 1)
    icmp_type = 0
    icmp_code = 0
    checksum = 0
    identifier = 1234
    sequence = 1
    icmp_header = struct.pack("!BBHHH", icmp_type, icmp_code, checksum, identifier, sequence)
    icmp_payload = bytes(32)
    icmp_packet = icmp_header + icmp_payload

    mock_sock.recvfrom.return_value = (icmp_packet, ("8.8.8.8", 1))

    return mock_sock


def test_ping_start_success(ping_instance):
    # Arrange
    packet_count = 3

    with patch("socket.socket", side_effect=mock_socket), patch("time.sleep"):
        # Act
        response = ping_instance.start(packet_count=packet_count)

        # Assert
        assert isinstance(response, PingResponse)
        assert response.transmitted_package_count == packet_count
        assert response.received_package_count == packet_count


def test_ping_packet_loss(ping_instance):
    packet_count = 3

    with patch("socket.socket.recvfrom", side_effect=socket.timeout("Timeout occurred")), patch("time.sleep"):
        response = ping_instance.start(packet_count=packet_count)

        assert isinstance(response, PingResponse)
        assert response.transmitted_package_count == packet_count
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
