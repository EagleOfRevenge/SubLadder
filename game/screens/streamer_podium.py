import pygame
from game.constants import *
from game.ui_helpers import draw_text, draw_button

class StreamerPodiumScreen:
    def __init__(self, screen, viewer_stats):
        self.screen = screen
        self.viewer_stats = viewer_stats
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Trier les viewers par nombre de bonnes réponses (du plus haut au plus bas)
        self.sorted_viewers = sorted(
            viewer_stats.items(), 
            key=lambda x: x[1]['correct_answers'], 
            reverse=True
        )
        
        # Prendre les 3 premiers
        self.top_three = self.sorted_viewers[:3]
        
    def draw(self):
        # Fond noir
        self.screen.fill(BLACK)
        
        # Titre
        title = self.font.render("Podium des Viewvers", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Affichage du podium
        y_offset = 150
        
        # Médaille d'or pour le premier
        if len(self.top_three) > 0:
            viewer_name, stats = self.top_three[0]
            gold_text = self.font.render(f"1er - {viewer_name}", True, GOLD)
            self.screen.blit(gold_text, (SCREEN_WIDTH // 2 - 150, y_offset))
            
            score_text = self.small_font.render(f"Bonnes réponses : {stats['correct_answers']}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 150, y_offset + 50))
            
            y_offset += 120
        
        # Médaille d'argent pour le deuxième
        if len(self.top_three) > 1:
            viewer_name, stats = self.top_three[1]
            silver_text = self.font.render(f"2ème - {viewer_name}", True, SILVER)
            self.screen.blit(silver_text, (SCREEN_WIDTH // 2 - 150, y_offset))
            
            score_text = self.small_font.render(f"Bonnes réponses : {stats['correct_answers']}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 150, y_offset + 50))
            
            y_offset += 120
        
        # Médaille de bronze pour le troisième
        if len(self.top_three) > 2:
            viewer_name, stats = self.top_three[2]
            bronze_text = self.font.render(f"3ème - {viewer_name}", True, BRONZE)
            self.screen.blit(bronze_text, (SCREEN_WIDTH // 2 - 150, y_offset))
            
            score_text = self.small_font.render(f"Bonnes réponses : {stats['correct_answers']}", True, WHITE)
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 150, y_offset + 50))
        
        # Si moins de 3 participants
        if len(self.top_three) < 3:
            remaining = 3 - len(self.top_three)
            for i in range(remaining):
                y_offset += 100
                no_participant_text = self.small_font.render("Pas de participant", True, GRAY)
                self.screen.blit(no_participant_text, (SCREEN_WIDTH // 2 - 150, y_offset))
        
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