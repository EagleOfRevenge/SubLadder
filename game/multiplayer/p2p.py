"""
p2p.py — Sub Ladder v6.0+
Peer-to-peer session handling for local/LAN multiplayer.
One player hosts, others connect directly.
"""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Dict, List, Optional


def _encode_message(payload: Dict[str, Any]) -> bytes:
    """Encode a JSON payload as a single newline-delimited message."""
    return (json.dumps(payload) + "\n").encode("utf-8")


class P2PSessionHost:
    """Minimal local P2P host for a Sub Ladder LAN session.

    The implementation uses a simple JSON-over-TCP protocol. The host keeps a
    listening socket, accepts join requests from clients, broadcasts round
    state, records answers, and determines a winner from the submitted answers.
    """

    def __init__(self, host_ip: str = "127.0.0.1", port: int = 0) -> None:
        self.host_ip = host_ip
        self.port = port
        self._server_socket: Optional[socket.socket] = None
        self._accept_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._clients: Dict[str, socket.socket] = {}
        self._lock = threading.Lock()
        self._answers: List[Dict[str, Any]] = []
        self._session: Dict[str, Any] = {
            "question_id": None,
            "question_index": None,
            "timer": None,
        }

    def start(self) -> "P2PSessionHost":
        """Open a listening socket and accept incoming client connections."""
        if self._server_socket is not None:
            return self

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host_ip, self.port))
        server.listen(8)
        server.settimeout(0.25)

        self._server_socket = server
        self.port = server.getsockname()[1]
        self._stop_event.clear()

        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        return self

    def create_session(self, question_id: int, timer: int, question_index: Optional[int] = None) -> Dict[str, Any]:
        """Create or update the current round session details."""
        with self._lock:
            self._session = {
                "question_id": question_id,
                "question_index": question_index,
                "timer": timer,
            }

        return {
            "status": "hosting",
            "host_ip": self.host_ip,
            "port": self.port,
            "question_id": question_id,
            "question_index": question_index,
            "timer": timer,
        }

    def sync_round(self, question_id: int, timer: int, question_index: Optional[int] = None) -> Dict[str, Any]:
        """Synchronise the round across all connected players."""
        payload = {
            "type": "sync_round",
            "question_id": question_id,
            "question_index": question_index,
            "timer": timer,
        }
        self._broadcast(payload)

        with self._lock:
            self._session = {
                "question_id": question_id,
                "question_index": question_index,
                "timer": timer,
            }

        return {
            "status": "synced",
            "question_id": question_id,
            "question_index": question_index,
            "timer": timer,
            "players": list(self._clients.keys()),
        }

    def register_answer(self, player_name: str, level: int, time_taken: float) -> Dict[str, Any]:
        """Record a submitted answer from a connected player."""
        entry = {
            "player_name": player_name,
            "level": level,
            "time_taken": float(time_taken),
        }
        with self._lock:
            self._answers.append(entry)

        return {
            "status": "recorded",
            "player_name": player_name,
            "level": level,
            "time_taken": time_taken,
        }

    def determine_winner(self) -> Dict[str, Any]:
        """Return the winning answer. Tiebreakers use highest level, then fastest time."""
        with self._lock:
            if not self._answers:
                return {"status": "no_answers"}

            sorted_answers = sorted(
                self._answers,
                key=lambda item: (-item["level"], item["time_taken"], item["player_name"]),
            )
            winner = dict(sorted_answers[0])

        return {
            "status": "winner_found",
            **winner,
        }

    def stop(self) -> None:
        """Stop the session and close all network resources."""
        self._stop_event.set()

        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        for conn in list(self._clients.values()):
            try:
                conn.close()
            except OSError:
                pass
        self._clients.clear()

    def _accept_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                conn, addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()

    def _handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        try:
            raw = conn.recv(4096)
            if not raw:
                return

            message = json.loads(raw.decode("utf-8"))
            message_type = message.get("type")

            if message_type == "join":
                player_name = message.get("player_name", "player")
                with self._lock:
                    self._clients[player_name] = conn

                response = {
                    "type": "join_ack",
                    "status": "joined",
                    "player_name": player_name,
                    "host_ip": self.host_ip,
                    "port": self.port,
                }
                conn.sendall(_encode_message(response))

                round_state = {
                    "type": "sync_round",
                    "question_id": self._session.get("question_id"),
                    "question_index": self._session.get("question_index"),
                    "timer": self._session.get("timer"),
                }
                conn.sendall(_encode_message(round_state))
                return

            if message_type == "answer":
                player_name = message.get("player_name")
                level = message.get("level")
                time_taken = message.get("time_taken", 0.0)

                if player_name is None or level is None:
                    conn.sendall(_encode_message({"type": "error", "message": "invalid answer"}))
                    return

                self.register_answer(player_name, level, time_taken)
                conn.sendall(_encode_message({"type": "answer_ack", "status": "recorded"}))
                return

            conn.sendall(_encode_message({"type": "error", "message": "unsupported message type"}))
        except Exception:
            try:
                conn.sendall(_encode_message({"type": "error", "message": "malformed payload"}))
            except OSError:
                pass

    def _broadcast(self, payload: Dict[str, Any]) -> None:
        encoded = _encode_message(payload)
        stale_clients: List[str] = []

        for player_name, conn in list(self._clients.items()):
            try:
                conn.sendall(encoded)
            except OSError:
                stale_clients.append(player_name)

        for player_name in stale_clients:
            self._clients.pop(player_name, None)


class NormalLobby:
    """Visible lobby for local normal multiplayer tables.

    A table is created by one player and becomes the host by default. The lobby
    exposes open tables with metadata such as name, player count, and whether a
    password is required. This mirrors the "Normal" mode flow described by the
    player: visible tables, host-owned rooms, and optional locked access.
    """

    def __init__(self) -> None:
        self.tables: Dict[str, Dict[str, Any]] = {}

    def create_table(
        self,
        table_name: str,
        host_player: str,
        password: Optional[str] = None,
        max_players: int = 2,
    ) -> Dict[str, Any]:
        """Create a visible table and let the creator host it by default.

        Parameters
        ----------
        table_name : str
            Display name for the table.
        host_player : str
            Name of the player who creates (hosts) the table.
        password : str or None
            Optional password. When provided the table is marked locked.
        max_players : int
            Maximum number of players allowed in the table (2, 3 or 4).
        """
        table_id = f"tbl_{len(self.tables) + 1}"
        table = {
            "table_id": table_id,
            "table_name": table_name,
            "host_player": host_player,
            "player_count": 1,
            "max_players": max_players,
            "locked": bool(password),
            "password": password,
            "players": [host_player],
            "status": "waiting",
        }
        self.tables[table_id] = table
        return table

    def list_tables(self) -> List[Dict[str, Any]]:
        """Return a lightweight snapshot of all open tables."""
        return [dict(table) for table in self.tables.values()]

    def join_table(self, table_id: str, player_name: str, password: Optional[str] = None) -> Dict[str, Any]:
        """Join an existing table if the request is allowed."""
        table = self.tables.get(table_id)
        if table is None:
            raise KeyError(f"Unknown table {table_id}")

        if table["locked"] and table.get("password") != password:
            return {
                "status": "denied",
                "reason": "invalid_password",
                "player_name": player_name,
            }

        if player_name in table["players"]:
            return {
                "status": "joined",
                "player_name": player_name,
                "table_id": table_id,
            }

        table["players"].append(player_name)
        table["player_count"] = len(table["players"])
        return {
            "status": "joined",
            "player_name": player_name,
            "table_id": table_id,
        }

    def remove_table(self, table_id: str) -> None:
        """Remove a table from the lobby."""
        self.tables.pop(table_id, None)


class RankedMatchmaker:
    """Invisible ranked matching layer.

    Ranked matchmaking pairs players by close ELO and then chooses an effective
    host based on connection quality. If quality data is unavailable, the
    selection falls back to a deterministic/first-player choice.
    """

    def __init__(self) -> None:
        self.queue: List[Dict[str, Any]] = []

    def enqueue_player(self, player_name: str, elo: int, connection_quality: Optional[int] = None) -> Dict[str, Any]:
        """Add a player to the ranked queue."""
        entry = {
            "player_name": player_name,
            "elo": elo,
            "connection_quality": connection_quality,
        }
        self.queue.append(entry)
        return entry

    def find_match(self) -> Optional[Dict[str, Any]]:
        """Pair two close-elo players and choose a host based on quality."""
        if len(self.queue) < 2:
            return None

        players = sorted(
            self.queue[:2],
            key=lambda item: item["elo"],
        )
        self.queue = self.queue[2:]
        host = self.choose_host(players)
        return {
            "match_id": "ranked_match",
            "players": [p["player_name"] for p in players],
            "host": host,
            "quality_score": max((p.get("connection_quality") or 0) for p in players),
            "stable_connection": bool(host),
        }

    def choose_host(self, players: List[Dict[str, Any]]) -> str:
        """Choose the player with the best connection quality, else first player."""
        if not players:
            raise ValueError("No players were supplied to choose a host")

        best = sorted(players, key=lambda item: (item.get("connection_quality") or 0, item["elo"]), reverse=True)
        return best[0]["player_name"]


class P2PClient:
    """A lightweight client that can join a P2P host and submit answers."""

    def __init__(self) -> None:
        self._socket: Optional[socket.socket] = None
        self._host_ip: Optional[str] = None
        self._port: Optional[int] = None
        self._player_name: Optional[str] = None
        self._buffer = ""

    def _recv_message(self) -> Dict[str, Any]:
        """Read one newline-delimited JSON message from the socket."""
        if self._socket is None:
            raise RuntimeError("Client socket is not connected")

        while "\n" not in self._buffer:
            chunk = self._socket.recv(4096)
            if not chunk:
                raise ConnectionError("Host closed the connection while reading a message")
            self._buffer += chunk.decode("utf-8")

        line, _, remaining = self._buffer.partition("\n")
        self._buffer = remaining
        return json.loads(line)

    def join_session(self, host_ip: str, port: int, player_name: str) -> Dict[str, Any]:
        """Connect to a host and register the player in the session."""
        sock = socket.create_connection((host_ip, port))
        raw = {
            "type": "join",
            "player_name": player_name,
        }
        sock.sendall(_encode_message(raw))

        join_payload = self._recv_message_from_socket(sock)
        if join_payload.get("status") != "joined":
            raise ConnectionError("Could not join the host session")

        sync_payload = self._recv_message_from_socket(sock)

        self._socket = sock
        self._host_ip = host_ip
        self._port = port
        self._player_name = player_name

        return {
            "status": "joined",
            "player_name": player_name,
            "host_ip": host_ip,
            "port": port,
            "round_state": sync_payload,
        }

    def _recv_message_from_socket(self, sock: socket.socket) -> Dict[str, Any]:
        """Read a single newline-delimited JSON message from a socket."""
        buffer = ""
        while "\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("Host closed the connection while reading a message")
            buffer += chunk.decode("utf-8")

        line, _, _ = buffer.partition("\n")
        return json.loads(line)

    def send_answer(self, level: int, time_taken: float) -> Dict[str, Any]:
        """Send an answer payload to the host for recording."""
        if self._socket is None or self._player_name is None:
            raise RuntimeError("Client must join a session before sending answers")

        payload = {
            "type": "answer",
            "player_name": self._player_name,
            "level": level,
            "time_taken": float(time_taken),
        }
        self._socket.sendall(_encode_message(payload))

        ack = self._recv_message()
        return ack

    def close(self) -> None:
        """Close the connection to the host."""
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
