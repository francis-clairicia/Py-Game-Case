# -*- coding: Utf-8 -*

import socket
import select
import struct
import pickle
from typing import Any, Optional
from .thread import threaded_function
from .clock import Clock

STRUCT_FORMAT_PREFIX = ">I"
STRUCT_FORMAT_SIZE = struct.calcsize(STRUCT_FORMAT_PREFIX)
QUIT = "quit"

def recv_data(socket_obj: socket.socket) -> bytes:
    try:
        recv_size = struct.unpack(STRUCT_FORMAT_PREFIX, socket_obj.recv(STRUCT_FORMAT_SIZE))[0]
        data = socket_obj.recv(recv_size)
    except:
        data = None
    return data

def send_data(socket_obj: socket.socket, data: bytes) -> None:
    try:
        packed_data = struct.pack(STRUCT_FORMAT_PREFIX, len(data)) + data
        socket_obj.sendall(packed_data)
    except:
        pass

class ServerSocket:

    def __init__(self):
        self.__thread = None
        self.__port = -1
        self.__listen = 0
        self.__socket = None
        self.__clients = list()
        self.__loop = False

    def __del__(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return isinstance(self.__socket, socket.socket)

    def bind(self, port: int, listen: int) -> None:
        self.stop()
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.bind(("", port))
        except:
            self.__socket = None
        else:
            self.__port = port
        self.listen = listen
        self.__thread = self.__run()

    @property
    def ip(self) -> str:
        return socket.gethostbyname(socket.gethostname())

    @property
    def port(self) -> int:
        return self.__port

    @property
    def listen(self) -> int:
        return self.__listen

    @listen.setter
    def listen(self, value: int) -> int:
        self.__listen = abs(int(value))
        if self.connected():
            self.__socket.listen(self.__listen)

    @property
    def clients(self) -> list[socket.socket]:
        return self.__clients

    @threaded_function
    def __run(self) -> None:
        if not self.connected():
            return
        self.__loop = True
        while self.__loop:
            self.__check_for_connections()
            data_recieved = list()
            for client in self.__clients_to_read():
                data = recv_data(client)
                if isinstance(data, bytes):
                    try:
                        unpickled_data = pickle.loads(data)
                        if not isinstance(unpickled_data, dict):
                            raise TypeError
                    except:
                        pass
                    else:
                        for msg, data in unpickled_data.items():
                            print("Server - Recieved from {}: {}".format(client.getpeername(), {msg: data}))
                            data_recieved.append((client, msg, data))
            self.handler(data_recieved.copy())
            self.__check_for_disconnected_clients(data_recieved)
        for client in self.clients:
            client.close()
        self.clients.clear()
        self.__socket.close()
        self.__socket = None
        self.__port = -1

    def handler(self, data_recieved: list[tuple[socket.socket, str, dict]]) -> None:
        for client_who_send, msg, data in data_recieved:
            self.send_to_all_clients(msg, data, filter_function=lambda client: client != client_who_send)

    def __check_for_disconnected_clients(self, data_recieved: list[tuple[socket.socket, str, dict]]) -> None:
        # pylint: disable=unused-variable
        for client_who_send, msg, data in data_recieved:
            if msg == QUIT:
                print(f"{client_who_send.getpeername()} disconnected")
                client_who_send.close()
                self.__clients.remove(client_who_send)

    def stop(self) -> None:
        if self.__loop:
            self.__loop = False
            self.__thread.join()
            self.__thread = None

    def __check_for_connections(self) -> None:
        try:
            connections = select.select([self.__socket], [], [], 0.05)[0]
        except:
            connections = list()
        for client in [connection.accept()[0] for connection in connections]:
            self.new_client_connected(client)
            self.clients.append(client)

    def __clients_to_read(self) -> list[socket.socket]:
        try:
            clients_to_read = select.select(self.clients, [], [], 0.05)[0]
        except:
            clients_to_read = list()
        return clients_to_read

    def send_to(self, client: socket.socket, msg: str, data: Optional[Any] = None) -> None:
        if self.connected():
            data_dict = {str(msg): data}
            print(f"Server - Sending {data_dict} to {client.getpeername()}")
            send_data(client, pickle.dumps(data_dict))

    def send_to_all_clients(self, msg: str, data: Optional[Any] = None, filter_function=None) -> None:
        for client in filter(filter_function, self.clients):
            self.send_to(client, msg, data)

    def new_client_connected(self, client: socket.socket) -> None:
        pass

class ClientSocket:

    QUIT_MESSAGE = QUIT

    def __init__(self):
        self.__thread = None
        self.__socket = None
        self.__loop = False
        self.__msg = dict()
        self.__timeout_clock = Clock()

    def __del__(self) -> None:
        self.stop()

    def connected(self) -> bool:
        return isinstance(self.__socket, socket.socket)

    def connect(self, server_address: str, server_port: int, timeout: int) -> bool:
        self.stop()
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout(timeout)
            self.__socket.connect((server_address, server_port))
            self.__socket.settimeout(None)
        except:
            self.__socket = None
        self.__thread = self.__run()
        return self.connected()

    @threaded_function
    def __run(self) -> None:
        if not self.connected():
            return
        self.__loop = True
        while self.__loop:
            try:
                read_socket = bool(len(select.select([self.__socket], [], [], 0.05)[0]) > 0)
            except:
                read_socket = False
            if not read_socket:
                continue
            try:
                data = recv_data(self.__socket)
                msg = pickle.loads(data) if isinstance(data, bytes) else None
            except:
                msg = None
            if not isinstance(msg, dict):
                continue
            print(f"Client - Recieved {msg}")
            self.__msg |= msg
        self.__socket.close()
        self.__socket = None

    def stop(self) -> None:
        if self.__loop:
            self.send(ClientSocket.QUIT_MESSAGE)
            self.__loop = False
            self.__thread.join()
            self.__thread = None

    def send(self, msg: str, data: Optional[Any] = None) -> None:
        if self.connected():
            data_dict = {str(msg): data}
            print(f"Client - Sending {data_dict}")
            send_data(self.__socket, pickle.dumps(data_dict))

    def recv(self, msg: str) -> bool:
        recieved = bool(msg in self.__msg)
        if recieved and self.__msg[msg] is None:
            self.__msg.pop(msg)
        return recieved

    def get(self, msg: str) -> Any:
        return self.__msg.pop(msg, None)

    def wait_for(self, *messages: str, timeout=1) -> str:
        self.__timeout_clock.restart()
        while self.connected() and not self.recv(ClientSocket.QUIT_MESSAGE) and not self.__timeout_clock.elapsed_time(timeout * 1000):
            for msg in messages:
                if self.recv(msg):
                    return msg
        if self.connected():
            self.__msg[ClientSocket.QUIT_MESSAGE] = None
        return ClientSocket.QUIT_MESSAGE
