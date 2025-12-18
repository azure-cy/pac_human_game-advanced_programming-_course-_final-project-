# src/particles.py
import pygame
import random
from settings import *
"""特效sprites类"""

class TrailSprite(pygame.sprite.Sprite):
    """玩家移动时的拖尾类"""
    def __init__(self, groups, pos, surf, life_time):
        super().__init__(groups)
        # 直接使用传入的图案 surface
        self.image = surf.copy() 
        self.rect = self.image.get_rect(topleft=pos)
        
        self.timer = life_time           # 拖尾存在的生命周期
        self.original_alpha = 255        # 初始透明度；255为最大

    def update(self):
        self.timer -= 1
        
        if self.timer <= 0:
            self.kill()

class BubbleSprite(pygame.sprite.Sprite):
    """玩家碰撞时产生的气泡类"""
    def __init__(self, groups, center_pos):
        super().__init__(groups)
        # 随机大小：直径 (2px - 6px)
        diameter = random.randint(6, 9)
        radius = diameter // 2

        # 在透明画布的中心画一个圆
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)       # 创建一个支持透明通道的 Surface (SRCALPHA 是关键)，这样圆的四个角落才是透明的，而不是黑色的
        pygame.draw.circle(self.image, BUBBLE_COLOR, (radius, radius), radius)   # 参数：(画布, 颜色, 圆心坐标, 半径)
        
        # 初始位置：在角色中心附近随机偏移
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        self.rect = self.image.get_rect(center=(center_pos[0] + offset_x, center_pos[1] + offset_y))

        # 爆炸运动逻辑 (360度随机)
        # 随机角度 0-360
        angle = random.uniform(0, 360)
        speed = random.uniform(3, 5)     # 初始速度
        # 使用向量旋转计算速度分量
        self.direction = pygame.math.Vector2(1, 0).rotate(angle) * speed
        
        self.timer = random.randint(15, 20) # 寿命

    def update(self):
        self.rect.center += self.direction
        self.timer -= 1
        
        # 模拟摩擦力：速度越来越慢
        self.direction *= 0.8 

        if self.timer <= 0:
            self.kill()