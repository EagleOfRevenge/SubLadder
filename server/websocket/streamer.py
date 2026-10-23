"""
Gestion des communications WebSocket pour le mode Streamer vs Viewvers
"""
import asyncio
import json
from typing import Dict, List, Any
from server.streamer import streamer_manager, StreamerSession, Question
from server.websocket import websocket_manager

# Stockage des connexions WebSocket par session
streamer_connections: Dict[str, List[Any]] = {}
viewver_connections: Dict[str, List[Any]] = {}

def register_streamer_connection(session_id: str, websocket):
    """Enregistre une connexion WebSocket pour le streamer"""
    if session_id not in streamer_connections:
        streamer_connections[session_id] = []
    streamer_connections[session_id].append(websocket)

def unregister_streamer_connection(session_id: str, websocket):
    """Désenregistre une connexion WebSocket pour le streamer"""
    if session_id in streamer_connections:
        if websocket in streamer_connections[session_id]:
            streamer_connections[session_id].remove(websocket)

def register_viewver_connection(session_id: str, websocket):
    """Enregistre une connexion WebSocket pour un viewver"""
    if session_id not in viewver_connections:
        viewver_connections[session_id] = []
    viewver_connections[session_id].append(websocket)

def unregister_viewver_connection(session_id: str, websocket):
    """Désenregistre une connexion WebSocket pour un viewver"""
    if session_id in viewver_connections:
        if websocket in viewver_connections[session_id]:
            viewver_connections[session_id].remove(websocket)

async def send_to_streamer(session_id: str, message: dict):
    """Envoie un message au streamer d'une session"""
    if session_id in streamer_connections:
        for websocket in streamer_connections[session_id]:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Erreur lors de l'envoi au streamer: {e}")

async def send_to_viewvers(session_id: str, message: dict):
    """Envoie un message à tous les viewvers d'une session"""
    if session_id in viewver_connections:
        for websocket in viewver_connections[session_id]:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Erreur lors de l'envoi aux viewvers: {e}")

async def send_to_all_in_session(session_id: str, message: dict):
    """Envoie un message à tous les participants d'une session"""
    # Envoyer au streamer
    await send_to_streamer(session_id, message)
    # Envoyer aux viewvers
    await send_to_viewvers(session_id, message)

def handle_streamer_message(session_id: str, message_data: dict):
    """Traite les messages du streamer"""
    try:
        action = message_data.get('action')
        
        if action == 'start_session':
            # Démarrage d'une session
            session = streamer_manager.start_session(session_id)
            if session:
                # Envoyer la première question
                if session.questions:
                    first_question = session.questions[0]
                    asyncio.create_task(send_to_all_in_session(session_id, {
                        'type': 'question_start',
                        'question': {
                            'id': first_question.id,
                            'text': first_question.text,
                            'options': first_question.options,
                            'time_limit': session.viewver_response_time
                        }
                    }))
        
        elif action == 'answer_question':
            # Réponse du streamer à une question
            question_id = message_data.get('question_id')
            answer = message_data.get('answer')
            used_jokers = message_data.get('used_jokers', [])
            
            if question_id and answer:
                success = streamer_manager.add_streamer_answer(
                    session_id, question_id, answer, used_jokers
                )
                
                if success:
                    # Informer les viewvers que le streamer a répondu
                    asyncio.create_task(send_to_viewvers(session_id, {
                        'type': 'streamer_answer_received',
                        'question_id': question_id,
                        'answer': answer,
                        'used_jokers': used_jokers
                    }))
                    
                    # Envoyer les statistiques du vote du public
                    stats = streamer_manager.get_question_stats(session_id, question_id)
                    asyncio.create_task(send_to_streamer(session_id, {
                        'type': 'public_vote_results',
                        'question_id': question_id,
                        'stats': stats
                    }))
    
    except Exception as e:
        print(f"Erreur dans handle_streamer_message: {e}")

def handle_viewver_message(session_id: str, message_data: dict):
    """Traite les messages des viewvers"""
    try:
        action = message_data.get('action')
        
        if action == 'submit_answer':
            # Réponse d'un viewver
            question_id = message_data.get('question_id')
            answer = message_data.get('answer')
            player_id = message_data.get('player_id')
            
            if question_id and answer and player_id:
                success = streamer_manager.add_player_response(
                    session_id, player_id, question_id, answer
                )
                
                if success:
                    # Informer le viewver que sa réponse a été enregistrée
                    asyncio.create_task(send_to_viewvers(session_id, {
                        'type': 'answer_received',
                        'question_id': question_id,
                        'player_id': player_id
                    }))
    
    except Exception as e:
        print(f"Erreur dans handle_viewver_message: {e}")

async def broadcast_session_update(session_id: str):
    """Diffuse une mise à jour de session à tous les participants"""
    try:
        session = streamer_manager.sessions.get(session_id)
        if session:
            # Envoyer les informations de la session
            await send_to_all_in_session(session_id, {
                'type': 'session_update',
                'session_info': {
                    'id': session.id,
                    'status': session.status,
                    'questions_count': len(session.questions),
                    'current_question_index': session.current_question_index
                }
            })
    except Exception as e:
        print(f"Erreur dans broadcast_session_update: {e}")

async def send_question_stats(session_id: str, question_id: str):
    """Envoie les statistiques d'une question à tous les participants"""
    try:
        stats = streamer_manager.get_question_stats(session_id, question_id)
        await send_to_all_in_session(session_id, {
            'type': 'question_stats',
            'question_id': question_id,
            'stats': stats
        })
    except Exception as e:
        print(f"Erreur dans send_question_stats: {e}")

async def end_question_timer(session_id: str, question_id: str):
    """Termine le timer d'une question"""
    try:
        # Envoyer un message que le temps est écoulé
        await send_to_all_in_session(session_id, {
            'type': 'time_up',
            'question_id': question_id
        })
        
        # Envoyer les statistiques du vote du public
        stats = streamer_manager.get_question_stats(session_id, question_id)
        await send_to_streamer(session_id, {
            'type': 'public_vote_results',
            'question_id': question_id,
            'stats': stats
        })
    except Exception as e:
        print(f"Erreur dans end_question_timer: {e}")

async def start_new_question(session_id: str, question_index: int):
    """Démarre une nouvelle question"""
    try:
        session = streamer_manager.sessions.get(session_id)
        if not session or question_index >= len(session.questions):
            return
            
        question = session.questions[question_index]
        
        # Mettre à jour l'index de la question
        session.current_question_index = question_index
        
        # Diffuser la nouvelle question
        await send_to_all_in_session(session_id, {
            'type': 'question_start',
            'question': {
                'id': question.id,
                'text': question.text,
                'options': question.options,
                'time_limit': session.viewver_response_time
            }
        })
    except Exception as e:
        print(f"Erreur dans start_new_question: {e}")

def get_streamer_session_info(session_id: str) -> dict:
    """Récupère les informations d'une session pour le streamer"""
    session = streamer_manager.sessions.get(session_id)
    if not session:
        return {}
    
    return {
        'id': session.id,
        'streamer_link': session.streamer_link,
        'live_duration': session.live_duration,
        'viewver_response_time': session.viewver_response_time,
        'status': session.status,
        'questions_count': len(session.questions),
        'current_question_index': session.current_question_index
    }