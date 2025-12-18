# src/settings.py
import os

# 屏幕设置
SCREEN_WIDTH = 420    # 游戏屏幕宽度（单位：像素）
SCREEN_HEIGHT = 600   # 游戏屏幕高度（单位：像素）
TILE_SIZE = 30        # 地图中小格子边长（单位：像素）；宽度14个，高度20个
FPS = 60              # 帧率（每秒的刷新次数）
COLOR_BG = (0, 0, 0)  # 黑色背景

# ui弹窗设置
COLOR_TEXT_MAIN = (20, 20, 20)        # 标题颜色：白色
COLOR_TEXT_SUB = (20, 20, 20)         # 副标题颜色：浅灰
FONT_SIZE_TITLE = 40                  # 标题大字
FONT_SIZE_SUB = 20                    # 副标题小字
UI_BOX_WIDTH = 200                    # 画框宽度
UI_BOX_HEIGHT = 100                   # 画框高度
UI_BOX_BG_COLOR = (220, 220, 220)     # 浅灰色底
UI_BOX_BORDER_COLOR = (255, 255, 255) # 白色边框
UI_BORDER_WIDTH = 3                   # 边框粗细

# 移动速度
PLAYER_SPEED = 10  # 确保能整除 TILE_SIZE 以保证移动平滑
GHOST_SPEED = 1    # 鬼的移动速度

# 茧和鬼的设置
COLOR_GHOST = (255, 0, 0)    # 字的颜色：红色
COCOON_SPAWN_DELAY = 1000    # 茧孵化所需时间 (毫秒)

# 陷阱和刺的设置
TRAP_COOLDOWN = 3000         # 陷阱总冷却时间 (要比刺的整套动作长)
SPIKE_WARNING_TIME = 500     # 玩家触发后，刺伸出前的延迟 (预警时间)
SPIKE_WAIT_TIME = 1000       # 刺伸出后停留的时间
SPIKE_SPEED = 3              # 刺移动速度 (像素/帧)

COLOR_TRAP = (0, 0, 0)       # 陷阱背景颜色： 黑色
COLOR_SPIKE = (200, 50, 50)  # 刺的颜色 (暗红)
COLOR_CYAN = (0, 255, 255)   # 青色 (用于文字和边框)

# 金币设置
COLOR_COIN = (255, 215, 0)      # 金色
COLOR_COIN_EDGE = (200, 150, 0) # 深金色 (用于描边)
COIN_ANIMATION_SPEED = 0.15     # 动画播放速度

# 拖尾设置
TRAIL_LIFE_MAIN = int((2 * TILE_SIZE) / PLAYER_SPEED)     # 中间拖尾的生命周期
TRAIL_LIFE_UP = int((1.3 * TILE_SIZE) / PLAYER_SPEED)     # 上侧拖尾生命周期
TRAIL_LIFE_DOWN = int((1.5 * TILE_SIZE) / PLAYER_SPEED)   # 下侧拖尾生命周期
COLOR_LINES = (218, 165, 32)                              # 黄色

# 气泡设置
BUBBLE_COLOR = (211, 211, 211)                            # 浅灰色

# 图片资源位置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # 获取当前项目的根目录；abspath()获取当前文件的绝对路径；dirname()获取父目录，即去除最后一个路径
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')                             # 添加资源文件夹路径
GRAPHICS_DIR = os.path.join(ASSETS_DIR, 'graphics')

WALL_IMG_PATH = os.path.join(GRAPHICS_DIR, 'wall.png')                    # 墙图片位置
PLAYER_IMG_PATH = os.path.join(GRAPHICS_DIR, 'player.png')                # 玩家图片位置
GHOST_IMG_PATH = os.path.join(GRAPHICS_DIR, 'ghost.png')                  # 鬼图片位置
DOOR_IMG_PATH = os.path.join(GRAPHICS_DIR, 'door.png')                    # 门图片位置