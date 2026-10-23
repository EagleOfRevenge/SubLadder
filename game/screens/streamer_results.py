import pygame
import json
from game.constants import *
from game.ui_helpers import draw_text, draw_button

class StreamerResultsScreen:
    def __init__(self, screen, questions_data, streamer_answers, viewer_stats):
        self.screen = screen
        self.questions_data = questions_data
        self.streamer_answers = streamer_answers
        self.viewer_stats = viewer_stats
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
        # Calcul des pourcentages de votes pour chaque réponse
        self.vote_percentages = []
        for question in questions_data:
            total_votes = sum(question.get('votes', [0, 0, 0, 0]))
            percentages = [int((vote / total_votes) * 100) if total_votes > 0 else 0 
                          for vote in question.get('votes', [0, 0, 0, 0])]
            self.vote_percentages.append(percentages)
        
    def draw(self):
        # Fond noir
        self.screen.fill(BLACK)
        
        # Titre
        title = self.font.render("Résultats du Quiz", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Affichage des résultats pour chaque question
        y_offset = 100
        for i, (question, streamer_answer, percentages) in enumerate(
            zip(self.questions_data, self.streamer_answers, self.vote_percentages)):
            
            # Numéro de la question
            question_num = self.small_font.render(f"Question {i+1}", True, WHITE)
            self.screen.blit(question_num, (50, y_offset))
            
            # Énoncé de la question
            question_text = self.small_font.render(question['question'], True, LIGHT_GRAY)
            self.screen.blit(question_text, (50, y_offset + 30))
            
            # Bonne réponse
            correct_answer = question['correct_answer']
            correct_text = self.small_font.render(f"Bonne réponse : {correct_answer}", True, GREEN)
            self.screen.blit(correct_text, (50, y_offset + 60))
            
            # Réponse du streamer
            streamer_text = self.small_font.render(f"Réponse streamer : {streamer_answer}", True, ORANGE)
            self.screen.blit(streamer_text, (50, y_offset + 90))
            
            # Pourcentages de votes pour chaque réponse
            y_vote = y_offset + 120
            for j, percentage in enumerate(percentages):
                answer_text = question['options'][j]
                vote_text = self.small_font.render(f"{answer_text} : {percentage}%", True, LIGHT_GRAY)
                self.screen.blit(vote_text, (50, y_vote + j * 30))
            
            # Ligne de séparation
            pygame.draw.line(self.screen, GRAY, (50, y_offset + 220), 
                           (SCREEN_WIDTH - 50, y_offset + 220), 1)
            
            y_offset += 250
            
        # Bouton pour revenir au menu principal
        back_button = draw_button(self.screen, "Menu Principal", 
                                SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        
        return back_button
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Vérifier si le bouton "Menu Principal" est cliqué
            if (SCREEN_WIDTH // 2 - 100 <= mouse_pos[0] <= SCREEN_WIDTH // 2 + 100 and
                SCREEN_HEIGHT - 100 <= mouse_pos[1] <= SCREEN_HEIGHT - 50):
                return "main_menu"
        return None