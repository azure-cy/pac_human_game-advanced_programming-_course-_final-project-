# src/level.py
import pygame
from settings import *
from maps import LEVELS
from sprites import Wall, Door, Coin, Cocoon, Trap, Ghost, Player
from assets import AssetFactory
from particles import TrailSprite, BubbleSprite
from camera import CameraGroup

class Level:
    def __init__(self, level_index):
        self.display_surface = pygame.display.get_surface()
        self.level_index = level_index
        
        # 初始化组
        self.visible_sprites = CameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.damage_sprites = pygame.sprite.Group()
        self.coin_sprites = pygame.sprite.Group()
        self.goal_sprites = pygame.sprite.Group()
        
        self._build_level()

    def _build_level(self):
        """解析地图数据并生成物体"""
        # 获取当前地图数据
        current_map = LEVELS[self.level_index]

        # 生成碰撞网格
        self.obstacle_grid = set()
        for r, row in enumerate(current_map):
            for c, col in enumerate(row):
                if col == 'W' or col == 'O' or col == '^':
                    self.obstacle_grid.add((c, r))

        # 生成玩家
        for r, row in enumerate(current_map):
            for c, col in enumerate(row):
                if col == 'P':
                    self.player = Player(
                        groups=[self.visible_sprites],
                        pos=(c*TILE_SIZE, r*TILE_SIZE),
                        obstacle_sprites=self.obstacle_sprites,
                        wall_grid=self.obstacle_grid,
                        create_particle_func=self.trigger_particle
                    )

        # 生成其他物体
        for r, row in enumerate(current_map):
            for c, col in enumerate(row):
                pos = (c * TILE_SIZE, r * TILE_SIZE)
                
                if col == 'W':
                    # 墙壁：特殊处理，加入静态网格优化
                    wall = Wall([self.obstacle_sprites], pos)
                    self.visible_sprites.add_static(wall)
                
                elif col == 'D':
                    Door(
                        groups=[self.visible_sprites, self.goal_sprites],
                        pos=pos,
                    )
                    
                elif col == 'C':
                    Coin(
                        groups=[self.visible_sprites, self.coin_sprites], # 加入可见组和金币组
                        pos=pos,
                    )
                    
                elif col == 'G':
                    Ghost(
                        groups=[self.visible_sprites, self.damage_sprites], # 加入伤害组
                        pos=pos,
                        obstacle_sprites=self.obstacle_sprites,
                        player=self.player, # 鬼需要知道人在哪
                        wall_grid=self.obstacle_grid
                    )
                    
                elif col == 'O':
                    Cocoon(
                        groups=[self.visible_sprites, self.obstacle_sprites], 
                        pos=pos,
                        player=self.player, # 需要玩家引用来检测距离
                        visible_group=self.visible_sprites,
                        damage_group=self.damage_sprites,
                        obstacle_sprites=self.obstacle_sprites,
                        wall_grid=self.obstacle_grid
                    )
                
                elif col == '^':
                    Trap(
                        groups=[self.visible_sprites, self.obstacle_sprites], 
                        pos=pos, 
                        damage_group=self.damage_sprites, 
                        player=self.player
                    )

    # --- 粒子/特效接口 ---
    def trigger_particle(self, type, pos, surf=None, life_span=0, direction_key=None):
        if type == 'trail' and direction_key:
             self._spawn_trail(pos, direction_key)
        elif type == 'bubble':
             BubbleSprite([self.visible_sprites], pos)

    def _spawn_trail(self, pos, direction_key):
        assets = AssetFactory.get_trail_assets()
        if direction_key in assets:
            surfaces = assets[direction_key]
            TrailSprite([self.visible_sprites], pos, surfaces[0], TRAIL_LIFE_MAIN)
            TrailSprite([self.visible_sprites], pos, surfaces[1], TRAIL_LIFE_UP)
            TrailSprite([self.visible_sprites], pos, surfaces[2], TRAIL_LIFE_DOWN)

    def _check_game_status(self):
        hit_func = pygame.sprite.collide_rect_ratio(0.5)
        if pygame.sprite.spritecollide(self.player, self.damage_sprites, False, collided=hit_func):
            return 'game_over'
        
        door_hit_func = pygame.sprite.collide_rect_ratio(0.8)
        if pygame.sprite.spritecollide(self.player, self.goal_sprites, False, collided=door_hit_func):
            return 'level_complete'
            
        pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
        return 'playing'
    
    def run(self):
        self.visible_sprites.update()
        self.display_surface.fill(COLOR_BG) 
        self.visible_sprites.custom_draw(self.player)
        return self._check_game_status()