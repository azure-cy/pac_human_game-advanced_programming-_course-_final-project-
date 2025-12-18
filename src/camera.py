# src/camera.py
import pygame
import random
from settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        
        # 1. 摄像机偏移量 (这是核心)
        self.offset = pygame.math.Vector2()
        
        # 2. 屏幕中心点 (用于计算玩家应该在的位置)
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2

        # 3. 屏幕震动参数
        self.shake_timer = 0
        self.shake_intensity = 0

    def trigger_shake(self, intensity=5, duration=20):
        """触发屏幕震动"""
        self.shake_intensity = intensity
        self.shake_timer = duration

    def custom_draw(self, player):
        """
        核心绘制逻辑：
        1. 计算 玩家中心 与 屏幕中心 的差距 -> 得到 offset
        2. 如果有震动，给 offset 加上随机值
        3. 遍历所有精灵，减去 offset 后再绘制
        """
        
        # --- A. 计算基础跟随偏移 ---
        # 目标：让 player.rect.center 位于屏幕中心 (half_w, half_h)
        # 公式：offset = 玩家当前位置 - 屏幕中心位置
        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        # --- B. 计算震动偏移 ---
        shake_offset = pygame.math.Vector2()
        if self.shake_timer > 0:
            self.shake_timer -= 1
            # 在 (-intensity, +intensity) 之间随机抖动
            shake_offset.x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_offset.y = random.randint(-self.shake_intensity, self.shake_intensity)

        # --- C. 绘制所有精灵 ---
        # 提示：如果你的游戏有前后遮挡关系（比如树木遮挡玩家），
        # 可以用 sorted(self.sprites(), key=lambda s: s.rect.centery) 来排序绘制
        
        for sprite in self.sprites():
            # 原始位置 - 摄像机偏移 + 震动偏移 = 屏幕上的最终位置
            offset_pos = sprite.rect.topleft - self.offset + shake_offset
            self.display_surface.blit(sprite.image, offset_pos)