"""
Module pour le mode Streamer vs Viewvers
Gestion de la logique du jeu pour ce mode spécifique
"""
import json
import asyncio
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StreamerQuestion:
    """Représente une question pour le mode Streamer vs Viewvers"""
    id: str
    text: str
    options: List[str]
    correct_answer: str  # index de la bonne réponse (0-3)
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StreamerQuestion':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PlayerAnswer:
    """Réponse d'un viewver"""
    player_id: str
    player_name: str
    question_id: str
    answer_index: int
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerAnswer':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class StreamerVote:
    """Vote du streamer pour une question"""
    question_id: str
    answer_index: int
    used_jokers: List[str]  # "fifty_fifty", "public_vote"
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.used_jokers is None:
            self.used_jokers = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StreamerVote':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SessionConfig:
    """Configuration d'une session Streamer vs Viewvers"""
    session_id: str
    streamer_link: str
    live_delay: int  # délai du live en secondes
    response_time: int  # temps de réponse en secondes
    questions_count: int = 15
    status: str = "waiting"  # waiting, config, playing, voting, results, finished
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return asdict(self)


class StreamerGame:
    """Classe principale pour gérer une partie Streamer vs Viewvers"""
    
    def __init__(self, session_id: str, questions: List[StreamerQuestion], 
                 response_time: int = 180):
        self.session_id = session_id
        self.questions = questions
        self.current_question_index = 0
        self.response_time = response_time
        self.remaining_time = response_time
        
        # Stockage des réponses
        self.player_answers: Dict[str, Dict[str, int]] = {}  # player_id -> {question_id: answer_index}
        self.streamer_votes: Dict[str, StreamerVote] = {}  # question_id -> StreamerVote
        
        # Statut de la question actuelle
        self.question_phase: str = "viewver_answer"  # viewver_answer, streamer_vote, results
        self.timer_active: bool = False
        self.timer_callback: Optional[Callable] = None
        
        # Jokers du streamer (1 par question, True = disponible)
        self.streamer_fifty_fifty: List[bool] = [True] * len(questions)
        self.streamer_public_vote: List[bool] = [True] * len(questions)
        
        # Stats pour le podium
        self.player_scores: Dict[str, int] = {}  # player_id -> score
        self.total_players: int = 0
        
        # Config
        self.config = SessionConfig(
            session_id=session_id,
            streamer_link="",
            live_delay=0,
            response_time=response_time
        )
    
    def get_current_question(self) -> Optional[StreamerQuestion]:
        """Récupère la question actuelle"""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def get_current_question_index(self) -> int:
        return self.current_question_index
    
    def submit_player_answer(self, player_id: str, question_id: str, answer_index: int) -> bool:
        """Soumet la réponse d'un viewver (seulement la première compte)"""
        if player_id not in self.player_answers:
            self.player_answers[player_id] = {}
        
        # Vérifier si le joueur a déjà répondu à cette question
        if question_id in self.player_answers[player_id]:
            return False  # Déjà répondu
        
        self.player_answers[player_id][question_id] = answer_index
        
        # Mettre à jour le nombre total de joueurs unique
        if player_id not in self.player_scores:
            self.player_scores[player_id] = 0
            self.total_players += 1
        
        return True
    
    def submit_streamer_vote(self, question_id: str, answer_index: int, 
                            jokers: Optional[List[str]] = None) -> bool:
        """Soumet le vote du streamer"""
        if jokers is None:
            jokers = []
        
        vote = StreamerVote(
            question_id=question_id,
            answer_index=answer_index,
            used_jokers=jokers
        )
        
        self.streamer_votes[question_id] = vote
        return True
    
    def get_question_stats(self, question_id: str) -> Dict[str, Any]:
        """Récupère les statistiques pour une question"""
        answers = []
        for player_answers in self.player_answers.values():
            if question_id in player_answers:
                answers.append(player_answers[question_id])
        
        total = len(answers)
        distribution = {}
        
        for i in range(4):  # 4 options max
            count = answers.count(i)
            distribution[str(i)] = {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
        
        return {
            "total_responses": total,
            "distribution": distribution
        }
    
    def check_answer(self, answer_index: int, correct_answer: str) -> bool:
        """Vérifie si une réponse est correcte"""
        return str(answer_index) == str(correct_answer)
    
    def calculate_scores(self) -> Dict[str, int]:
        """Calcule les scores finaux de tous les joueurs"""
        scores = {}
        
        for player_id, answers in self.player_answers.items():
            score = 0
            for question in self.questions:
                if question.id in answers:
                    if self.check_answer(answers[question.id], question.correct_answer):
                        score += 1
            scores[player_id] = score
        
        self.player_scores = scores
        return scores
    
    def get_podium(self) -> List[Dict[str, Any]]:
        """Récupère le podium (top 3)"""
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"player_id": p[0], "player_name": p[0], "score": p[1]} for p in sorted_players[:3]]
    
    def next_question(self) -> bool:
        """Passe à la question suivante"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.remaining_time = self.response_time
            self.question_phase = "viewver_answer"
            return True
        return False
    
    def get_results(self) -> Dict[str, Any]:
        """Récupère les résultats complets de la session"""
        # Calculer les scores si pas déjà fait
        if not self.player_scores:
            self.calculate_scores()
        
        results = {
            "session_id": self.session_id,
            "podium": self.get_podium(),
            "all_scores": self.player_scores,
            "total_players": self.total_players,
            "questions": []
        }
        
        for i, question in enumerate(self.questions):
            stats = self.get_question_stats(question.id)
            streamer_vote = self.streamer_votes.get(question.id)
            
            question_result = {
                "question_index": i + 1,
                "question": question.to_dict(),
                "stats": stats,
                "streamer_vote": streamer_vote.to_dict() if streamer_vote else None,
                "correct_answer": question.correct_answer
            }
            
            results["questions"].append(question_result)
        
        return results
    
    def get_phase_info(self) -> Dict[str, Any]:
        """Récupère les informations pour la phase actuelle"""
        current_q = self.get_current_question()
        if not current_q:
            return {}
        
        return {
            "phase": self.question_phase,
            "question": current_q.to_dict(),
            "question_index": self.current_question_index + 1,
            "total_questions": len(self.questions),
            "remaining_time": self.remaining_time,
            "total_players": self.total_players,
            "streamer_jokers": {
                "fifty_fifty": self.streamer_fifty_fifty[self.current_question_index],
                "public_vote": self.streamer_public_vote[self.current_question_index]
            }
        }
    
    def use_fifty_fifty(self) -> Optional[List[int]]:
        """Utilise le joker 50/50 pour la question actuelle. Retourne les indices restants."""
        if self.current_question_index >= len(self.streamer_fifty_fifty):
            return None
        if not self.streamer_fifty_fifty[self.current_question_index]:
            return None
        
        current_q = self.get_current_question()
        if not current_q:
            return None
        
        correct_idx = int(current_q.correct_answer)
        # Trouver les mauvaises réponses
        wrong_indices = [i for i in range(len(current_q.options)) if i != correct_idx]
        
        # Garder la bonne réponse et supprimer 2 mauvaises réponses
        if len(wrong_indices) > 2:
            removed_wrong = random.sample(wrong_indices, 2)
            remaining = [correct_idx] + [i for i in wrong_indices if i not in removed_wrong]
        else:
            remaining = wrong_indices + [correct_idx]
        
        self.streamer_fifty_fifty[self.current_question_index] = False
        return remaining
    
    def use_public_vote(self) -> Dict[str, Any]:
        """Utilise le joker vote du public. Retourne les pourcentages."""
        if self.current_question_index >= len(self.streamer_public_vote):
            return {}
        if not self.streamer_public_vote[self.current_question_index]:
            return {}
        
        current_q = self.get_current_question()
        if not current_q:
            return {}
        
        self.streamer_public_vote[self.current_question_index] = False
        stats = self.get_question_stats(current_q.id)
        return stats
    
    def start_timer(self, root, callback=None):
        """Démarre le timer côté client Tkinter"""
        self.timer_active = True
        self.timer_callback = callback
        self._update_timer(root)
    
    def stop_timer(self):
        """Arrête le timer"""
        self.timer_active = False
        self.timer_callback = None
    
    def _update_timer(self, root):
        """Méthode interne pour mettre à jour le timer"""
        if self.timer_active and self.remaining_time > 0:
            self.remaining_time -= 1
            if self.remaining_time == 0:
                self.timer_active = False
                if self.timer_callback:
                    self.timer_callback()
            else:
                root.after(1000, lambda: self._update_timer(root))
