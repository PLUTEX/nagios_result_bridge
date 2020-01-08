from io import BytesIO
from time import time
import pytest
import socket
import threading
import socketserver

from nagios_result_bridge import PassiveResultHandler


class Wrapper:
    def __init__(self):
        self.output = BytesIO()
        self.handler = PassiveResultHandler(self.output)
        self.server = socketserver.ThreadingTCPServer(('', 0), self.handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.output.close()

    def get_output(self, input):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(self.server.server_address)
            sock.sendall(input)
            sock.send(b'\n')
            output = sock.recv(1024)
        assert output == b''
        return self.output.getvalue()


@pytest.fixture
def wrapper():
    with Wrapper() as wrapped:
        yield wrapped


def test_binary(wrapper):
    assert wrapper.get_output(b'\xe4') == b''


def test_invalid(wrapper):
    assert wrapper.get_output(b'invalid format') == b''


def test_unauthorized(wrapper):
    line = b'[%d] PROCESS_SERVICE_CHECK_RESULT;example.org;service;0;OK\n' % time()
    assert wrapper.get_output(line) == b''


def test_success(wrapper):
    line = b'[%d] PROCESS_SERVICE_CHECK_RESULT;localhost;service;0;OK\n' % time()
    assert wrapper.get_output(line) == line
