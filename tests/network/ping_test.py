import socket
import struct
from unittest.mock import patch, MagicMock

import pytest

from network.icmp import Ping, PingResponse


def mock_to_ip():
    """Mock hostname-to-IP conversion: always return a fixed IP address."""
    return "192.168.1.1"


def mock_calculate_checksum():
    """Mock checksum calculation: always return zero."""
    return 0


def mock_socket():
    """Mock socket returning a default empty ICMP packet."""
    mock_sock = MagicMock()
    # Simulate receiving a zeroed 28-byte packet and sender address
    mock_sock.recvfrom.return_value = (b'\x00' * 28, ('192.168.1.1', 1))
    return mock_sock


@pytest.fixture
def ping_instance():
    """Create a Ping instance with patched utilities for consistent behavior."""
    with patch("network.icmp.icmp_utils.to_ip", side_effect=mock_to_ip), \
            patch("network.icmp.icmp_utils.calculate_checksum", side_effect=mock_calculate_checksum):
        return Ping(destination="8.8.8.8", packet_size=64, timeout=1)


def mock_socket(*args, **kwargs):
    """Mock socket for successful ping response."""
    mock_sock = MagicMock()

    # Construct a correct ICMP Echo Reply packet:
    # type=0 (Echo Reply), code=0, checksum=0, identifier=1234, sequence=1
    icmp_type = 0
    icmp_code = 0
    checksum = 0
    identifier = 1234
    sequence = 1
    icmp_header = struct.pack("!BBHHH", icmp_type, icmp_code, checksum, identifier, sequence)
    icmp_payload = bytes(32)
    icmp_packet = icmp_header + icmp_payload

    # Simulate receiving the packet from the destination host
    mock_sock.recvfrom.return_value = (icmp_packet, ("8.8.8.8", 1))
    return mock_sock


def test_ping_start_success(ping_instance):
    """
    Test successful execution of Ping.start:
    - All packets sent are echoed back
    - Transmitted and received packet counts match the requested count
    """
    packet_count = 3
    with patch("socket.socket", side_effect=mock_socket), patch("time.sleep"):
        response = ping_instance.start(packet_count=packet_count)

        assert isinstance(response, PingResponse)
        assert response.transmitted_package_count == packet_count
        assert response.received_package_count == packet_count


def test_ping_packet_loss(ping_instance):
    """
    Test Ping.start handling of timeout scenarios:
    - Simulate socket.timeout on recvfrom to indicate packet loss
    - Received packet count should be zero and packet loss rate 100%
    """
    packet_count = 3
    # Patch recvfrom to always raise a timeout exception
    with patch("socket.socket.recvfrom", side_effect=socket.timeout("Timeout occurred")), \
            patch("time.sleep"):
        response = ping_instance.start(packet_count=packet_count)

        assert isinstance(response, PingResponse)
        assert response.transmitted_package_count == packet_count
        assert response.received_package_count == 0
        assert response.packet_loss_rate == 100


def test_create_packet(ping_instance):
    """
    Test internal _create_packet method:
    - Packet length equals payload size plus ICMP header (8 bytes)
    """
    sequence = 1
    expected_length = ping_instance._packet_size + 8

    packet = ping_instance._create_packet(sequence=sequence)

    assert isinstance(packet, bytes)
    assert len(packet) == expected_length
