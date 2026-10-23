"""
game/auth/client.py — HTTP client for server communication
Provides login, signup, and health check functionality.
"""

import urllib.request
import urllib.error
import json
import time


PRIMARY_SERVER_HOST = "dedicated-zap1280014-1.zap-srv.com"
LEGACY_SERVER_HOST = "45.156.84.114"
DEFAULT_SERVER_PORT = 8000
PUBLIC_SERVER_URL = f"https://{PRIMARY_SERVER_HOST}"


class APIClient:
    """HTTP client for communicating with SubLadder server."""
    
    def __init__(self, host: str = PRIMARY_SERVER_HOST, port: int = DEFAULT_SERVER_PORT):
        """
        Initialize API client.
        
        Args:
            host: Server IP or hostname (default: dedicated-zap1280014-1.zap-srv.com)
            port: Server port (default: 8000)
        """
        self.host = host
        self.port = port
        self.base_urls = self._build_base_urls(host, port)
        self.base_url = self.base_urls[0]
        self.timeout = 3  # seconds
        self.last_error = None

    def _build_base_urls(self, host: str, port: int) -> list[str]:
        """Return prioritized server base URLs with DNS preferred over the legacy IP."""
        if not host or host in {LEGACY_SERVER_HOST, "0.0.0.0", "127.0.0.1", "localhost"}:
            return [PUBLIC_SERVER_URL, f"http://{LEGACY_SERVER_HOST}:{port}"]

        if host == PRIMARY_SERVER_HOST:
            return [PUBLIC_SERVER_URL, f"http://{LEGACY_SERVER_HOST}:{port}"]

        if host == LEGACY_SERVER_HOST:
            return [f"http://{LEGACY_SERVER_HOST}:{port}", PUBLIC_SERVER_URL]

        return [f"http://{host}:{port}"]

    def _request_json(self, path: str, method: str = "GET", data: dict | bytes | None = None, headers: dict | None = None) -> dict:
        """Send a request and fall back to the next base URL when the current one is unreachable."""
        payload = None
        if data is not None:
            payload = data if isinstance(data, (bytes, bytearray)) else json.dumps(data).encode("utf-8")

        request_headers = {"User-Agent": "SubLadder/1.0"}
        if headers:
            request_headers.update(headers)

        last_error = None
        for base_url in self.base_urls:
            url = f"{base_url}{path}"
            req = urllib.request.Request(url, data=payload, method=method)
            for header_name, header_value in request_headers.items():
                req.add_header(header_name, header_value)

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    body = response.read().decode("utf-8")
                    self.last_error = None
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as error:
                self.last_error = str(error)
                try:
                    body = error.read().decode("utf-8")
                    parsed = json.loads(body) if body else {}
                    if isinstance(parsed, dict):
                        if "error" not in parsed and "detail" in parsed:
                            parsed["error"] = parsed["detail"]
                        if parsed:
                            return parsed
                    return {"error": str(error)}
                except Exception:
                    return {"error": str(error)}
            except urllib.error.URLError as error:
                last_error = str(error)
                continue
            except Exception as error:
                last_error = str(error)
                continue

        self.last_error = last_error
        return {"error": last_error or "Unable to reach server"}
    
    def health_check(self) -> bool:
        """
        Check if server is online by pinging health endpoint.
        Returns True if server responds, False otherwise.
        """
        result = self._request_json("/api/health")
        if isinstance(result, dict) and result.get("status"):
            return True
        
        return False
    
    def login(self, email: str, password: str) -> dict:
        """
        Login with email/password.
        
        Returns:
            {
                "access_token": "jwt_token",
                "token_type": "bearer",
                "user": {"id": "...", "email": "...", "game_name": "..."},
                "error": None  # or error message
            }
        """
        return self._request_json(
            "/auth/login",
            method="POST",
            data={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
    
    def register(self, email: str, password: str, game_name: str) -> dict:
        """
        Register new account with email/password.
        
        Returns:
            {
                "access_token": "jwt_token",
                "token_type": "bearer",
                "user": {"id": "...", "email": "...", "game_name": "..."},
                "error": None  # or error message
            }
        """
        return self._request_json(
            "/auth/register",
            method="POST",
            data={"email": email, "password": password, "game_name": game_name},
            headers={"Content-Type": "application/json"},
        )
    
    def get_profile(self, token: str) -> dict:
        """
        Fetch user profile data from server using JWT token.
        
        Args:
            token: JWT access token from login/signup
            
        Returns:
            {
                "profile": {
                    "id": "...",
                    "email": "...",
                    "game_name": "...",
                    "level": 0,
                    "games_played": 0,
                    "total_score": 0,
                    "last_updated": "2026-05-21T...",
                    ...
                },
                "error": None  # or error message
            }
        """
        return self._request_json(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

    def get_ranked_stats(self, profile_name: str, token: str) -> dict:
        """GET /api/ranked/profile/{profile_name}/stats"""
        return self._request_json(
            f"/api/ranked/profile/{urllib.request.quote(profile_name)}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )

    def get_ranked_leaderboard(self, token: str = None, limit: int = 50, offset: int = 0) -> dict:
        """GET /api/ranked/leaderboard"""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self._request_json(f"/api/ranked/leaderboard?limit={limit}&offset={offset}", headers=headers)

    def find_ranked_match(self, token: str, preferred_elo_range: int = 200, min_games_played: int = 5) -> dict:
        """POST /api/ranked/matchmaking/find"""
        return self._request_json(
            "/api/ranked/matchmaking/find",
            method="POST",
            data={"preferred_elo_range": preferred_elo_range, "min_games_played": min_games_played},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

    def leave_ranked_matchmaking(self, token: str) -> dict:
        """POST /api/ranked/matchmaking/leave"""
        return self._request_json(
            "/api/ranked/matchmaking/leave",
            method="POST",
            data=b"",
            headers={"Authorization": f"Bearer {token}"},
        )

    def get_profile_overview(self, profile_name: str, token: str | None = None) -> dict:
        """GET /api/profile/{profile_name}/overview"""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self._request_json(f"/api/profile/{urllib.request.quote(profile_name)}/overview", headers=headers)

    def get_profile_stats(self, profile_name: str, token: str | None = None) -> dict:
        """GET /api/profile/{profile_name}/stats"""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self._request_json(f"/api/profile/{urllib.request.quote(profile_name)}/stats", headers=headers)

    def get_profile_matches(self, profile_name: str, token: str | None = None, limit: int = 50, offset: int = 0) -> dict:
        """GET /api/profile/{profile_name}/matches?limit=&offset="""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self._request_json(
            f"/api/profile/{urllib.request.quote(profile_name)}/matches?limit={limit}&offset={offset}",
            headers=headers,
        )

    def get_profile_ranked(self, profile_name: str, token: str | None = None) -> dict:
        """GET /api/profile/{profile_name}/ranked"""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        return self._request_json(f"/api/profile/{urllib.request.quote(profile_name)}/ranked", headers=headers)

    def get_social_snapshot(self, token: str) -> dict:
        """GET /api/social/me"""
        return self._request_json("/api/social/me", headers={"Authorization": f"Bearer {token}"})

    def get_social_friends(self, token: str) -> dict:
        """GET /api/social/friends"""
        return self._request_json("/api/social/friends", headers={"Authorization": f"Bearer {token}"})

    def send_friend_request(self, token: str, target_profile_name: str) -> dict:
        """POST /api/social/requests/send"""
        return self._request_json(
            "/api/social/requests/send",
            method="POST",
            data={"target_profile_name": target_profile_name},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

    def accept_friend_request(self, token: str, requestor_profile_name: str) -> dict:
        """POST /api/social/requests/accept"""
        return self._request_json(
            "/api/social/requests/accept",
            method="POST",
            data={"requestor_profile_name": requestor_profile_name},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

    def decline_friend_request(self, token: str, requestor_profile_name: str) -> dict:
        """POST /api/social/requests/decline"""
        return self._request_json(
            "/api/social/requests/decline",
            method="POST",
            data={"requestor_profile_name": requestor_profile_name},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )

    def get_normal_rooms(self) -> dict:
        """GET /api/multiplayer/normal-rooms"""
        return self._request_json("/api/multiplayer/normal-rooms")

    def create_normal_room(self, table_name: str, host_player: str, max_players: int = 2, password: str | None = None) -> dict:
        """POST /api/multiplayer/normal-rooms"""
        payload = {
            "table_name": table_name,
            "host_player": host_player,
            "max_players": max_players,
            "password": password,
        }
        return self._request_json(
            "/api/multiplayer/normal-rooms",
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

    def get_normal_room(self, table_id: str) -> dict:
        """GET /api/multiplayer/normal-rooms/{table_id}"""
        return self._request_json(f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}")

    def join_normal_room(self, table_id: str, player_name: str, password: str | None = None) -> dict:
        """POST /api/multiplayer/normal-rooms/{table_id}/join"""
        return self._request_json(
            f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}/join",
            method="POST",
            data={"table_id": table_id, "player_name": player_name, "password": password},
            headers={"Content-Type": "application/json"},
        )

    def delete_normal_room(self, table_id: str) -> dict:
        """DELETE /api/multiplayer/normal-rooms/{table_id}"""
        return self._request_json(
            f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}",
            method="DELETE",
        )

    def leave_normal_room(self, table_id: str, player_name: str) -> dict:
        """POST /api/multiplayer/normal-rooms/{table_id}/leave"""
        return self._request_json(
            f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}/leave",
            method="POST",
            data={"player_name": player_name},
            headers={"Content-Type": "application/json"},
        )

    def start_normal_room(self, table_id: str, starter_player: str) -> dict:
        """POST /api/multiplayer/normal-rooms/{table_id}/start"""
        return self._request_json(
            f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}/start",
            method="POST",
            data={"starter_player": starter_player},
            headers={"Content-Type": "application/json"},
        )

    def set_normal_room_ready(self, table_id: str, player_name: str, ready: bool = True) -> dict:
        """POST /api/multiplayer/normal-rooms/{table_id}/ready"""
        return self._request_json(
            f"/api/multiplayer/normal-rooms/{urllib.request.quote(table_id)}/ready",
            method="POST",
            data={"table_id": table_id, "player_name": player_name, "ready": ready},
            headers={"Content-Type": "application/json"},
        )

    def poll_oauth_result(self, state: str) -> dict:
        """Poll the server for a completed Discord/Steam OAuth result."""
        return self._request_json(f"/auth/oauth/result?state={state}")
