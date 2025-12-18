# src/sprites.py
import pygame
import math
from settings import *

class Wall(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surface):
        # groups 是 sprite 组的列表，Pygame 会自动把这个 sprite 加入这些组
        super().__init__(groups)

        # 图片方块
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)

class Door(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surface):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)

class Coin(pygame.sprite.Sprite):
    def __init__(self, groups, pos, frames):
        super().__init__(groups)
        
        # 1. 动画帧
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = COIN_ANIMATION_SPEED
        
        # 2. 初始图像
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(pos[0] + TILE_SIZE//2, pos[1] + TILE_SIZE//2))
        
    def animate(self):
        # 增加索引
        self.frame_index += self.animation_speed
        
        # 循环播放
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
            
        # 切换图片
        self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()

class Cocoon(pygame.sprite.Sprite):
    """
    茧类：
    1. 外观：红色实线边框 + 中间红色“茧”字 (使用 COLOR_GHOST)。
    2. 物理：像墙一样阻挡玩家 (加入 obstacle_sprites)。
    3. 逻辑：检测玩家进入周围 3x3 区域，触发计时，时间到后变身成鬼。
    """
    def __init__(self, groups, pos, player, spawn_ghost_callback):
        # groups 通常包含 [visible_sprites, obstacle_sprites]
        super().__init__(groups)
        
        self.pos = pos
        self.player = player
        self.spawn_ghost_callback = spawn_ghost_callback # 保存生成鬼的回调函数

        # --- 1. 外观绘制 ---
        # 创建透明画布
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=pos)
        
        color = COLOR_GHOST

        # A. 绘制最外围实线边框 (线宽为 2)
        pygame.draw.rect(self.image, color, self.image.get_rect(), width=2)

        # B. 绘制中间的“茧”字
        # 字体大小设置与鬼、陷阱保持一致
        font_size = int(TILE_SIZE * 0.8)
        try:
            font = pygame.font.SysFont(['simhei', 'microsoftyahei', 'pingfangsc'], font_size, bold=True)
        except:
            font = pygame.font.Font(None, font_size)
            
        text_surf = font.render("茧", True, color)
        text_rect = text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.blit(text_surf, text_rect)
        
        # --- 2. 逻辑状态 ---
        self.is_triggered = False
        self.trigger_time = 0
        
        # 定义检测区域：以自身中心为原点，向四周扩展 1 个格子
        # 自身是 1x1，扩展后就是 3x3。
        # inflate(x, y) 是在原有基础上增加宽度和高度。要变成 3倍大小，需要增加 2倍 TILE_SIZE
        self.detection_rect = self.rect.inflate(TILE_SIZE * 2, TILE_SIZE * 2)

    def update(self):
        # 如果已经触发，进入倒计时状态
        if self.is_triggered:
            current_time = pygame.time.get_ticks()
            if current_time - self.trigger_time >= COCOON_SPAWN_DELAY:
                self.hatch() # 孵化
        else:
            # 未触发状态，检测玩家是否进入 3x3 区域
            if self.detection_rect.colliderect(self.player.rect):
                self.trigger()

    def trigger(self):
        """玩家靠近，开始孵化计时"""
        self.is_triggered = True
        self.trigger_time = pygame.time.get_ticks()
        # 可选：触发时的视觉反馈（例如变亮一点）
        # temp_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # temp_surf.fill((255, 50, 50, 100)) # 半透明红蒙版
        # self.image.blit(temp_surf, (0,0))

    def hatch(self):
        """时间到，孵化成鬼"""
        # 1. 调用回调函数在当前位置生成鬼
        # 我们传递自身的左上角坐标
        self.spawn_ghost_callback(self.rect.topleft)
        
        # 2. 销毁自己
        self.kill()

class Spike(pygame.sprite.Sprite):
    """状态机控制的刺：Warning -> Extending -> Active -> Retracting"""
    def __init__(self, groups, start_pos, direction_vector):
        super().__init__(groups)
        
        self.start_pos = pygame.math.Vector2(start_pos)
        self.direction = direction_vector
        
        # 状态管理
        self.state = 'warning'
        self.timer = 0
        self.last_time = pygame.time.get_ticks()
        
        # 移动参数
        self.dist_moved = 0
        self.max_dist = TILE_SIZE
        self.speed = SPIKE_SPEED

        # 绘制图像
        self.image = self._create_spike_image()
        self.rect = self.image.get_rect(topleft=start_pos)

    def _create_spike_image(self):
        """绘制带箭杆的尖锐箭头，背景透明"""
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        c = COLOR_SPIKE
        
        # 假设向右绘制，最后旋转
        arrow_len = 8      # 箭头尖的长度
        arrow_half_h = 3   # 箭头尖的一半宽度 (比较尖)
        shaft_len = 20     # 箭杆长度
        shaft_h = 2        # 箭杆厚度
        
        total_len = arrow_len + shaft_len # 总长 20px
        start_x = (TILE_SIZE - total_len) // 2 # 居中 X
        
        # 三个箭头的 Y 轴中心
        centers_y = [5, 15, 25] 
        
        for cy in centers_y:
            # 1. 绘制箭杆 (矩形)
            # Rect(left, top, width, height)
            shaft_rect = pygame.Rect(start_x, cy - shaft_h//2, shaft_len, shaft_h)
            pygame.draw.rect(surf, c, shaft_rect)
            
            # 2. 绘制箭头尖 (三角形)
            tip_x = start_x + total_len
            base_x = tip_x - arrow_len
            
            points = [
                (tip_x, cy),                 # 尖端
                (base_x, cy - arrow_half_h), # 左上
                (base_x, cy + arrow_half_h)  # 左下
            ]
            pygame.draw.polygon(surf, c, points)

        # 根据方向旋转
        if self.direction.x == -1:   # 左
            surf = pygame.transform.flip(surf, True, False)
        elif self.direction.y == -1: # 上
            surf = pygame.transform.rotate(surf, 90)
        elif self.direction.y == 1:  # 下
            surf = pygame.transform.rotate(surf, -90)
        
        return surf

    def update(self):
        current_time = pygame.time.get_ticks()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # --- 状态机 ---
        if self.state == 'warning':
            self.timer += dt
            if self.timer >= SPIKE_WARNING_TIME:
                self.state = 'extending'
                self.timer = 0
                
        elif self.state == 'extending':
            self.dist_moved += self.speed
            if self.dist_moved >= self.max_dist:
                self.dist_moved = self.max_dist
                self.state = 'active'
                self.timer = 0
            self._update_position()

        elif self.state == 'active':
            self.timer += dt
            if self.timer >= SPIKE_WAIT_TIME:
                self.state = 'retracting'

        elif self.state == 'retracting':
            self.dist_moved -= self.speed
            if self.dist_moved <= 0:
                self.kill()
            self._update_position()

    def _update_position(self):
        move_vec = self.direction * self.dist_moved
        self.rect.topleft = (
            round(self.start_pos.x + move_vec.x),
            round(self.start_pos.y + move_vec.y)
        )

class Trap(pygame.sprite.Sprite):
    """陷阱本体：青色虚线边框 + 旋转的“刺”字"""
    def __init__(self, groups, pos, direction_char, damage_group, player):
        super().__init__(groups)
        
        # 1. 解析方向
        self.direction = pygame.math.Vector2()
        angle = 0 # 文字旋转角度
        if direction_char == '^': 
            self.direction.y = -1
            angle = 0
        elif direction_char == 'v': 
            self.direction.y = 1
            angle = 180
        elif direction_char == '<': 
            self.direction.x = -1
            angle = 90
        elif direction_char == '>': 
            self.direction.x = 1
            angle = -90

        # 2. 准备字体素材
        font_size = int(TILE_SIZE * 0.9)
        try:
            raw_font = pygame.font.SysFont(['simhei', 'microsoftyahei', 'pingfangsc'], font_size)
        except:
            raw_font = pygame.font.Font(None, font_size)
            
        # 预渲染文字并旋转
        raw_text = raw_font.render("刺", True, COLOR_CYAN)
        self.text_surf = pygame.transform.rotate(raw_text, angle)

        # 3. 初始化图像
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self._update_visuals(COLOR_TRAP) # 初始绘制 (深灰底)
        
        # 4. 逻辑依赖
        self.damage_group = damage_group
        self.visible_groups = groups[0]
        self.player = player
        
        self.status = 'idle'
        self.cooldown_timer = 0
        
        # 5. 触发区域
        self.trigger_rect = self.rect.copy()
        self.trigger_rect.x += self.direction.x * TILE_SIZE
        self.trigger_rect.y += self.direction.y * TILE_SIZE
        self.trigger_rect.inflate_ip(-10, -10)

    def _draw_border(self, surface, color):
        """内部辅助：绘制虚线边框"""
        rect = surface.get_rect()
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        dash_len, gap_len = 5, 3
        
        # 定义四条边线段
        lines = [
            ((x, y), (x + w - 1, y)),             # Top
            ((x + w - 1, y), (x + w - 1, y + h - 1)), # Right
            ((x + w - 1, y + h - 1), (x, y + h - 1)), # Bottom
            ((x, y + h - 1), (x, y))              # Left
        ]

        for start, end in lines:
            x1, y1 = start
            x2, y2 = end
            total_dist = math.hypot(x2 - x1, y2 - y1)
            if total_dist == 0: continue
            
            dx = (x2 - x1) / total_dist
            dy = (y2 - y1) / total_dist
            
            curr = 0
            while curr < total_dist:
                p1 = (x1 + dx * curr, y1 + dy * curr)
                end_dist = min(curr + dash_len, total_dist)
                p2 = (x1 + dx * end_dist, y1 + dy * end_dist)
                
                pygame.draw.line(surface, color, p1, p2, 2) # 线宽2
                curr += dash_len + gap_len

    def _update_visuals(self, bg_color):
        """统一绘制逻辑：改变底色，但保留文字和边框"""
        # 1. 填充背景
        self.image.fill(bg_color)
        
        # 2. 绘制边框
        self._draw_border(self.image, COLOR_CYAN)
        
        # 3. 绘制文字 (居中)
        text_rect = self.text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.blit(self.text_surf, text_rect)

    def update(self):
        current_time = pygame.time.get_ticks()
        
        # 冷却检查
        if self.status == 'cooldown':
            if current_time - self.cooldown_timer > TRAP_COOLDOWN:
                self.status = 'idle'
        
        # 触发检查
        elif self.status == 'idle':
            if self.trigger_rect.colliderect(self.player.rect):
                self.trigger_attack(current_time)

    def trigger_attack(self, time):
        self.status = 'cooldown'
        self.cooldown_timer = time
        
        # 生成刺
        Spike(
            groups=[self.visible_groups, self.damage_group],
            start_pos=self.rect.topleft, 
            direction_vector=self.direction
        )

class Ghost(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surface, obstacle_sprites, player):
        super().__init__(groups)
        
        # 1. 图像与位置
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        # 2. 移动属性
        self.direction = pygame.math.Vector2()
        self.speed = GHOST_SPEED
        
        # 3. 依赖注入
        self.obstacle_sprites = obstacle_sprites
        self.player = player  # 持有玩家引用，用于追踪

        # 4. 初始化启动
        self.find_new_direction()  # 刚生成时，立刻思考第一步往哪走

    def move(self):
        # 1. 移动逻辑：先根据当前方向移动
        self.pos += self.direction * self.speed
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        
        # 2. 检查是否“到达”了某个格子的中心
        # 我们计算当前位置相对于网格中心的偏差
        # 如果偏差非常小（说明我们路过了或者刚好踩在中心），就进行校准和转向
        
        # 算出当前所在的网格中心坐标
        center_x = (self.rect.centerx // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
        center_y = (self.rect.centery // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
        
        # 只有当鬼确实在移动时，才检查是否到达新格子
        if self.direction.magnitude() != 0:
            # 检查是否“越过”了中心点 (或者非常接近)
            # 这里的逻辑是：如果我这一帧的移动导致我跨过了中心点，或者刚好落在中心点
            # 我们可以简单判断：距离中心的距离 < 速度的一半 (表示非常接近)
            dist_sq = (self.rect.centerx - center_x)**2 + (self.rect.centery - center_y)**2
            
            # 如果距离非常近（小于移动步长的一半），说明“到站了”
            if dist_sq < (self.speed * 0.5) ** 2:
                # A. 强制对齐 (Snap) - 消除误差，防止歪斜
                self.pos.x = center_x - TILE_SIZE // 2
                self.pos.y = center_y - TILE_SIZE // 2
                self.rect.topleft = (self.pos.x, self.pos.y)
                
                # B. 到站了，思考下一站去哪
                self.find_new_direction()

    def find_new_direction(self):
        """
        AI 思考逻辑：只在到达格子中心时调用一次。
        绝对不会卡住，因为就算死胡同也会返回回头路。
        """
        all_directions = [
            pygame.math.Vector2(0, -1), # 上
            pygame.math.Vector2(0, 1),  # 下
            pygame.math.Vector2(-1, 0), # 左
            pygame.math.Vector2(1, 0)   # 右
        ]
        
        # 1. 找出所有“物理上”能走的路 (不撞墙)
        possible_dirs = []
        for d in all_directions:
            # 预测下一个整格的位置
            check_rect = self.rect.move(d.x * TILE_SIZE, d.y * TILE_SIZE)
            
            blocked = False
            for wall in self.obstacle_sprites:
                if wall.rect.colliderect(check_rect):
                    blocked = True
                    break
            
            if not blocked:
                possible_dirs.append(d)
        
        # 2. 如果无路可走 (理论上不应该，除非出生在墙里)，保持不动
        if not possible_dirs:
            self.direction = pygame.math.Vector2(0, 0)
            return

        # 3. 智能筛选：不想走回头路
        # 如果有多个选择，且其中一个是“回头路”，则剔除回头路
        # 除非是死胡同 (possible_dirs 只有 1 个，且就是回头路)，那必须走
        if len(possible_dirs) > 1:
            # 过滤掉反方向
            # d + self.direction == (0,0) 意味着 d 是反方向
            possible_dirs = [d for d in possible_dirs if d + self.direction != pygame.math.Vector2(0,0)]

        # 4. 贪婪算法：选择离玩家最近的方向
        player_center = pygame.math.Vector2(self.player.rect.center)
        current_center = pygame.math.Vector2(self.rect.center)
        
        # 按距离排序 (距离越小越靠前)
        possible_dirs.sort(key=lambda d: (player_center - (current_center + d * TILE_SIZE)).magnitude())
        
        # 5. 应用新方向
        self.direction = possible_dirs[0]

    def update(self):
        self.move()

class Player(pygame.sprite.Sprite):
    """玩家类"""
    def __init__(self, groups, pos, surface, obstacle_sprites, create_particle_func, line_assets):
        # Sprite初始化函数
        super().__init__(groups)

        # 基础外观
        self.image_base = surface
        self.image = surface
        self.rect = self.image.get_rect(topleft=pos)
        
        # 接收素材字典
        self.line_assets = line_assets
        
        # 移动相关
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.speed = PLAYER_SPEED
        self.status = 'idle'                                 # 状态机: 'idle' 或 'moving'
        self.obstacle_sprites = obstacle_sprites             # 会发生碰撞的位置组
        self.create_particle = create_particle_func          # 创建拖尾或气泡的函数
        self.move_start_time = 0                             # 开始移动的时间
    
    def update_input(self):
        if self.status == 'idle':
            keys = pygame.key.get_pressed()
            move_vector = pygame.math.Vector2()                               # 移动方向向量
            if keys[pygame.K_UP] or keys[pygame.K_w]: move_vector.y = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]: move_vector.y = 1
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]: move_vector.x = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_vector.x = 1

            if move_vector.magnitude() != 0:       # magnitude()获取向量长度
                check_rect = self.rect.move(move_vector.x, move_vector.y)
                
                blocked = False
                for sprite in self.obstacle_sprites:
                    if sprite.rect.colliderect(check_rect):
                        blocked = True
                        break
                
                # 只有前方【没有】障碍物时，才改变状态和外观
                if not blocked:
                    self.direction = move_vector
                    self.status = 'moving'
                    self.move_start_time = pygame.time.get_ticks()
                    self.update_appearance_when_moving() # 只有真能动的时候，才贴上流线图

    def update_appearance_when_moving(self):
        """把对应方向的线条画在人物身上"""
        self.image = self.image_base.copy()            # 重置
        dir_key = (int(self.direction.x), int(self.direction.y))

        if dir_key in self.line_assets:
            # 叠加三条拖尾 (Blit)
            self.image.blit(self.line_assets[dir_key][0], (0, 0))
            self.image.blit(self.line_assets[dir_key][1], (0, 0))
            self.image.blit(self.line_assets[dir_key][2], (0, 0))

    def update_move(self):
        if self.status == 'moving':
            # Level 类收到 direction_key 后，会自动生成 Main/Up/Down 三条线
            dir_key = (int(self.direction.x), int(self.direction.y))
            
            # 让 Level 处理复杂性
            self.create_particle('trail', self.rect.topleft, direction_key=dir_key)
            
            # 位移
            self.pos += self.direction * self.speed
            self.rect.topleft = round(self.pos.x), round(self.pos.y)
            
            # 碰撞检测
            hits = pygame.sprite.spritecollide(self, self.obstacle_sprites, False)
            if hits:
                self.collision_response(hits[0])
    
    def collision_response(self, wall):
        """撞墙后的物理反馈"""
        # 修正位置（贴墙）
        if self.direction.x > 0: self.rect.right = wall.rect.left
        elif self.direction.x < 0: self.rect.left = wall.rect.right
        elif self.direction.y > 0: self.rect.bottom = wall.rect.top
        elif self.direction.y < 0: self.rect.top = wall.rect.bottom
        self.pos = pygame.math.Vector2(self.rect.topleft)

        # 生成撞击气泡(之前在运动时生成)
        current_time = pygame.time.get_ticks()
        if current_time - self.move_start_time > 10:
            bubble_amount = (int)(self.speed * 0.8)
            for _ in range(bubble_amount):
                self.create_particle('bubble', self.rect.center)

        # 状态重置
        self.status = 'idle'
        self.direction = pygame.math.Vector2(0, 0)
        self.image = self.image_base.copy()

    def update(self):
        # 在Level类中每帧调用
        self.update_input()
        self.update_move()