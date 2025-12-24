# src/map_generator.py
import random
from collections import deque

# ==============================================================================
#                                  配置参数
# ==============================================================================
MAP_CONFIG = {
    # 物品生成数量
    "coin_groups": 10,           
    "coin_group_size": (3, 6),  
    
    "trap_groups": 8,           
    "trap_group_size": (2, 4),  
    
    "cocoon_groups": 5,         
    "cocoon_group_size": (1, 1),
    
    "wall_spike_groups": 10,     
    "wall_spike_len": (2, 5),
    
    # 变异参数
    "enable_flip": True,       # 是否允许地图镜像翻转
}

# 母图 (你的手绘图)
BASE_TEMPLATE = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W..............W.....W.........W",
    "W.....W...W....W.....W......WW.W",
    "W.WW..W...W....W.WC..W......WW.W",
    "W..W..W.WWWWWWW.WC.WWW.W.......W",
    "W..W..W...W.....WC.W...W..W....W",
    "W..W..W...W.....W.WW...W..W....W",
    "W..W.WW...W..WWWW..W...WW.W.WWWW",
    "WW.W..W...W...CW...W...WW....CWW",
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
        # 兼容接口
        self.raw_grid = [list(row) for row in BASE_TEMPLATE]
        self.h = len(self.raw_grid)
        self.w = len(self.raw_grid[0])
        self.dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def generate(self):
        """
        基于模板的生成流程
        """
        # 1. 深度拷贝模板，并清理掉原来的物品
        self.grid = []
        for row in self.raw_grid:
            new_row = []
            for char in row:
                if char == 'W': new_row.append('W')
                else: new_row.append('.')
            self.grid.append(new_row)

        # 2. 地图变异
        if MAP_CONFIG["enable_flip"]:
            self._apply_random_flip()

        # 3. [优化] 寻找最佳出生点
        # 尝试多次，确保玩家出生在一个“能去很多地方”的位置
        # 防止出生在死角导致门只能生成在附近
        best_start = None
        best_reachability = {}
        
        for _ in range(20): # 尝试找20个不同的起点
            # 在全图中随机找空地，不局限于左上角
            try_pos = self._find_random_empty_spot()
            reach = self._get_sliding_distances(try_pos)
            # 如果这个起点能到达全图 40% 以上的区域，就是一个合格的起点
            if len(reach) > (self.w * self.h) * 0.4:
                best_start = try_pos
                best_reachability = reach
                break
        
        # 如果实在找不到完美的，就退化到找一个能走的就行
        if not best_start:
            best_start = self._find_random_empty_spot()
            best_reachability = self._get_sliding_distances(best_start)

        self.player_pos = best_start
        self.grid[self.player_pos[1]][self.player_pos[0]] = 'P'

        # 4. [优化] 放置门 D (物理距离最远)
        self._place_door_far_away(best_reachability)

        # 5. 计算解法路径
        solution_path = self._solve_sliding_path()
        safe_zone = self._get_area_around(self.player_pos, 3) | \
                    self._get_area_around(self.door_pos, 3)

        # 6. 填充物品
        print(f"Populating map... P:{self.player_pos} -> D:{self.door_pos}")
        
        self._place_linear_groups('O', MAP_CONFIG["cocoon_groups"], 
                                  MAP_CONFIG["cocoon_group_size"], safe_zone)
        self._place_linear_groups('^', MAP_CONFIG["trap_groups"], 
                                  MAP_CONFIG["trap_group_size"], safe_zone | solution_path, strict=True)
        self._place_wall_spikes()
        self._place_linear_groups('C', MAP_CONFIG["coin_groups"], 
                                  MAP_CONFIG["coin_group_size"], set())

        return ["".join(row) for row in self.grid]

    # =========================================================================
    #  变异逻辑
    # =========================================================================
    def _apply_random_flip(self):
        if random.random() < 0.5:
            for row in self.grid: row.reverse()
        if random.random() < 0.5:
            self.grid.reverse()

    # =========================================================================
    #  门与位置计算 (核心修改)
    # =========================================================================
    def _find_random_empty_spot(self):
        """在全图中随机找一个空点"""
        for _ in range(100):
            rx = random.randint(1, self.w - 2)
            ry = random.randint(1, self.h - 2)
            if self.grid[ry][rx] == '.':
                return (rx, ry)
        return (1, 1) # Fallback

    def _place_door_far_away(self, reachability):
        """
        [算法优化] 
        计算所有可达点相对于玩家的【曼哈顿距离】+【滑行步数】的加权分。
        优先选择物理距离最远的点。
        """
        if not reachability:
            # 极罕见情况，强制放一个
            self.door_pos = (self.w-2, self.h-2)
            self.grid[self.h-2][self.w-2] = 'D'
            return

        candidates = []
        px, py = self.player_pos
        
        for (dx, dy), steps in reachability.items():
            # 1. 计算物理距离 (曼哈顿距离)
            physical_dist = abs(dx - px) + abs(dy - py)
            
            # 2. 综合评分：物理距离权重极高 (10倍)，滑行步数作为次要参考
            # 这样保证门一定生成在地图的另一端
            score = (physical_dist * 10) + steps
            
            candidates.append(((dx, dy), score))

        # 按分数降序排列
        candidates.sort(key=lambda x: x[1], reverse=True)

        # 从分数最高的 5 个点里随机选一个 (增加一点随机性，但保证都很远)
        limit = max(1, min(5, len(candidates)))
        self.door_pos = random.choice(candidates[:limit])[0]
        
        self.grid[self.door_pos[1]][self.door_pos[0]] = 'D'

    # =========================================================================
    #  物品填充 (成组)
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
            open_dir = None
            for dx, dy in self.dirs:
                if 0<=wx+dx<self.w and 0<=wy+dy<self.h and self.grid[wy+dy][wx+dx] == '.':
                    open_dir = (dx, dy); break
            if not open_dir: continue
            
            grow_dir = (0, 1) if open_dir[0] != 0 else (1, 0)
            length = random.randint(MAP_CONFIG["wall_spike_len"][0], MAP_CONFIG["wall_spike_len"][1])
            
            curr_placed = False
            for i in range(length):
                tx, ty = wx + grow_dir[0]*i, wy + grow_dir[1]*i
                if not(0<tx<self.w-1 and 0<ty<self.h-1) or self.grid[ty][tx] != 'W': break
                cx, cy = tx+open_dir[0], ty+open_dir[1]
                if 0<=cx<self.w and 0<=cy<self.h and self.grid[cy][cx] in ['.','P','C']:
                    self.grid[ty][tx] = '^'
                    curr_placed = True
            if curr_placed: placed += 1

    # =========================================================================
    #  滑行与寻路
    # =========================================================================
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