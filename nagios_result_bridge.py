import re
import socket
import socketserver
import logging


logger = logging.getLogger(__name__)


class PassiveResultHandler(socketserver.StreamRequestHandler):
    COMMAND_REGEXP = re.compile(r'''(?x)
        ^
        \[(?P<time>\d+)\]
        \s
        PROCESS_SERVICE_CHECK_RESULT
        ;
        (?P<host_name>[a-zA-Z0-9\.-]+)
        ;
        (?P<service_description>[a-zA-Z0-9\. -]+)
        ;
        (?P<return_code>[0123])
        ;
        (?P<plugin_output>.+)
        $
    ''')

    def __init__(self, cmdfile):
        self.cmdfile = cmdfile
        logger.debug('%s initialized', self.__class__.__name__)

    def __call__(self, *args):
        super().__init__(*args)

    def _log(self, msg, *args, extra={}, level='info'):
        getattr(logger, level)(
            'Client %s ' + msg,
            self.client_address[0],
            *args,
            extra={'CLIENT': self.client_address[0], **extra},
        )

    def handle(self):
        try:
            data = self.rfile.readline().decode('UTF-8')
        except UnicodeError:
            self._log('sent invalid UTF-8')
            return

        match = self.COMMAND_REGEXP.match(data)
        if not match:
            self._log(
                'sent garbage: %r',
                data[:256],
                extra={'DATA': data},
            )
            return

        try:
            valid_addresses = socket.getaddrinfo(match['host_name'], None)
        except socket.gaierror:
            valid_addresses = ()

        for valid_address in valid_addresses:
            if valid_address[4][0] == self.client_address[0]:
                break
        else:
            self._log(
                'not authorized for host %s',
                match['host_name'],
                extra={'HOST_NAME': match['host_name']},
            )
            return

        self._log(
            'passed validation for host %s, passing message',
            match['host_name'],
            extra={k.upper(): v for k, v in match.groupdict().items()},
            level='debug',
        )
        self.cmdfile.write(data)
        print('written')

    def finish(self):
        super().finish()
        self.connection.close()
        self._log('socket closed')


def start_listening(port, cmdfile):
    handler = PassiveResultHandler(cmdfile)
    with socketserver.ThreadingTCPServer(('', port), handler) as server:
        server.serve_forever()
