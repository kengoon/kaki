import contextlib
import os
import socket
import select
import pickle
from threading import Thread
from time import sleep

from kivy import Logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import logging

logging.getLogger("watchdog").setLevel(logging.INFO)

# --------Binary File Checker----------#

text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
is_binary = lambda byte: bool(byte.translate(None, text_chars))

# --------Binary File Checker----------#


class KivyFileListener(FileSystemEventHandler):
    def __init__(self):
        self.server = KivyLiveServer()
        self.filepath = ""

    def on_any_event(self, event):
        pass

    def on_modified(self, event):
        src_path = event.src_path
        if event.is_directory or src_path.endswith("~") or "__pycache__" in src_path:
            return
        filename = os.path.relpath(event.src_path)
        folder = filename.split("/")[0]
        if folder in [".venv", "venv", ".buildozer", "bin", ".idea", ".git"]:
            return
        binary = is_binary(open(filename, "rb").read(1024))
        with open(filename, "rb" if binary else "r") as file:
            code_data = pickle.dumps({"file": filename, "code": file.read()})
            self.server.broadcast_new_code(
                f"{len(code_data):<{self.server.HEADER_LENGTH}}".encode("utf-8") + code_data,
            )

    def on_created(self, event):
        pass

    def on_closed(self, event):
        pass

    def on_moved(self, event):
        pass

    def on_deleted(self, event):
        pass


class KivyLiveServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", 5567))
        Logger.info(f"Server: Running on {self.server_socket.getsockname()}")
        self.server_socket.listen()
        self.socket_list = [self.server_socket]
        # Create a dummy socket pair
        self.stop_socket_r, self.stop_socket_w = socket.socketpair()
        self.socket_list.append(self.stop_socket_r)  # Add the reader socket to break select()
        self.kill_server = False
        self.client = {}
        self.HEADER_LENGTH = 64
        self.thread = Thread(target=self.run_server)
        self.thread.start()
        # Thread(target=self.recv_msg).start()

    def broadcast_new_code(self, code_message):
        for clients in self.client:
            self.client[clients].send(code_message)

    def recv_msg(self, client_socket, client_address):
        while True:
            message = client_socket.recv(self.HEADER_LENGTH)
            if len(message) == 0:
                self.clean(client_socket, client_address)
                break

    def recv_conn(self):
        read_socket, _, exception_sockets = select.select(self.socket_list, [], self.socket_list)
        for notified_socket in read_socket:
            if notified_socket == self.server_socket:
                client_socket, client_address = self.server_socket.accept()
                Logger.info(f"NEW CONNECTION: [IP] {client_address[0]}, [PORT] {client_address[1]}")
                self.socket_list.append(client_socket)
                # client_socket.close()
                self.client.update({f"{client_address[0]}:{client_address[1]}": client_socket})
                Thread(target=self.recv_msg, args=(client_socket, client_address)).start()
            elif notified_socket is self.stop_socket_r:
                # Stop signal received, exit loop
                return

    def clean(self, client_socket, address):
        Logger.info(f"CONNECTION CLOSED: {address[0]}:{address[1]}")
        self.socket_list.remove(client_socket)
        try:
            self.client.pop(f"{address[0]}:{address[1]}")
        except KeyError:
            self.client.pop(address)
        client_socket.close()

    def clean_all(self):
        with contextlib.suppress(ValueError):
            address, client_sockets = self.client.keys(), self.client.values()
            for client, address, process in zip(client_sockets, address):
                self.clean(client, address)
        self.server_socket.close()

    def run_server(self):
        try:
            while not self.kill_server:
                self.recv_conn()
        except KeyboardInterrupt:
            self.clean_all()

    def stop_server(self):
        self.kill_server = True
        self.stop_socket_w.send(b"STOP")  # Send stop signal to break select()


if __name__ == "__main__":
    handler = KivyFileListener()
    observer = Observer()
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        handler.server.stop_server()
        observer.stop()
    observer.join()
