# src/sprites.py
import pygame
import math
from settings import *

# ==========================================
# 1. 核心工厂类 (AssetFactory)
# ==========================================
class AssetFactory:
    """
    [核心工厂] 负责生成所有基于文字和方框的资源。
    将绘图逻辑集中在此，Sprite 类只需调用即可。
    """

    # 类级别的缓存变量
    _trail_cache = None
    _coin_cache = None

    @classmethod  # 注意：这里建议改用 @classmethod，因为我们要访问 cls._trail_cache
    def get_trail_assets(cls): # 改名：从 create 改为 get，暗示获取（可能是缓存的）
        """获取线条图案（带缓存）"""
        if cls._trail_cache is None:
            # === 如果缓存为空，则执行原来的生成逻辑 ===
            """生成不同长度、不同位置的线条图案"""
            line_h = 3
            center_y = TILE_SIZE // 2
            
            # 定义线条长度
            main_len = 20
            up_len = 14
            down_len = 16
            
            # --- 绘制基础图 ---
            surf_main = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf_main, COLOR_LINES, (0, center_y - 2, main_len, line_h))
            
            surf_up = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf_up, COLOR_LINES, (0, center_y - 11, up_len, line_h))

            surf_down = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(surf_down, COLOR_LINES, (0, center_y + 7, down_len, line_h))

            # --- 生成旋转字典 ---
            def create_rotations(surf):
                return {
                    (1, 0):  surf,
                    (-1, 0): pygame.transform.flip(surf, True, False),
                    (0, -1): pygame.transform.rotate(surf, 90),
                    (0, 1):  pygame.transform.rotate(surf, -90),
                }

            dict_main = create_rotations(surf_main)
            dict_up = create_rotations(surf_up)
            dict_down = create_rotations(surf_down)
            
            final_assets = {}
            for direction in dict_main.keys():
                final_assets[direction] = [
                    dict_main[direction], 
                    dict_up[direction], 
                    dict_down[direction]
                ]

            cls._trail_cache = final_assets
        return cls._trail_cache
    
    @classmethod
    def get_coin_assets(cls): # 改名：从 create 改为 get
        """获取金币动画帧（带缓存）"""
        if cls._coin_cache is None:
            # === 如果缓存为空，则执行原来的生成逻辑 ===
            """生成像素金币动画帧"""
            frames = []
            pixel_size = 2      
            grid_h = 9          
            center_offset = (TILE_SIZE - grid_h * pixel_size) // 2
            
            c_gold = COLOR_COIN
            c_edge = COLOR_COIN_EDGE
            widths = [9, 7, 5, 3, 1]
            
            for w in widths:
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                offset_x = (9 - w) // 2
                mid_x = w // 2 
                
                for ly in range(grid_h):
                    for lx in range(w):
                        dist = abs(lx - mid_x)
                        core_radius = 1 if w >= 7 else 0
                        is_core_area = (dist <= core_radius)
                        is_gap_area = (dist == core_radius + 1)
                        
                        should_draw = False
                        if ly == 0 or ly == 8:
                            if w == 1 or (0 < lx < w - 1): should_draw = True
                        elif ly == 1 or ly == 7:
                            should_draw = True
                        elif ly == 2 or ly == 6:
                            if w <= 3 or not is_core_area: should_draw = True
                        elif 3 <= ly <= 5:
                            if w <= 3 or (not is_gap_area): should_draw = True

                        if should_draw:
                            color = c_gold
                            is_edge = (lx == w - 1)
                            if (ly == 0 or ly == 8) and w > 1 and lx == w - 2: is_edge = True
                            if is_edge or ly == 8: color = c_edge
                            
                            dx = center_offset + (offset_x + lx) * pixel_size
                            dy = center_offset + ly * pixel_size
                            pygame.draw.rect(surf, color, (dx, dy, pixel_size, pixel_size))

                frames.append(surf)
            cls._coin_cache = frames + frames[-2:0:-1]
            
        return cls._coin_cache

    @staticmethod
    def get_font(size, bold=False):
        try:
            return pygame.font.SysFont(['simhei', 'microsoftyahei', 'pingfangsc'], size, bold=bold)
        except:
            return pygame.font.Font(None, size)

    @staticmethod
    def _draw_border(surface, color, style='solid'):
        """
        绘制边框。
        style: 'solid' (实线), 'dashed' (虚线)
        修正：坐标使用 w-1, h-1 确保画在画布内部。
        """
        w, h = surface.get_size()
        # 顺时针四个角，注意 -1 偏移
        pts = [(0, 0), (w - 1, 0), (w - 1, h - 1), (0, h - 1)]

        if style == 'solid':
            pygame.draw.lines(surface, color, True, pts, 2)
        elif style == 'dashed':
            lines = [
                (pts[0], pts[1]), (pts[1], pts[2]), 
                (pts[2], pts[3]), (pts[3], pts[0])
            ]
            dash_len = 5
            gap_len = 4
            for start, end in lines:
                x1, y1 = start
                x2, y2 = end
                dist = math.hypot(x2 - x1, y2 - y1)
                if dist == 0: continue
                
                dx = (x2 - x1) / dist
                dy = (y2 - y1) / dist
                curr = 0
                while curr < dist:
                    p1 = (x1 + dx * curr, y1 + dy * curr)
                    draw_len = min(dash_len, dist - curr)
                    p2 = (p1[0] + dx * draw_len, p1[1] + dy * draw_len)
                    pygame.draw.line(surface, color, p1, p2, 2)
                    curr += dash_len + gap_len

    @staticmethod
    def create_tile(text, color, bg_color=None, border_style='solid', angle=0):
        """
        [万能接口] 生成方块素材
        :param text: 显示的文字 (如 '墙', '我')
        :param color: 文字和边框颜色
        :param bg_color: 背景填充色
        :param border_style: 'solid'(实线), 'dashed'(虚线), 'none'(无边框)
        :param angle: 旋转角度
        """
        image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # 1. 背景
        if bg_color:
            image.fill(bg_color)

        # 2. 边框 (根据样式绘制)
        if border_style != 'none':
            AssetFactory._draw_border(image, color, style=border_style)

        # 3. 文字
        font_size = int(TILE_SIZE * 0.8)
        font = AssetFactory.get_font(font_size, bold=True)
        text_surf = font.render(text, True, color)
        
        # 4. 旋转
        if angle != 0:
            text_surf = pygame.transform.rotate(text_surf, angle)
            
        # 5. 居中绘制
        text_rect = text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
        image.blit(text_surf, text_rect)
        
        return image

    @staticmethod
    def create_spike_bullet(direction, color):
        """生成飞出的刺（子弹形状）"""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        arrow_len, shaft_len = 8, 20
        start_x = (TILE_SIZE - (arrow_len + shaft_len)) // 2
        
        # 画三根刺
        for cy in [5, 15, 25]:
            # 杆
            pygame.draw.rect(surf, color, (start_x, cy - 1, shaft_len, 2))
            # 尖
            pts = [(start_x + 28, cy), (start_x + 20, cy - 3), (start_x + 20, cy + 3)]
            pygame.draw.polygon(surf, color, pts)
            
        # 根据方向旋转
        if direction.x == -1: surf = pygame.transform.flip(surf, True, False)
        elif direction.y == -1: surf = pygame.transform.rotate(surf, 90)
        elif direction.y == 1: surf = pygame.transform.rotate(surf, -90)
        return surf
    
# ==========================================
# 2. 基础类 (提取公共逻辑)
# ==========================================

class BaseStaticSprite(pygame.sprite.Sprite):
    def __init__(self, groups, pos, text, color):
        super().__init__(groups)
        # 统一调用工厂，默认实线边框
        self.image = AssetFactory.create_tile(text, color, border_style='solid')
        self.rect = self.image.get_rect(topleft=pos)


# ==========================================
# 3. 游戏实体类 (Sprites)
# ==========================================

class Wall(BaseStaticSprite):
    def __init__(self, groups, pos):
        # 墙：绿色，实线
        super().__init__(groups, pos, "墙", COLOR_WALL)

class Door(BaseStaticSprite):
    def __init__(self, groups, pos):
        # 门：金色，实线
        super().__init__(groups, pos, "门", COLOR_DOOR)

class Coin(pygame.sprite.Sprite):
    def __init__(self, groups, pos):
        super().__init__(groups)
        self.frames = AssetFactory.get_coin_assets()
        self.idx = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(pos[0]+TILE_SIZE//2, pos[1]+TILE_SIZE//2))
    
    def update(self):
        self.idx = (self.idx + COIN_ANIMATION_SPEED) % len(self.frames)
        self.image = self.frames[int(self.idx)]

class Cocoon(pygame.sprite.Sprite):
    def __init__(self, groups, pos, player, spawn_ghost_callback):
        super().__init__(groups)
        self.pos = pos
        self.player = player
        self.spawn_cb = spawn_ghost_callback
        
        # 茧：红色，实线
        self.image = AssetFactory.create_tile("茧", COLOR_GHOST, border_style='solid')
        self.rect = self.image.get_rect(topleft=pos)
        
        self.is_triggered = False
        self.trigger_time = 0
        self.detection_rect = self.rect.inflate(TILE_SIZE * 2, TILE_SIZE * 2)

    def update(self):
        if self.is_triggered:
            if pygame.time.get_ticks() - self.trigger_time >= COCOON_SPAWN_DELAY:
                self.spawn_cb(self.rect.topleft)
                self.kill()
        elif self.detection_rect.colliderect(self.player.rect):
            self.is_triggered = True
            self.trigger_time = pygame.time.get_ticks()

class Trap(pygame.sprite.Sprite):
    def __init__(self, groups, pos, direction_char, damage_group, player):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.damage_group = damage_group
        self.visible_groups = groups[0]
        self.player = player
        
        # 逻辑属性
        self.angle = 0
        self.direction = pygame.math.Vector2(0, -1)
        self.status = 'idle'
        self.cooldown_timer = 0
        
        # 初始绘制 (青色，虚线)
        self._refresh_visuals()
        self.rect = self.image.get_rect(topleft=pos)

    def _refresh_visuals(self):
        # 动态根据 self.angle 绘制
        self.image = AssetFactory.create_tile(
            "刺", COLOR_CYAN, bg_color=COLOR_TRAP, 
            border_style='dashed', angle=self.angle
        )

    def update(self):
        now = pygame.time.get_ticks()
        if self.status == 'cooldown':
            if now - self.cooldown_timer > TRAP_COOLDOWN:
                self.status = 'idle'
        else:
            self._detect_player(now)

    def _detect_player(self, now):
        vec = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
        if vec.length() > TILE_SIZE * 1.5: return
        
        # 轴对齐判定
        align_x = abs(vec.x) < TILE_SIZE // 2
        align_y = abs(vec.y) < TILE_SIZE // 2
        
        if align_x:
            self.direction = pygame.math.Vector2(0, 1 if vec.y > 0 else -1)
            self.angle = 180 if vec.y > 0 else 0
            self._trigger(now)
        elif align_y:
            self.direction = pygame.math.Vector2(1 if vec.x > 0 else -1, 0)
            self.angle = -90 if vec.x > 0 else 90
            self._trigger(now)

    def _trigger(self, now):
        self.status = 'cooldown'
        self.cooldown_timer = now
        self._refresh_visuals() # 更新文字方向
        Spike([self.visible_groups, self.damage_group], self.rect.topleft, self.direction)

class Spike(pygame.sprite.Sprite):
    def __init__(self, groups, start_pos, direction):
        super().__init__(groups)
        self.start_pos = pygame.math.Vector2(start_pos)
        self.direction = direction
        self.state = 'warning'
        self.timer = 0
        self.last_time = pygame.time.get_ticks()
        self.dist = 0
        self.speed = SPIKE_SPEED
        
        # 生成子弹
        self.image = AssetFactory.create_spike_bullet(direction, COLOR_SPIKE)
        self.rect = self.image.get_rect(topleft=start_pos)
        
        # 状态处理映射
        self.state_handlers = {
            'warning': self._handle_warning,
            'extending': self._handle_extending,
            'active': self._handle_active,
            'retracting': self._handle_retracting
        }

    def update(self):
        now = pygame.time.get_ticks()
        dt = now - self.last_time
        self.last_time = now
        
        handler = self.state_handlers.get(self.state)
        if handler:
            handler(dt)
            
    def _handle_warning(self, dt):
        self.timer += dt
        if self.timer >= SPIKE_WARNING_TIME: 
            self.state = 'extending'; self.timer = 0
            
    def _handle_extending(self, dt):
        self.dist = min(self.dist + self.speed, TILE_SIZE)
        if self.dist >= TILE_SIZE: self.state = 'active'
        self._update_pos()
        
    def _handle_active(self, dt):
        self.timer += dt
        if self.timer >= SPIKE_WAIT_TIME: self.state = 'retracting'; self.timer = 0
        
    def _handle_retracting(self, dt):
        self.dist -= self.speed
        if self.dist <= 0: self.kill()
        self._update_pos()
        
    def _update_pos(self):
        pos = self.start_pos + self.direction * self.dist
        self.rect.topleft = (round(pos.x), round(pos.y))

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, pos, obstacle_sprites, create_particle_func):
        super().__init__(groups)
        
        # 使用工厂生成：黄色 "我"，无边框 (border_style='none')
        self.image_base = AssetFactory.create_tile("我", COLOR_PLAYER_TEXT, border_style='none')
        self.image = self.image_base.copy()
        
        # 统一：使用 pos 初始化
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        self.obstacle_sprites = obstacle_sprites
        self.create_particle = create_particle_func
        self.line_assets = AssetFactory.get_trail_assets()
        self.direction = pygame.math.Vector2()
        self.speed = PLAYER_SPEED
        self.status = 'idle'
        self.move_start_time = 0

        # # === 新增：粒子特效的计时器 ===
        # self.particle_timer = 0 
        # self.particle_cooldown = 150

    def update(self):
        if self.status == 'idle':
            self._input()
        else:
            self._move()

    def _input(self):
        keys = pygame.key.get_pressed()
        d = pygame.math.Vector2()
        if keys[pygame.K_UP] or keys[pygame.K_w]: d.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: d.y = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]: d.x = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: d.x = 1

        if d.length() != 0:
            check_rect = self.rect.move(d.x, d.y)
            if not any(s.rect.colliderect(check_rect) for s in self.obstacle_sprites):
                self.direction = d
                self.status = 'moving'
                self.move_start_time = pygame.time.get_ticks()
                self._update_image_layer()

    def _update_image_layer(self):
        self.image = self.image_base.copy()
        key = (int(self.direction.x), int(self.direction.y))
        if key in self.line_assets:
            for layer in self.line_assets[key]:
                self.image.blit(layer, (0, 0))

    def _move(self):
        key = (int(self.direction.x), int(self.direction.y))
        self.create_particle('trail', self.rect.topleft, direction_key=key)

        # current_time = pygame.time.get_ticks()
        
        # if current_time - self.particle_timer > self.particle_cooldown:
        #     key = (int(self.direction.x), int(self.direction.y))
        #     self.create_particle('trail', self.rect.topleft, direction_key=key)
        #     self.particle_timer = current_time # 重置计时器
        
        self.pos += self.direction * self.speed
        self.rect.topleft = round(self.pos.x), round(self.pos.y)
        
        hit = pygame.sprite.spritecollideany(self, self.obstacle_sprites)
        if hit:
            self._handle_collision(hit)

    def _handle_collision(self, hit):
        if self.direction.x > 0: self.rect.right = hit.rect.left
        elif self.direction.x < 0: self.rect.left = hit.rect.right
        elif self.direction.y > 0: self.rect.bottom = hit.rect.top
        elif self.direction.y < 0: self.rect.top = hit.rect.bottom
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        if pygame.time.get_ticks() - self.move_start_time > 10:
            for _ in range(int(self.speed * 0.8)):
                self.create_particle('bubble', self.rect.center)
        
        self.status = 'idle'
        self.direction = pygame.math.Vector2()
        self.image = self.image_base.copy()

class Ghost(pygame.sprite.Sprite):
    def __init__(self, groups, pos, obstacle_sprites, player):
        super().__init__(groups)
        
        # [修改] 移除 surface 参数
        # 使用工厂生成：红色 "鬼"，无边框
        self.image = AssetFactory.create_tile("鬼", COLOR_GHOST, border_style='none')
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(pos)
        
        self.obstacle_sprites = obstacle_sprites
        self.player = player
        self.direction = pygame.math.Vector2()
        self.speed = GHOST_SPEED
        self.find_dir()

    def update(self):
        self.pos += self.direction * self.speed
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        if self.direction.length() != 0:
            cx = (self.rect.centerx // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
            cy = (self.rect.centery // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
            if (self.rect.centerx-cx)**2 + (self.rect.centery-cy)**2 < (self.speed*0.5)**2:
                self.pos.x = cx - TILE_SIZE // 2; self.pos.y = cy - TILE_SIZE // 2
                self.rect.topleft = (self.pos.x, self.pos.y)
                self.find_dir()

    def find_dir(self):
        dirs = [pygame.math.Vector2(0,-1), pygame.math.Vector2(0,1), 
                pygame.math.Vector2(-1,0), pygame.math.Vector2(1,0)]
        valid = []
        for d in dirs:
            if not any(w.rect.colliderect(self.rect.move(d.x*TILE_SIZE, d.y*TILE_SIZE)) for w in self.obstacle_sprites):
                valid.append(d)
        
        if not valid: self.direction = pygame.math.Vector2(); return
        if len(valid) > 1:
            valid = [d for d in valid if d + self.direction != pygame.math.Vector2(0,0)]
        
        target = pygame.math.Vector2(self.player.rect.center)
        curr = pygame.math.Vector2(self.rect.center)
        valid.sort(key=lambda d: (target - (curr + d*TILE_SIZE)).length())
        self.direction = valid[0]