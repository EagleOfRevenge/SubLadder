"""
Module pour gérer le mode Streamer vs Viewvers
"""
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Question:
    """Représente une question du quiz"""
    id: str
    text: str
    options: List[str]
    correct_answer: str
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class StreamerSession:
    """Représente une session Streamer vs Viewvers"""
    id: str
    streamer_link: str
    live_duration: int  # en secondes
    viewver_response_time: int  # en secondes
    status: str = "waiting"  # waiting, active, finished
    questions: List[Question] = None
    current_question_index: int = 0
    created_at: str = None
    participants: List[str] = None
    integrations: Dict[str, dict] = None
    
    def __post_init__(self):
        if self.questions is None:
            self.questions = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.participants is None:
            self.participants = []
        if self.integrations is None:
            self.integrations = {}

@dataclass
class PlayerResponse:
    """Représente la réponse d'un joueur"""
    player_id: str
    question_id: str
    answer: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class StreamerAnswer:
    """Représente la réponse du streamer"""
    session_id: str
    question_id: str
    answer: str
    used_jokers: List[str] = None  # 50_50, public_vote
    timestamp: str = None
    
    def __post_init__(self):
        if self.used_jokers is None:
            self.used_jokers = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class StreamerModeManager:
    """Gestionnaire du mode Streamer vs Viewvers"""
    
    def __init__(self):
        self.sessions: Dict[str, StreamerSession] = {}
        self.responses: Dict[str, List[PlayerResponse]] = {}  # player_id -> list of responses
        self.streamer_answers: Dict[str, StreamerAnswer] = {}
        self.question_timers: Dict[str, float] = {}  # question_id -> end_time
        
    def create_session(self, streamer_link: str, live_duration: int, 
                      viewver_response_time: int) -> StreamerSession:
        """Crée une nouvelle session Streamer vs Viewvers"""
        session_id = f"session_{int(time.time())}"
        session = StreamerSession(
            id=session_id,
            streamer_link=streamer_link,
            live_duration=live_duration,
            viewver_response_time=viewver_response_time
        )
        self.sessions[session_id] = session
        return session
    
    def add_question(self, session_id: str, question: Question) -> bool:
        """Ajoute une question à une session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.questions.append(question)
        return True
    
    def start_session(self, session_id: str) -> bool:
        """Démarre une session"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        session.status = "active"
        return session
    
    def end_session(self, session_id: str) -> bool:
        """Termine une session"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        session.status = "finished"
        return session

    def join_session(self, session_id: str, player_id: str) -> bool:
        """Ajoute un participant à la session."""
        if session_id not in self.sessions:
            return False
        session = self.sessions[session_id]
        if player_id in session.participants:
            return True
        session.participants.append(player_id)
        return True

    def leave_session(self, session_id: str, player_id: str) -> bool:
        """Retire un participant de la session."""
        if session_id not in self.sessions:
            return False
        session = self.sessions[session_id]
        if player_id in session.participants:
            session.participants.remove(player_id)
            return True
        return False

    def set_integration(self, session_id: str, provider: str, config: dict) -> bool:
        """Associe une configuration d'intégration (twitch/youtube) à la session."""
        if session_id not in self.sessions:
            return False
        session = self.sessions[session_id]
        session.integrations[provider] = config or {}
        return True
    
    def add_player_response(self, session_id: str, player_id: str, 
                           question_id: str, answer: str) -> bool:
        """Enregistre la réponse d'un joueur"""
        if session_id not in self.sessions:
            return False
            
        # Vérifier si la session est active
        session = self.sessions[session_id]
        if session.status != "active":
            return False
            
        # Stocker uniquement la première réponse du joueur pour une question
        response_key = f"{player_id}_{question_id}"
        if response_key not in self.responses:
            self.responses[response_key] = []
        
        # Vérifier si le joueur a déjà répondu à cette question
        for existing_response in self.responses[response_key]:
            if existing_response.question_id == question_id:
                return False  # Le joueur a déjà répondu
        
        response = PlayerResponse(
            player_id=player_id,
            question_id=question_id,
            answer=answer
        )
        
        self.responses[response_key].append(response)
        return True
    
    def get_session_responses(self, session_id: str, question_id: str) -> List[PlayerResponse]:
        """Récupère toutes les réponses pour une question dans une session"""
        responses = []
        for response_list in self.responses.values():
            for response in response_list:
                if response.question_id == question_id:
                    responses.append(response)
        return responses
    
    def get_question_stats(self, session_id: str, question_id: str) -> Dict:
        """Calcule les statistiques pour une question"""
        responses = self.get_session_responses(session_id, question_id)
        total_responses = len(responses)
        
        if total_responses == 0:
            return {
                "total_responses": 0,
                "responses_distribution": {}
            }
        
        # Calculer la distribution des réponses
        distribution = {}
        for response in responses:
            answer = response.answer
            if answer not in distribution:
                distribution[answer] = 0
            distribution[answer] += 1
        
        # Convertir en pourcentages
        percentages = {}
        for answer, count in distribution.items():
            percentages[answer] = (count / total_responses) * 100
        
        return {
            "total_responses": total_responses,
            "responses_distribution": percentages
        }
    
    def add_streamer_answer(self, session_id: str, question_id: str, 
                           answer: str, used_jokers: List[str] = None) -> bool:
        """Enregistre la réponse du streamer"""
        if session_id not in self.sessions:
            return False
            
        # Vérifier si la session est active
        session = self.sessions[session_id]
        if session.status != "active":
            return False
            
        # Vérifier si la question existe
        question_exists = any(q.id == question_id for q in session.questions)
        if not question_exists:
            return False
        
        streamer_answer = StreamerAnswer(
            session_id=session_id,
            question_id=question_id,
            answer=answer,
            used_jokers=used_jokers or []
        )
        
        self.streamer_answers[question_id] = streamer_answer
        return True
    
    def get_session_results(self, session_id: str) -> Dict:
        """Récupère les résultats d'une session"""
        if session_id not in self.sessions:
            return {}
            
        session = self.sessions[session_id]
        
        results = {
            "session_info": asdict(session),
            "questions": []
        }
        
        for question in session.questions:
            question_data = {
                "question": asdict(question),
                "stats": self.get_question_stats(session_id, question.id),
                "streamer_answer": None
            }
            
            # Ajouter la réponse du streamer si disponible
            if question.id in self.streamer_answers:
                question_data["streamer_answer"] = asdict(self.streamer_answers[question.id])
            
            results["questions"].append(question_data)
        
        return results

# Instance unique du gestionnaire
streamer_manager = StreamerModeManager()