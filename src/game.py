# src/game.py
import pygame, sys
from settings import *
from level import Level
from maps import LEVELS
from ui import UI

class Game:
    def __init__(self):
        # 初始化 Pygame
        pygame.init()

        # 创建显示窗口
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man Game")

        # 设置时钟
        self.clock = pygame.time.Clock()

        # 实例化Level
        self.current_level_index = 1
        self.level = Level(self.current_level_index)    # 加载第0关
        self.game_state = 'level_start'                 # 游戏状态level_start, playing, game_over
        
        # 实例化ui
        self.ui = UI()

    def run(self):
        while True:
            # --- 事件监听 ---
            for event in pygame.event.get():
                # 如果检测到用户点击了窗口的关闭按钮，退出程序
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # 在GAME_OVER状态下检测到用户按下空格键，重启关卡
                if self.game_state == 'game_over':
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.restart_level()
                
                # 关卡开始前,按回车进入游戏
                if self.game_state == 'level_start':
                    if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER):
                        self.game_state = 'playing'
        
            # --- 状态分发 ---      
            if self.game_state == 'playing':
                self.screen.fill(COLOR_BG)
                
                # 运行 Level 并获取返回值
                level_signal = self.level.run()
                
                if level_signal == 'game_over':
                    self.game_state = 'game_over'       
                elif level_signal == 'level_complete':
                    self.next_level()

            elif self.game_state == 'game_over':
                # 1. 画 Level (为了背景显示最后死掉的画面，而不是黑屏)
                self.level.visible_sprites.custom_draw(self.level.player) 
                
                # 2. 调用我们在 UI 类里写好的函数
                self.ui.show_game_over()
            
            elif self.game_state == 'level_start':
                self.level.visible_sprites.custom_draw(self.level.player) 
                
                # 绘制 LEVEL X 弹窗
                self.ui.show_level_start(self.current_level_index)
                
            pygame.display.update()

            # --- 控制循环时间 ---
            self.clock.tick(FPS)
    
    def restart_level(self):
        """重试：重新实例化当前关卡"""
        self.level = Level(self.current_level_index)
        self.game_state = 'playing'

    def next_level(self):
        """下一关"""
        self.current_level_index += 1
        # 检查是否还有下一关
        if self.current_level_index in LEVELS:
            self.level = Level(self.current_level_index)
            self.game_state = 'level_start'
        else:
            self.current_level_index = 0 
            self.restart_level()