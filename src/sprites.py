# src/sprites.py
import pygame
import math
from settings import *
from assets import AssetFactory

# ==========================================
# 基础类 (提取公共逻辑)
# ==========================================

class BaseStaticSprite(pygame.sprite.Sprite):
    def __init__(self, groups, pos, text, color):
        super().__init__(groups)
        # 统一调用工厂，默认实线边框
        self.image = AssetFactory.create_tile(text, color, border_style='solid')
        self.rect = self.image.get_rect(topleft=pos)


# ==========================================
# 游戏实体类 (Sprites)
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