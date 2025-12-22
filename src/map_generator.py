# src/map_generator.py
import random
from collections import deque

# ==========================================
#              地图生成配置
# ==========================================
MAP_CONFIG = {
    "width": 31,            # 宽度 (奇数)
    "height": 31,           # 高度 (奇数)
    
    # 迷宫结构
    "braid_chance": 0.05,   # 死胡同消除率
    "widen_chance": 0.4,    # [新增] 拓宽道路概率 (实现1-2格混合宽度)
    
    # 难度控制
    "min_slide_steps": 10,   # P到D至少滑行几步
    
    # --- 物体生成配置 ---
    "coin_groups": 10,      # 金币组数
    "coin_len": (3, 5),     # 金币每组长度
    
    "floor_spike_groups": 12, # [调整] 地面刺组数 (出现在通道两侧)
    "floor_spike_len": (1, 3),
    
    "wall_spike_count": 10,   # [新增] 墙面刺的数量 (嵌入墙体)
    
    "cocoon_groups": 4,     # 茧的组数
    "cocoon_len": (2, 3)    # 茧每组长度
}

class MapGenerator:
    def __init__(self, width=None, height=None):
        w = width if width else MAP_CONFIG["width"]
        h = height if height else MAP_CONFIG["height"]
        self.width = w + (0 if w % 2 else 1)
        self.height = h + (0 if h % 2 else 1)
        self.dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def generate(self):
        attempt = 0
        while True:
            attempt += 1
            # 1. 初始化全墙
            self.grid = [['W' for _ in range(self.width)] for _ in range(self.height)]
            
            # 2. 生成基础迷宫 (1格宽)
            self._recursive_maze(1, 1)
            
            # 3. [新增] 拓宽道路 (实现1格和2格宽度混合)
            self._widen_paths(MAP_CONFIG["widen_chance"])
            
            # 4. 消除死胡同
            self._braid_maze(MAP_CONFIG["braid_chance"])

            # 5. 放置玩家
            self.player_pos = self._find_empty_spot(area='top_left')
            self.grid[self.player_pos[1]][self.player_pos[0]] = 'P'

            # 6. 计算可达性
            reachable_map = self._analyze_reachability(self.player_pos)

            # 7. 放置门
            if not self._place_door_strict(reachable_map):
                continue 

            # 8. [核心逻辑升级] 获取详细路径信息
            # sol_lines: 滑行轨迹 (地面刺禁区)
            # sol_stops: 停留点 (地面刺禁区)
            # sol_impacts: [新增] 玩家为了刹车必须撞击的墙 (墙面刺禁区)
            self.sol_lines, self.sol_stops, self.sol_impacts = self._get_solution_details()
            
            # 地面安全区 = 轨迹 + 停留点 + 玩家 + 门
            self.safe_floor_set = self.sol_lines.union(self.sol_stops).union({self.player_pos, self.door_pos})

            # 9. 放置金币 (引导路径)
            self._place_generic_groups(
                char='C', 
                count=MAP_CONFIG["coin_groups"], 
                len_range=MAP_CONFIG["coin_len"],
                forbidden_cells=set(), 
                require_near_path=False
            )

            # 10. 放置地面刺 (出现在通道两侧)
            # 逻辑：只能放在非主路的空地上
            self._place_generic_groups(
                char='^', 
                count=MAP_CONFIG["floor_spike_groups"], 
                len_range=MAP_CONFIG["floor_spike_len"],
                forbidden_cells=self.safe_floor_set, # 绝对避开主路
                require_near_path=False
            )

            # 11. [新增] 放置墙面刺 (嵌入墙体)
            # 逻辑：替换墙壁，但绝对不能替换 sol_impacts (刹车墙)
            self._place_wall_spikes()

            # 12. 放置茧 (伏击)
            # 茧在路边，forbidden依然是路径本身
            forbidden_for_cocoons = self.safe_floor_set
            self._place_generic_groups(
                char='O',
                count=MAP_CONFIG["cocoon_groups"],
                len_range=MAP_CONFIG["cocoon_len"],
                forbidden_cells=forbidden_for_cocoons,
                require_near_path=True # 必须贴着路
            )

            print(f"Map generated in {attempt} attempts.")
            return ["".join(row) for row in self.grid]

    # --- 新增/修改的逻辑 ---

    def _widen_paths(self, chance):
        """随机拓宽道路，制造1格与2格宽并存的结构"""
        # 遍历内部的墙
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 'W':
                    # 如果这面墙上下左右有路，它就是潜在的拓宽点
                    # 统计周围的路的数量
                    road_neighbors = sum(1 for dx, dy in self.dirs if self.grid[y+dy][x+dx] == '.')
                    
                    # 只要有路在旁边，且随机命中，就打通变成路
                    if road_neighbors > 0 and random.random() < chance:
                        self.grid[y][x] = '.'

    def _place_wall_spikes(self):
        """放置嵌入墙体的刺"""
        candidates = []
        # 遍历所有墙壁
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 'W':
                    # 1. [核心保护] 绝对不能是玩家通关必须撞击的墙
                    if (x, y) in self.sol_impacts:
                        continue
                    
                    # 2. 必须暴露在空气中(旁边有路)，否则玩家碰不到
                    has_floor_neighbor = False
                    for dx, dy in self.dirs:
                        if self.grid[y+dy][x+dx] != 'W':
                            has_floor_neighbor = True
                            break
                    
                    if has_floor_neighbor:
                        candidates.append((x, y))
        
        random.shuffle(candidates)
        count = 0
        limit = MAP_CONFIG["wall_spike_count"]
        
        for x, y in candidates:
            if count >= limit: break
            self.grid[y][x] = '^' # 把墙变成刺
            count += 1

    def _slide_with_impact(self, start, d):
        """
        物理模拟升级版
        返回: (停止坐标, 路径列表, 撞击的墙坐标)
        """
        cx, cy = start
        path = []
        impact_wall = None # 记录撞到了哪个墙

        while True:
            nx, ny = cx + d[0], cy + d[1]
            
            # 检查越界 或 撞墙
            # 注意：在这里，刺(^)、墙(W)、甚至茧(O)如果不处理碰撞都会被视为阻挡
            # 但在生成阶段，物体还未放置，只有 'W' 和 '.'
            if not (0 <= nx < self.width and 0 <= ny < self.height) or self.grid[ny][nx] == 'W':
                # 如果是因为撞墙停下的（而不是出界），记录墙的坐标
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    impact_wall = (nx, ny)
                break
            
            cx, cy = nx, ny
            path.append((cx, cy))
            
        return (cx, cy), path, impact_wall

    def _get_solution_details(self):
        """
        计算解谜路径，同时识别出关键的'刹车墙'
        """
        # queue item: (curr_pos, lines, stops, impacts)
        queue = deque([(self.player_pos, set(), set(), set())]) 
        visited_stops = {self.player_pos}
        
        while queue:
            curr, lines, stops, impacts = queue.popleft()
            if curr == self.door_pos:
                return lines, stops, impacts

            for d in self.dirs:
                # 使用带撞击检测的滑行函数
                stop_pos, segment, impact_wall = self._slide_with_impact(curr, d)
                
                if stop_pos not in visited_stops:
                    visited_stops.add(stop_pos)
                    
                    new_lines = lines.union(set(segment))
                    new_stops = stops.union({stop_pos})
                    
                    # 记录这个关键的刹车墙
                    new_impacts = impacts.copy()
                    if impact_wall:
                        new_impacts.add(impact_wall)
                        
                    queue.append((stop_pos, new_lines, new_stops, new_impacts))
        return set(), set(), set()

    # --- 基础功能 (保持不变或微调适配) ---

    def _place_generic_groups(self, char, count, len_range, forbidden_cells, require_near_path=False):
        """通用成组放置器"""
        placed = 0
        attempts = 0
        min_len, max_len = len_range
        
        while placed < count and attempts < 3000:
            attempts += 1
            rx, ry = random.randint(1, self.width-2), random.randint(1, self.height-2)
            if self.grid[ry][rx] != '.': continue
            
            dx, dy = random.choice(self.dirs)
            length = random.randint(min_len, max_len)
            
            group_cells = []
            valid = True
            is_near_path = False 

            for i in range(length):
                nx, ny = rx + dx*i, ry + dy*i
                
                # A. 基础合法性
                if not (0 <= nx < self.width and 0 <= ny < self.height): valid = False; break
                if self.grid[ny][nx] != '.': valid = False; break
                if (nx, ny) == self.player_pos or (nx, ny) == self.door_pos: valid = False; break
                
                # B. 禁区检查
                if (nx, ny) in forbidden_cells: valid = False; break
                
                # C. 邻近性
                if require_near_path:
                    for neighbor_d in self.dirs:
                        tx, ty = nx + neighbor_d[0], ny + neighbor_d[1]
                        if (tx, ty) in self.safe_floor_set:
                            is_near_path = True
                
                group_cells.append((nx, ny))
            
            if valid:
                if require_near_path and not is_near_path: continue
                
                for cx, cy in group_cells:
                    self.grid[cy][cx] = char
                placed += 1

    def _slide(self, start, d):
        """简单的滑行模拟 (用于BFS距离计算)"""
        cx, cy = start
        while True:
            nx, ny = cx + d[0], cy + d[1]
            if not (0 <= nx < self.width and 0 <= ny < self.height) or self.grid[ny][nx] == 'W':
                break
            cx, cy = nx, ny
        return (cx, cy), [] 

    def _analyze_reachability(self, start):
        queue = deque([(start, 0)])
        visited = {start: 0}
        while queue:
            curr, steps = queue.popleft()
            for d in self.dirs:
                stop_pos, _ = self._slide(curr, d)
                if stop_pos not in visited:
                    visited[stop_pos] = steps + 1
                    queue.append((stop_pos, steps + 1))
        return visited

    def _place_door_strict(self, reachable_map):
        candidates = []
        min_steps = MAP_CONFIG["min_slide_steps"]
        for pos, steps in reachable_map.items():
            if steps >= min_steps:
                dist = abs(pos[0]-self.player_pos[0]) + abs(pos[1]-self.player_pos[1])
                score = steps * 100 + dist 
                candidates.append((score, pos))
        if not candidates: return False
        candidates.sort(key=lambda x: x[0], reverse=True)
        self.door_pos = candidates[0][1]
        self.grid[self.door_pos[1]][self.door_pos[0]] = 'D'
        return True

    def _recursive_maze(self, x, y):
        self.grid[y][x] = '.'
        d_list = self.dirs[:]
        random.shuffle(d_list)
        for dx, dy in d_list:
            nx, ny = x + dx*2, y + dy*2
            if 1 <= nx < self.width-1 and 1 <= ny < self.height-1 and self.grid[ny][nx] == 'W':
                self.grid[y+dy][x+dx] = '.'
                self._recursive_maze(nx, ny)

    def _braid_maze(self, fraction):
        dead_ends = [(x,y) for y in range(1,self.height-1) for x in range(1,self.width-1) 
                     if self.grid[y][x]=='.' and sum(1 for dx,dy in self.dirs if self.grid[y+dy][x+dx]=='W')==3]
        random.shuffle(dead_ends)
        for x, y in dead_ends[:int(len(dead_ends)*fraction)]:
            valid = [(dx,dy) for dx,dy in self.dirs if 1<x+dx<self.width-1 and 1<y+dy<self.height-1 and self.grid[y+dy][x+dx]=='W']
            if valid:
                dx, dy = random.choice(valid)
                self.grid[y+dy][x+dx] = '.'

    def _find_empty_spot(self, area='all'):
        while True:
            limit_x = self.width // 3 if area == 'top_left' else self.width - 2
            limit_y = self.height // 3 if area == 'top_left' else self.height - 2
            rx = random.randint(1, limit_x)
            ry = random.randint(1, limit_y)
            if self.grid[ry][rx] == '.': return (rx, ry)

if __name__ == "__main__":
    generator = MapGenerator(width=25, height=25)

    for line in generator.generate():
        print(line)