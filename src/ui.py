# src/ui.py
import pygame
from settings import *

class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font_title = pygame.font.Font(None, FONT_SIZE_TITLE)
        self.font_sub = pygame.font.Font(None, FONT_SIZE_SUB)
    
    def show_level_start(self, level_index):
        """绘制关卡开始前的提示画面"""
        
        # 1. 遮罩层
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.display_surface.blit(overlay, (0, 0))

        # 2. 弹窗框
        box_rect = pygame.Rect(0, 0, UI_BOX_WIDTH, UI_BOX_HEIGHT)
        box_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.display_surface, UI_BOX_BG_COLOR, box_rect)
        pygame.draw.rect(self.display_surface, UI_BOX_BORDER_COLOR, box_rect, UI_BORDER_WIDTH)

        # 3. 动态文字: LEVEL X
        title_text = f"LEVEL {level_index}"
        title_surf = self.font_title.render(title_text, True, COLOR_TEXT_MAIN)
        title_rect = title_surf.get_rect(center=(box_rect.centerx, box_rect.centery - 30))
        self.display_surface.blit(title_surf, title_rect)

        # 4. 提示文字: Press ENTER
        sub_surf = self.font_sub.render("Press ENTER to Start", True, COLOR_TEXT_SUB)
        sub_rect = sub_surf.get_rect(center=(box_rect.centerx, box_rect.centery + 10))
        self.display_surface.blit(sub_surf, sub_rect)

    def show_game_over(self):
        """绘制游戏结束画面"""
        
        # --- 第一层：全屏半透明遮罩 (背景变暗) ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150) 
        self.display_surface.blit(overlay, (0, 0))

        # --- 第二层：中心弹窗框 (Box) ---
        # 1. 定义矩形区域 (居中)
        box_rect = pygame.Rect(0, 0, UI_BOX_WIDTH, UI_BOX_HEIGHT)
        box_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # 2. 画半透明背景
        # A. 创建一个新的 Surface (画布)，大小与 box_rect 一致
        transparent_surf = pygame.Surface((UI_BOX_WIDTH, UI_BOX_HEIGHT))
        transparent_surf.set_alpha(150)
        transparent_surf.fill(UI_BOX_BG_COLOR)
        self.display_surface.blit(transparent_surf, box_rect.topleft)

        # 3. 画框的边框 (保持不透明)
        pygame.draw.rect(self.display_surface, UI_BOX_BORDER_COLOR, box_rect, UI_BORDER_WIDTH)

        # --- 第三层：文字 (Text) ---
        # 注意：文字的位置现在应该参考 box_rect.center
        
        # 标题 "GAME OVER"
        title_surf = self.font_title.render("GAME OVER", True, COLOR_TEXT_MAIN)
        # 让标题位于框中心偏上一点
        title_rect = title_surf.get_rect(center=(box_rect.centerx, box_rect.centery - 20))
        self.display_surface.blit(title_surf, title_rect)

        # 提示 "Press SPACE..."
        sub_surf = self.font_sub.render("Press SPACE to Restart", True, COLOR_TEXT_SUB)
        # 让提示位于框中心偏下一点
        sub_rect = sub_surf.get_rect(center=(box_rect.centerx, box_rect.centery + 20))
        self.display_surface.blit(sub_surf, sub_rect)