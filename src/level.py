# src/level.py
import pygame
from settings import *
from maps import LEVELS
from sprites import Wall, Door, Coin, Cocoon, Trap, Ghost, Player
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
        
        # 4. 加载资源
        self._load_resources()
        
        # 5. 构建地图
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

    def _load_resources(self):
        """统一管理所有外部图片和程序化生成的素材"""
        # A. 加载外部图片
        self.wall_surf = pygame.image.load(WALL_IMG_PATH).convert_alpha()
        self.player_surf = pygame.image.load(PLAYER_IMG_PATH).convert_alpha()
        # self.ghost_surf = pygame.image.load(GHOST_IMG_PATH).convert_alpha()
        self.door_surf = pygame.image.load(DOOR_IMG_PATH).convert_alpha()

        # B. 程序化生成“鬼”字 Surface
        self.ghost_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        font_size = int(TILE_SIZE * 0.9)
        try:
            # 尝试加载系统黑体
            font = pygame.font.SysFont(['simhei', 'microsoftyahei', 'pingfangsc'], font_size)
        except:
            # 如果失败，回退到默认字体(虽然可能不显示中文，但防报错)
            font = pygame.font.Font(None, font_size)

        text_surf = font.render("鬼", True, (255, 0, 0))
        text_rect = text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
        self.ghost_surf.blit(text_surf, text_rect)
        
        # C. 生成程序化素材
        self.trail_assets = self._generate_trail_assets()
        self.coin_frames = self._generate_coin_assets()

    def _generate_trail_assets(self):
        """
        生成不同长度、不同位置的线条图案。
        返回: 包含四个方向的素材字典
        """
        line_h = 3
        center_y = TILE_SIZE // 2
        
        # 定义线条长度
        main_len = 20
        up_len = 14
        down_len = 16
        
        # --- 1. 绘制基础图 (以向右 vector(1,0) 为基准) ---
        
        # 主线 (Main)
        surf_main = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf_main, COLOR_LINES, (0, center_y - 2, main_len, line_h))
        
        # 上线 (Up)
        surf_up = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf_up, COLOR_LINES, (0, center_y - 11, up_len, line_h))

        # 下线 (Down)
        surf_down = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf_down, COLOR_LINES, (0, center_y + 7, down_len, line_h))

        # --- 2. 生成旋转字典 ---
        # 辅助函数：根据基础图生成四个方向的列表
        def create_rotations(surf):
            return {
                (1, 0):  surf,
                (-1, 0): pygame.transform.flip(surf, True, False),
                (0, -1): pygame.transform.rotate(surf, 90),
                (0, 1):  pygame.transform.rotate(surf, -90),
            }

        # 我们需要返回的是一个“每个方向都包含[Main, Up, Down]”的字典
        # 我们先生成单张图的旋转版，再组合
        dict_main = create_rotations(surf_main)
        dict_up = create_rotations(surf_up)
        dict_down = create_rotations(surf_down)
        
        final_assets = {}
        # 遍历其中一个字典的key (方向)
        for direction in dict_main.keys():
            final_assets[direction] = [
                dict_main[direction], 
                dict_up[direction], 
                dict_down[direction]
            ]
            
        return final_assets
    
    def _generate_coin_assets(self):
        """
        生成像素金币
        """
        frames = []
        
        # --- 配置参数 ---
        pixel_size = 2      # 2px 精度 -> 18px 总大小
        grid_h = 9          # 9行高度 (y=0~8)
        
        # 居中偏移
        center_offset = (TILE_SIZE - grid_h * pixel_size) // 2
        
        c_gold = COLOR_COIN
        c_edge = COLOR_COIN_EDGE

        # 使用奇数序列保证中心对称
        widths = [9, 7, 5, 3, 1]
        
        for w in widths:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # 网格内偏移
            offset_x = (9 - w) // 2
            mid_x = w // 2  # 当前宽度的中心点
            
            for ly in range(grid_h):
                for lx in range(w):
                    
                    # --- 核心优化逻辑：基于中心距离 ---
                    dist = abs(lx - mid_x) # 当前像素距离中心的格数
                    
                    # 1. 核心定义 (Core)
                    # 关键优化：当 w>=7 时，核心保持半径1 (即宽度3)
                    # 只有当 w<7 (变得很窄) 时，核心才缩为半径0 (即宽度1)
                    core_radius = 1 if w >= 7 else 0
                    is_core_area = (dist <= core_radius)
                    
                    # 2. 间隙定义 (Gap)
                    # 间隙永远紧贴核心外侧
                    is_gap_area = (dist == core_radius + 1)
                    
                    # --- 绘制判断 ---
                    should_draw = False
                    
                    # [切角层] y=0, 8
                    if ly == 0 or ly == 8:
                         # 只要不是最边缘(切角)就画
                         if w == 1 or (0 < lx < w - 1): should_draw = True
                             
                    # [实心层] y=1, 7 (加厚)
                    elif ly == 1 or ly == 7:
                        should_draw = True
                        
                    # [桥接层] y=2, 6
                    elif ly == 2 or ly == 6:
                        if w <= 3 or not is_core_area:
                            should_draw = True
                            
                    # [核心层] y=3, 4, 5
                    elif 3 <= ly <= 5:
                        if w <= 3 or (not is_gap_area):
                            should_draw = True

                    # --- 渲染 ---
                    if should_draw:
                        color = c_gold
                        # 动态阴影：每一行的视觉最右侧加深
                        is_edge = (lx == w - 1)
                        if (ly == 0 or ly == 8) and w > 1 and lx == w - 2: is_edge = True
                        
                        if is_edge or ly == 8:
                            color = c_edge
                        
                        # 坐标计算
                        dx = center_offset + (offset_x + lx) * pixel_size
                        dy = center_offset + ly * pixel_size
                        
                        pygame.draw.rect(surf, color, (dx, dy, pixel_size, pixel_size))

            frames.append(surf)

        return frames + frames[-2:0:-1]

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
            'C': self._spawn_coin
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
            surface=self.wall_surf
        )
    
    def _spawn_door(self, pos):
        # 门是静态的，加入 visible 和 goal 组
        Door(
            groups=[self.visible_sprites, self.goal_sprites],
            pos=pos,
            surface=self.door_surf
        )

    def _spawn_coin(self, pos):
        # 导入 Coin 类     
        Coin(
            groups=[self.visible_sprites, self.coin_sprites], # 加入可见组和金币组
            pos=pos,
            frames=self.coin_frames # 传入那套动画素材
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

    def _spawn_ghost(self, pos):
        # 注意：Ghost 需要 obstacle_sprites (防穿墙) 和 player (追踪)
        Ghost(
            groups=[self.visible_sprites, self.damage_sprites], # 加入伤害组
            pos=pos,
            surface=self.ghost_surf,
            obstacle_sprites=self.obstacle_sprites,
            player=self.player # 鬼需要知道人在哪
        )

    def _spawn_player(self, pos):
        self.player = Player(
            groups=[self.visible_sprites], 
            pos=pos, 
            surface=self.player_surf,
            obstacle_sprites=self.obstacle_sprites, 
            create_particle_func=self.trigger_particle, # 传入回调
            line_assets=self.trail_assets
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
        if direction_key in self.trail_assets:
            surfaces = self.trail_assets[direction_key]
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