import pygame
import sys
from game.game_state import GameState
from game.ui_helpers import draw_text, draw_button, draw_progress_bar
from game.constants import *

class StreamerGameStreamerScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.question_index = 0
        self.current_question = None
        self.answered = False
        self.time_left = 0
        self.timer_start = 0
        self.jokers = {
            '50/50': True,
            'public_vote': True
        }
        self.public_votes = [0, 0, 0, 0]  # Pourcentage de votes pour chaque réponse
        
    def load_question(self, question_data):
        """Charge une question depuis les données"""
        self.current_question = question_data
        self.answered = False
        self.time_left = question_data.get('time_limit', 15)  # Temps par défaut: 15 secondes
        self.timer_start = pygame.time.get_ticks()
        self.public_votes = [0, 0, 0, 0]
        
    def update_timer(self):
        """Met à jour le timer"""
        if not self.answered:
            elapsed = (pygame.time.get_ticks() - self.timer_start) // 1000
            self.time_left = max(0, self.current_question.get('time_limit', 15) - elapsed)
            
    def handle_events(self, events):
        """Gère les événements"""
        for event in events:
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.MOUSEBUTTONDOWN and not self.answered:
                mouse_pos = pygame.mouse.get_pos()
                
                # Vérifier si un bouton de réponse a été cliqué
                if self.check_answer_click(mouse_pos):
                    self.answer_question()
                    
                # Vérifier les jokers
                elif self.check_joker_click(mouse_pos, '50/50'):
                    if self.jokers['50/50']:
                        self.use_5050()
                        
                elif self.check_joker_click(mouse_pos, 'public_vote'):
                    if self.jokers['public_vote']:
                        self.use_public_vote()
                        
        return True
        
    def check_answer_click(self, pos):
        """Vérifie si une réponse a été cliquée"""
        # Calculer la position des boutons de réponse
        button_width = 400
        button_height = 50
        button_margin = 20
        start_y = 200
        
        for i in range(4):
            x = (SCREEN_WIDTH - button_width) // 2
            y = start_y + i * (button_height + button_margin)
            
            if x <= pos[0] <= x + button_width and y <= pos[1] <= y + button_height:
                return True
        return False
        
    def check_joker_click(self, pos, joker_name):
        """Vérifie si un joker a été cliqué"""
        if joker_name == '50/50':
            x = 100
            y = SCREEN_HEIGHT - 100
        else:  # public_vote
            x = SCREEN_WIDTH - 200
            y = SCREEN_HEIGHT - 100
            
        button_width = 150
        button_height = 40
        
        return (x <= pos[0] <= x + button_width and 
                y <= pos[1] <= y + button_height)
                
    def answer_question(self):
        """Gère la réponse à la question"""
        self.answered = True
        
    def use_5050(self):
        """Utilise le joker 50/50"""
        # Pour l'instant, on ne fait rien ici, mais on pourrait masquer 2 réponses
        self.jokers['50/50'] = False
        
    def use_public_vote(self):
        """Utilise le vote du public"""
        # Simuler le vote du public avec des pourcentages aléatoires
        import random
        total = sum([random.randint(1, 100) for _ in range(4)])
        self.public_votes = [int((random.randint(1, 100) / total) * 100) for _ in range(4)]
        # S'assurer que la somme est 100%
        self.public_votes[0] += 100 - sum(self.public_votes)
        self.jokers['public_vote'] = False
        
    def draw(self):
        """Dessine l'écran"""
        self.screen.fill(WHITE)
        
        # Titre
        draw_text(self.screen, "Question Streamer", self.font, BLACK, 
                 SCREEN_WIDTH // 2, 50, center=True)
        
        # Afficher la question
        if self.current_question:
            question_text = self.current_question['question']
            draw_text(self.screen, question_text, self.small_font, BLACK, 
                     SCREEN_WIDTH // 2, 100, center=True)
            
            # Dessiner les réponses
            button_width = 400
            button_height = 50
            button_margin = 20
            start_y = 200
            
            for i, answer in enumerate(self.current_question['answers']):
                x = (SCREEN_WIDTH - button_width) // 2
                y = start_y + i * (button_height + button_margin)
                
                # Dessiner le bouton de réponse
                color = LIGHT_GRAY
                if self.answered:
                    # Si la question est déjà répondue, mettre en évidence les bonnes réponses
                    if answer == self.current_question['correct_answer']:
                        color = GREEN
                    else:
                        color = GRAY
                        
                pygame.draw.rect(self.screen, color, (x, y, button_width, button_height))
                pygame.draw.rect(self.screen, BLACK, (x, y, button_width, button_height), 2)
                
                draw_text(self.screen, answer, self.small_font, BLACK, 
                         x + button_width // 2, y + button_height // 2, center=True)
            
            # Afficher le timer
            timer_text = f"Temps restant: {self.time_left}s"
            draw_text(self.screen, timer_text, self.small_font, RED, 
                     SCREEN_WIDTH // 2, 150, center=True)
            
            # Afficher les jokers
            if self.jokers['50/50']:
                draw_button(self.screen, "Joker 50/50", (100, SCREEN_HEIGHT - 100), 
                          (150, 40), LIGHT_BLUE, DARK_BLUE)
            else:
                draw_button(self.screen, "Joker 50/50", (100, SCREEN_HEIGHT - 100), 
                          (150, 40), GRAY, DARK_GRAY)
                          
            if self.jokers['public_vote']:
                draw_button(self.screen, "Vote Public", (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100), 
                          (150, 40), LIGHT_BLUE, DARK_BLUE)
            else:
                draw_button(self.screen, "Vote Public", (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100), 
                          (150, 40), GRAY, DARK_GRAY)
            
            # Afficher les résultats du vote public si activé
            if not self.jokers['public_vote'] and sum(self.public_votes) > 0:
                # Afficher les pourcentages
                start_y = 300
                for i, percentage in enumerate(self.public_votes):
                    x = (SCREEN_WIDTH - 300) // 2
                    y = start_y + i * 40
                    
                    # Dessiner la barre de progression
                    pygame.draw.rect(self.screen, GRAY, (x, y, 300, 20))
                    pygame.draw.rect(self.screen, BLUE, (x, y, 300 * percentage / 100, 20))
                    
                    draw_text(self.screen, f"Réponse {i+1}: {percentage}%", self.small_font, 
                             BLACK, x + 150, y + 10, center=True)
        
        # Progression
        progress = (self.question_index / 15) * 100 if self.question_index < 15 else 100
        draw_progress_bar(self.screen, 20, SCREEN_HEIGHT - 30, 
                         SCREEN_WIDTH - 40, 20, progress)
        
        pygame.display.flip()
        
    def next_question(self):
        """Passe à la question suivante"""
        self.question_index += 1
        if self.question_index >= 15:
            # Fin du jeu
            GameState.current_screen = "streamer_results"
        else:
            # Charger la prochaine question
            pass
            
    def get_question_data(self):
        """Retourne les données de la question actuelle"""
        return self.current_question
        
    def set_question_index(self, index):
        """Définit l'index de la question"""
        self.question_index = index