"""
Sub Ladder v4.0 — WebSocket Manager
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Set


class WebSocketManager:
    """
    Gestionnaire central des connexions WebSocket.

    Fournit les méthodes pour enregistrer, désenregistrer,
    filtrer et diffuser des messages aux websockets connectés.
    """

    def __init__(self) -> None:
        # websocket -> metadata
        self._connections: Dict[Any, Dict[str, Optional[str]]] = {}
        # session_id -> role -> set of websockets
        self._by_session: Dict[str, Dict[str, Set[Any]]] = {}
        # role -> set of websockets (global, no session)
        self._by_role: Dict[str, Set[Any]] = {}
        self._lock = asyncio.Lock()

    async def register(self, websocket: Any, session_id: Optional[str] = None,
                       role: Optional[str] = None) -> None:
        """Enregistre une connexion WebSocket avec ses métadonnées."""
        async with self._lock:
            self._connections[websocket] = {
                "session_id": session_id,
                "role": role,
            }

            if session_id is not None and role is not None:
                if session_id not in self._by_session:
                    self._by_session[session_id] = {}
                if role not in self._by_session[session_id]:
                    self._by_session[session_id][role] = set()
                self._by_session[session_id][role].add(websocket)

            if role is not None:
                if role not in self._by_role:
                    self._by_role[role] = set()
                self._by_role[role].add(websocket)

    async def unregister(self, websocket: Any) -> None:
        """Retire une connexion WebSocket et nettoie les structures associées."""
        async with self._lock:
            meta = self._connections.pop(websocket, None)
            if meta is None:
                return

            session_id = meta.get("session_id")
            role = meta.get("role")

            # Retirer de _by_session
            if session_id is not None and role is not None:
                if session_id in self._by_session:
                    if role in self._by_session[session_id]:
                        self._by_session[session_id][role].discard(websocket)
                        if not self._by_session[session_id][role]:
                            del self._by_session[session_id][role]
                            if not self._by_session[session_id]:
                                del self._by_session[session_id]

            # Retirer de _by_role
            if role is not None:
                if role in self._by_role:
                    self._by_role[role].discard(websocket)
                    if not self._by_role[role]:
                        del self._by_role[role]

    async def is_registered(self, websocket: Any) -> bool:
        """Vérifie si une connexion WebSocket est enregistrée."""
        return websocket in self._connections

    def get_registered_websockets(self, session_id: Optional[str] = None,
                                   role: Optional[str] = None) -> List[Any]:
        """
        Récupère la liste des websockets filtrés par session_id et/ou role.

        - Si les deux sont None : retourne tous les websockets.
        - Si session_id est fourni : retourne les websockets de cette session.
        - Si role est fourni : retourne les websockets de ce rôle.
        - Si les deux sont fournis : intersection (websocket dans la session ET du rôle).
        """
        if session_id is None and role is None:
            return list(self._connections.keys())

        if session_id is not None and role is not None:
            if session_id in self._by_session and role in self._by_session[session_id]:
                return list(self._by_session[session_id][role])
            return []

        if session_id is not None:
            result: Set[Any] = set()
            if session_id in self._by_session:
                for role_set in self._by_session[session_id].values():
                    result.update(role_set)
            return list(result)

        if role is not None:
            if role in self._by_role:
                return list(self._by_role[role])
            return []

        return []

    async def broadcast(self, message: Any, session_id: Optional[str] = None,
                        role: Optional[str] = None) -> int:
        """
        Diffuse un message JSON aux websockets ciblés.

        Retourne le nombre de websockets ayant reçu le message.
        """
        websockets = self.get_registered_websockets(session_id, role)
        if not websockets:
            return 0

        serialized = json.dumps(message) if not isinstance(message, str) else message
        sent = 0
        for ws in websockets:
            try:
                ws.write_json(json.loads(serialized) if isinstance(serialized, str) else message)
                sent += 1
            except Exception:
                # Le websocket est probablement déconnecté
                pass

        return sent

    async def send_to_role(self, session_id: str, message: Any,
                           role: str) -> int:
        """Envoie un message à tous les websockets d'un rôle donné dans une session."""
        websockets = self.get_registered_websockets(session_id, role)
        if not websockets:
            return 0

        serialized = json.dumps(message) if not isinstance(message, str) else message
        sent = 0
        for ws in websockets:
            try:
                ws.write_json(json.loads(serialized) if isinstance(serialized, str) else message)
                sent += 1
            except Exception:
                pass

        return sent


# Instance singleton globale
websocket_manager = WebSocketManager()
