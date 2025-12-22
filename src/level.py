# src/level.py
import pygame
from settings import *
from maps import LEVELS
from sprites import Wall, Door, Coin, Cocoon, Trap, Ghost, Player
from sprites import AssetFactory
from particles import TrailSprite, BubbleSprite
from camera import CameraGroup

class Level:
    def __init__(self, level_index):
        # 1. 获取显示表面
        self.display_surface = pygame.display.get_surface()
        
        # 2. 记录当前关卡索引 (方便重试或加载下一关)
        self.level_index = level_index
        
        # 3. 初始化精灵组
        self._init_sprite_groups()
        
        # 4. 构建地图
        self._build_level()

    def _init_sprite_groups(self):
        """初始化精灵组，按功能分类"""
        # 渲染组
        self.visible_sprites = CameraGroup()   # 使用CameraGroup()，用于相机移动
        
        # 物理碰撞组 (阻挡移动)
        self.obstacle_sprites = pygame.sprite.Group()
        
        # 伤害组 (碰到就死: 鬼, 刺)
        self.damage_sprites = pygame.sprite.Group()

        # 消失组（碰到后组消失）
        self.coin_sprites = pygame.sprite.Group()
        
        # 目标组 (碰到就赢: 门)
        self.goal_sprites = pygame.sprite.Group()

    def _build_level(self):
        """解析地图数据并生成物体"""
        # 获取当前地图数据
        current_map = LEVELS[self.level_index]

        # --- 第一遍扫描：只生成玩家 (Player) ---
        # 必须确保 self.player 先存在，鬼才能追踪它
        for row_index, row in enumerate(current_map):
            for col_index, col in enumerate(row):
                if col == 'P':
                    pos = (col_index * TILE_SIZE, row_index * TILE_SIZE)
                    self._spawn_player(pos)

        # --- 第二遍扫描：生成其他物体 (Wall, Ghost, Door) ---
        # 此时 self.player 已经绝对存在了
        spawn_map = {
            'W': self._spawn_wall,
            'G': self._spawn_ghost,
            'D': self._spawn_door,
            'C': self._spawn_coin,
            'O': self._spawn_cocoon,
        }
        trap_chars = ['^', 'v', '<', '>'] # 陷阱符号列表

        for row_index, row in enumerate(current_map):
            for col_index, col in enumerate(row):
                pos = (col_index * TILE_SIZE, row_index * TILE_SIZE)
                tile_type = col
                
                if tile_type in spawn_map:
                    spawn_map[tile_type](pos)
                elif tile_type in trap_chars:
                    self._spawn_trap(pos, tile_type)

    # --- 生成具体的实体 (Spawner Functions) ---

    def _spawn_wall(self, pos):
        Wall(
            groups=[self.visible_sprites, self.obstacle_sprites], 
            pos=pos, 
        )
    
    def _spawn_door(self, pos):
        # 门是静态的，加入 visible 和 goal 组
        Door(
            groups=[self.visible_sprites, self.goal_sprites],
            pos=pos,
        )

    def _spawn_coin(self, pos):
        # 导入 Coin 类     
        Coin(
            groups=[self.visible_sprites, self.coin_sprites], # 加入可见组和金币组
            pos=pos,
        )
    
    def _spawn_trap(self, pos, direction_char):
        """生成陷阱"""
        Trap(
            groups=[self.visible_sprites, self.obstacle_sprites], # 陷阱本身是障碍物(墙)
            pos=pos,
            direction_char=direction_char,
            damage_group=self.damage_sprites, # 传入伤害组，让它能生成刺
            player=self.player                # 传入玩家，让它能检测位置
        )
    
    def _spawn_cocoon(self, pos):
        """新增：生成茧"""
        Cocoon(
            # 1. 加入可见组和障碍物组 (因为它像墙一样挡路)
            groups=[self.visible_sprites, self.obstacle_sprites], 
            pos=pos,
            player=self.player, # 需要玩家引用来检测距离
            spawn_ghost_callback=self._spawn_ghost 
        )

    def _spawn_ghost(self, pos):
        # 注意：Ghost 需要 obstacle_sprites (防穿墙) 和 player (追踪)
        Ghost(
            groups=[self.visible_sprites, self.damage_sprites], # 加入伤害组
            pos=pos,
            obstacle_sprites=self.obstacle_sprites,
            player=self.player # 鬼需要知道人在哪
        )

    def _spawn_player(self, pos):
        self.player = Player(
            groups=[self.visible_sprites], 
            pos=pos, 
            obstacle_sprites=self.obstacle_sprites, 
            create_particle_func=self.trigger_particle, # 传入回调
        )

    # --- 粒子/特效接口 ---

    def trigger_particle(self, type, pos, surf=None, life_span=0, direction_key=None):
        """
        统一的粒子触发接口 (原 create_particle)
        参数:
            type: 'trail' 或 'bubble'
            pos: 位置
            surf: (可选) 拖尾图片，如果是多重拖尾则不需要传
            life_span: (可选) 生命周期
            direction_key: (可选) 用于查找拖尾素材的方向键
        """
        if type == 'trail' and direction_key:
            self._spawn_trail(pos, direction_key)
        elif type == 'bubble':
            self._spawn_bubble(pos)

    def _spawn_trail(self, pos, direction_key):
        """内部方法：专门处理复杂的拖尾生成"""
        assets = AssetFactory.get_trail_assets()

        if direction_key in assets:
            surfaces = assets[direction_key]
            # 依次生成三条拖尾
            TrailSprite([self.visible_sprites], pos, surfaces[0], TRAIL_LIFE_MAIN)
            TrailSprite([self.visible_sprites], pos, surfaces[1], TRAIL_LIFE_UP)
            TrailSprite([self.visible_sprites], pos, surfaces[2], TRAIL_LIFE_DOWN)

    def _spawn_bubble(self, pos):
        """内部方法：生成气泡"""
        BubbleSprite([self.visible_sprites], pos)

    # --- 核心逻辑：裁判系统 ---

    def _check_game_status(self):
        """检测胜利或失败"""
        
        # 1. 检测失败 (玩家碰到 伤害组)
        # 定义一个回调函数，缩放比率为
        hit_func = pygame.sprite.collide_rect_ratio(0.5)
        if pygame.sprite.spritecollide(self.player, self.damage_sprites, False, collided=hit_func):
            return 'game_over'

        # 2. 检测胜利 (玩家碰到 目标组)
        # 门也建议稍微进深一点才算赢，防止擦边误触
        door_hit_func = pygame.sprite.collide_rect_ratio(0.8)
        if pygame.sprite.spritecollide(self.player, self.goal_sprites, False, collided=door_hit_func):
            return 'level_complete'
        
        # 3. 碰到金币就删除
        # spritecollide(sprite, group, dokill) -> dokill=True 表示碰到就删除金币
        hits = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
        if hits:
            pass

        return 'playing'
    
    # --- 相机窗口移动 ---

    def shake_screen(self, intensity=5, duration=20):
        """窗口震动函数"""
        self.visible_sprites.trigger_shake(intensity, duration)

    # --- 游戏主循环调用 ---

    def run(self):
        """
        运行一帧游戏逻辑。
        Returns:
            str: 'playing' | 'game_over' | 'level_complete'
        """
        # 1. 更新逻辑（自动调用visible_sprites中所有类的update()方法）
        self.visible_sprites.update()
        
        # 2. 绘制画面
        self.display_surface.fill(COLOR_BG) 
        self.visible_sprites.custom_draw(self.player)
        
        # 3. 检查并返回状态
        return self._check_game_status()