# src/map_generator.py
import random
from collections import deque

# ==============================================================================
#                                  配置参数
# ==============================================================================
MAP_CONFIG = {
    # 物品生成数量 (在你的地图骨架上填充多少东西)
    "coin_groups": 10,           
    "coin_group_size": (3, 6),  
    
    "trap_groups": 8,           
    "trap_group_size": (2, 4),  
    
    "cocoon_groups": 5,         
    "cocoon_group_size": (1, 1),
    
    "wall_spike_groups": 10,     
    "wall_spike_len": (2, 5),
    
    # 变异参数
    "enable_flip": True,       # 是否允许地图镜像翻转 (增加重玩性)
}

# 你的“完美地图”母版 (只保留墙壁结构，物品会被重置)
# 我把你的地图里的物品都替换成了 '.'，只保留了 W，作为纯净骨架
BASE_TEMPLATE = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W..............W.....W.........W",
    "W.....W...W....W.....W......WW.W",
    "W.WW..W...W....W.WC..W......WW.W",
    "W..W..W.WWWWWWW.WC.WWW.W.......W",
    "W..W..W...W.....WC.W...W..W....W",
    "W..W..W...W.....W.WW...W..W....W",
    "W..W.WW...W..WWWW..W...WW.W.WWWW",
    "WW.W..W...W...CW...W...WW....CW.",
    "W..W..W.WWW...CW...WW....W.....W",
    "W..W..W..WW...WWW.WW.....W.....W",
    "W..W..W..W....W...WW.....W.....W",
    "W..W..W..W....W...WW.....W.....W",
    "W..W..WWW.W...W...WW.....W.....W",
    "W..W..W..CW...W...W.WWW..W.....W",
    "W..WW.W..CW...W.......W..WWWW..W",
    "W.WW..W..CW...W.......W..W.....W",
    "W.WWW.W..CW...W.......W..W.....W",
    "W..W..W..CW...WWWWWWW.W..W.....W",
    "W..W..W..WW...W.......W..W.....W",
    "W..W..W..W....W.......WW.W.....W",
    "W..W..W..W.........W....WW.W..WW",
    "W..W..W..WW........W....W..W...W",
    "W..W..W..W.......WWWWWW..W.....W",
    "W..W..W..WWWWWWWWW...W...W.....W",
    "W..W.WW..............W..WW.....W",
    "W..W.W....W.W........W..W......W",
    "W..W.WWWWWWWWWWWWWWW.W..WW.WWW.W",
    "W..W.................W.........W",
    "W..W.........W.......W....WW...W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
]

class MapGenerator:
    def __init__(self, width=None, height=None):
        # 这里的宽高主要用于兼容接口，实际上由 Template 决定
        self.raw_grid = [list(row) for row in BASE_TEMPLATE]
        self.h = len(self.raw_grid)
        self.w = len(self.raw_grid[0])
        self.dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def generate(self):
        """
        基于模板的生成流程：
        1. 读取模板 -> 2. 随机翻转 -> 3. 放置玩家/门 -> 4. 填充物品
        """
        # 1. 深度拷贝模板，并清理掉原来的物品(如果有残留)
        self.grid = []
        for row in self.raw_grid:
            new_row = []
            for char in row:
                # 只保留墙，其他全部还原为空地
                if char == 'W': new_row.append('W')
                else: new_row.append('.')
            self.grid.append(new_row)

        # 2. 地图变异 (镜像翻转)
        if MAP_CONFIG["enable_flip"]:
            self._apply_random_flip()

        # 3. 放置玩家 P
        # 既然用了模板，我们就在左上角区域找个空位
        self.player_pos = self._find_empty_area(1, 1, 10, 10)
        self.grid[self.player_pos[1]][self.player_pos[0]] = 'P'

        # 4. 放置门 D (寻找最远点)
        reachability = self._get_sliding_distances(self.player_pos)
        self._place_door(reachability)

        # 5. 计算解法路径 (保护主路不被地刺封死)
        solution_path = self._solve_sliding_path()
        safe_zone = self._get_area_around(self.player_pos, 3) | \
                    self._get_area_around(self.door_pos, 3)

        # 6. 填充物品 (使用成组生成算法)
        print("Populating template map...")
        
        # 茧
        self._place_linear_groups('O', MAP_CONFIG["cocoon_groups"], 
                                  MAP_CONFIG["cocoon_group_size"], safe_zone)
        # 地刺
        self._place_linear_groups('^', MAP_CONFIG["trap_groups"], 
                                  MAP_CONFIG["trap_group_size"], safe_zone | solution_path, strict=True)
        # 墙刺
        self._place_wall_spikes()
        # 金币
        self._place_linear_groups('C', MAP_CONFIG["coin_groups"], 
                                  MAP_CONFIG["coin_group_size"], set())

        return ["".join(row) for row in self.grid]

    # =========================================================================
    #  变异逻辑
    # =========================================================================
    def _apply_random_flip(self):
        """随机翻转地图，让同一张模板玩起来不一样"""
        # 左右翻转
        if random.random() < 0.5:
            for row in self.grid:
                row.reverse()
        
        # 上下翻转
        if random.random() < 0.5:
            self.grid.reverse()

    # =========================================================================
    #  物品填充逻辑 (复用之前的优秀逻辑)
    # =========================================================================
    def _place_linear_groups(self, char, count, size_range, forbidden, strict=False):
        placed = 0
        attempts = 0
        while placed < count and attempts < 200:
            attempts += 1
            rx = random.randint(1, self.w - 2)
            ry = random.randint(1, self.h - 2)
            if self.grid[ry][rx] != '.': continue

            length = random.randint(size_range[0], size_range[1])
            dx, dy = random.choice(self.dirs)
            
            points = []
            valid = True
            for i in range(length):
                nx, ny = rx + dx*i, ry + dy*i
                if not (0 < nx < self.w-1 and 0 < ny < self.h-1): valid=False; break
                if self.grid[ny][nx] != '.': valid=False; break
                if (nx, ny) in forbidden and strict: valid=False; break
                points.append((nx, ny))
            
            if valid and points:
                for px, py in points: self.grid[py][px] = char
                placed += 1

    def _place_wall_spikes(self):
        walls = [(x,y) for y in range(self.h) for x in range(self.w) if self.grid[y][x] == 'W']
        random.shuffle(walls)
        placed = 0
        for wx, wy in walls:
            if placed >= MAP_CONFIG["wall_spike_groups"]: break
            # 找空地面
            open_dir = None
            for dx, dy in self.dirs:
                if 0<=wx+dx<self.w and 0<=wy+dy<self.h and self.grid[wy+dy][wx+dx] == '.':
                    open_dir = (dx, dy); break
            if not open_dir: continue
            
            # 垂直生长
            grow_dir = (0, 1) if open_dir[0] != 0 else (1, 0)
            length = random.randint(MAP_CONFIG["wall_spike_len"][0], MAP_CONFIG["wall_spike_len"][1])
            
            curr_placed = False
            for i in range(length):
                tx, ty = wx + grow_dir[0]*i, wy + grow_dir[1]*i
                if not(0<tx<self.w-1 and 0<ty<self.h-1) or self.grid[ty][tx] != 'W': break
                # 检查面
                cx, cy = tx+open_dir[0], ty+open_dir[1]
                if 0<=cx<self.w and 0<=cy<self.h and self.grid[cy][cx] in ['.','P','C']:
                    self.grid[ty][tx] = '^'
                    curr_placed = True
            if curr_placed: placed += 1

    # =========================================================================
    #  工具函数
    # =========================================================================
    def _find_empty_area(self, x, y, w, h):
        # 局部搜索
        for r in range(y, min(y+h, self.h)):
            for c in range(x, min(x+w, self.w)):
                if self.grid[r][c] == '.': return (c, r)
        # 全局搜索
        for r in range(1, self.h-1):
            for c in range(1, self.w-1):
                if self.grid[r][c] == '.': return (c, r)
        return (1, 1)

    def _slide(self, start, direction):
        cx, cy = start
        dx, dy = direction
        path = []
        while True:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < self.w and 0 <= ny < self.h) or self.grid[ny][nx] == 'W':
                return (cx, cy), path
            cx, cy = nx, ny
            path.append((cx, cy))

    def _get_sliding_distances(self, start):
        q = deque([(start, 0)])
        visited = {start: 0}
        while q:
            curr, steps = q.popleft()
            for d in self.dirs:
                end, _ = self._slide(curr, d)
                if end not in visited:
                    visited[end] = steps + 1
                    q.append((end, steps+1))
        return visited

    def _solve_sliding_path(self):
        q = deque([(self.player_pos, [])])
        visited = {self.player_pos}
        while q:
            curr, path = q.popleft()
            if curr == self.door_pos:
                full_path_tiles = set()
                curr_node = self.player_pos
                for next_node in path:
                    if next_node[0] == curr_node[0]:
                        step = 1 if next_node[1] > curr_node[1] else -1
                        for y in range(curr_node[1], next_node[1]+step, step): full_path_tiles.add((curr_node[0], y))
                    else:
                        step = 1 if next_node[0] > curr_node[0] else -1
                        for x in range(curr_node[0], next_node[0]+step, step): full_path_tiles.add((x, curr_node[1]))
                    curr_node = next_node
                return full_path_tiles
            for d in self.dirs:
                end, _ = self._slide(curr, d)
                if end not in visited:
                    visited.add(end)
                    q.append((end, path + [end]))
        return set()

    def _place_door(self, reachability):
        if not reachability: self.door_pos = (self.w-2, self.h-2); self.grid[self.h-2][self.w-2]='D'; return
        sorted_dest = sorted(reachability.items(), key=lambda x: x[1], reverse=True)
        # 从最远的前20%个点里选
        limit = max(1, len(sorted_dest)//5)
        self.door_pos = random.choice(sorted_dest[:limit])[0]
        self.grid[self.door_pos[1]][self.door_pos[0]] = 'D'

    def _get_area_around(self, pos, r):
        px, py = pos
        area = set()
        for y in range(py-r, py+r+1):
            for x in range(px-r, px+r+1): area.add((x, y))
        return area

if __name__ == "__main__":
    gen = MapGenerator()
    for row in gen.generate():
        print(f'    "{row}",')