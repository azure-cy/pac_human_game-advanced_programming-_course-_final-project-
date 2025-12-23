# src/assets.py
import pygame
import math
from settings import *

class AssetFactory:
    """
    [资源工厂] 
    独立负责所有图形资源的生成与缓存 (享元模式)。
    """
    #缓存池
    _trail_cache = None
    _coin_cache = None
    _bubble_cache = None 
    _font_cache = {}    # 缓存字体对象
    _tile_cache = {}    # 缓存绘制好的方块 Surface
    _bullet_cache = {}  # 缓存子弹 Surface

    @classmethod
    def get_trail_assets(cls):
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
    def get_coin_assets(cls):
        """获取金币动画帧（带缓存）"""
        if cls._coin_cache is None:
            # === 如果缓存为空，则执行生成逻辑 ===
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
    
    @classmethod
    def get_bubble_asset(cls, diameter, color):
        """获取气泡资源（享元模式)"""
        if cls._bubble_cache is None:
            cls._bubble_cache = {}
        
        key = (diameter, color)
        if key not in cls._bubble_cache:
            surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            radius = diameter // 2
            pygame.draw.circle(surf, color, (radius, radius), radius)
            cls._bubble_cache[key] = surf
            
        return cls._bubble_cache[key]

    @classmethod
    def get_font(cls, size, bold=False):
        key = (size, bold)
        if key not in cls._font_cache:
            try:
                # 尝试加载系统字体
                font = pygame.font.SysFont(['simhei', 'microsoftyahei', 'pingfangsc'], size, bold=bold)
            except:
                # 失败则使用默认字体
                font = pygame.font.Font(None, size)
            cls._font_cache[key] = font
            
        return cls._font_cache[key]

    @classmethod
    def create_tile(cls, text, color, bg_color=None, border_style='solid', angle=0):
        """
        :param text: 显示的文字 (如 '墙', '我')
        :param color: 文字和边框颜色
        :param bg_color: 背景填充色
        :param border_style: 'solid'(实线), 'dashed'(虚线), 'none'(无边框)
        :param angle: 旋转角度
        """
        key = (text, color, bg_color, border_style, angle)
        if key not in cls._tile_cache:
            image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            if bg_color:
                image.fill(bg_color)

            if border_style != 'none':
                AssetFactory._draw_border(image, color, style=border_style)

            font_size = int(TILE_SIZE * 0.8)
            font = AssetFactory.get_font(font_size, bold=True)
            text_surf = font.render(text, True, color)
            
            if angle != 0:
                text_surf = pygame.transform.rotate(text_surf, angle)
                
            text_rect = text_surf.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2))
            image.blit(text_surf, text_rect)

            cls._tile_cache[key] = image
        
        return cls._tile_cache[key]

    @classmethod
    def create_spike_bullet(cls, direction, color):
        """生成飞出的刺"""
        dir_key = (direction.x, direction.y)
        key = (dir_key, color)

        if key not in cls._bullet_cache:
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

            cls._bullet_cache[key] = surf
            
        return cls._bullet_cache[key]
    
    @staticmethod
    def _draw_border(surface, color, style='solid'):
        """
        绘制边框。
        style: 'solid' (实线), 'dashed' (虚线)
        修正：坐标使用 w-1, h-1 确保画在画布内部。
        """
        w, h = surface.get_size()
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