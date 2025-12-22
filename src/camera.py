# src/camera.py
import pygame
import random
from settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2
        
        # 震动
        self.shake_timer = 0
        self.shake_intensity = 0

        # === [核心优化] 静态网格缓存 ===
        # 字典结构：Key=(col, row), Value=Surface (墙的图片)
        # 我们只存图片和位置，不再把它当作 Sprite 对象去遍历
        self.static_grid = {} 

    def trigger_shake(self, intensity=5, duration=20):
        self.shake_intensity = intensity
        self.shake_timer = duration

    def add_static(self, sprite):
        """
        [新增] 专门用于添加静态物体（墙壁）
        将它们记录在网格字典里，而不是普通的 sprite 列表里
        """
        # 计算网格坐标
        col = int(sprite.rect.x // TILE_SIZE)
        row = int(sprite.rect.y // TILE_SIZE)
        # 存入字典
        self.static_grid[(col, row)] = sprite.image

    def custom_draw(self, player):
        # 1. 计算偏移
        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        # 2. 震动偏移
        shake_offset = pygame.math.Vector2()
        if self.shake_timer > 0:
            self.shake_timer -= 1
            shake_offset.x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_offset.y = random.randint(-self.shake_intensity, self.shake_intensity)

        # === [核心优化] 3. 绘制静态网格 (只循环屏幕内的格子) ===
        
        # 计算屏幕对应的网格范围 (Grid Coordinates)
        # 左边界 (最小列号)
        start_col = int((self.offset.x - self.shake_intensity) // TILE_SIZE)
        # 右边界 (最大列号) - 多加1列防止黑边
        end_col = int((self.offset.x + self.display_surface.get_width() + self.shake_intensity) // TILE_SIZE) + 1
        # 上边界
        start_row = int((self.offset.y - self.shake_intensity) // TILE_SIZE)
        # 下边界
        end_row = int((self.offset.y + self.display_surface.get_height() + self.shake_intensity) // TILE_SIZE) + 1

        # 嵌套循环只遍历屏幕内的几十个格子，而不是全图几千个物体
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                if (col, row) in self.static_grid:
                    # 获取墙的图片
                    surf = self.static_grid[(col, row)]
                    # 计算屏幕位置
                    pos_x = col * TILE_SIZE - self.offset.x + shake_offset.x
                    pos_y = row * TILE_SIZE - self.offset.y + shake_offset.y
                    self.display_surface.blit(surf, (pos_x, pos_y))

        # === 4. 绘制动态物体 (Player, Ghost, Particles) ===
        # 这些物体数量少且位置一直变，保持原有逻辑
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset + shake_offset
            self.display_surface.blit(sprite.image, offset_pos)