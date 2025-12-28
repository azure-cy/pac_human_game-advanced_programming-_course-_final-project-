# src/maps.py
from map_generator import MapGenerator
# 0,1,2号教程关卡
# W = 墙, P = 玩家, . = 空地 (暂时只用这两个测试)

LEVELS = {
    0: [
    "WWWWWWWWWWWWWWW",
    "W......DWW...W",
    "W.WWWW..WCCCWW",
    "W.WWW..WW....W",
    "W.WW..WW.....W",
    "W.W..WW......W",
    "W...WW.......W",
    "W..WWW.......W",
    "W........P...W",
    "WW..........CW",
    "WWWWWWWWWWWWWW",
    ], 
    
    1: [
    "WWWWWWWWWWWWWWW",
    "W.......WW...W",
    "W....W..W...WW",
    "W....W.^W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "WW...W^.W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "W....W.^W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "WW...W^.W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "W....W.^W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "WW...W^.W....W",
    "WW...W..W....W",
    "W^...W..W....W",
    "W....W.^W....W",
    "W....W..W....W",
    "W....W..W....W",
    "W....W^.W....W",
    "W....W..W....W",
    "W...CW..WC...W",
    "W...CW.^WC...W",
    "WP..CW......DW",
    "WWWWWWWWWWWWWW",
    ],

    2: [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "WCC..CW...W.....WC......WWD....W",
    "WC...CW...W.....WC......WWWWW..W",
    "WCWW.CWCCC....W.WC......WWWWW..W",
    "WCCW.CW.WWWWWWW.WC.WWWWCWWCCCCCW",
    "WCCW.CW...W.....WC.W...CWWC...CW",
    "WCCW.CW...W.....WCWW.^.CWWC...CW",
    "WCCW.CWWW.W.....W..W.^^WWWCCCCCW",
    "WCCW.WWC..W..WWWW..WCCCCWW.OWWWW",
    "WWCWCCWC..W...CWO..WCCCCWW....CW",
    "W.CWCCWCWWW...CWO..WW.^.WWC^^^CW",
    "W.CWCCWC..WW..CWWW.WW.^CWWC^^^CW",
    "W.CWCCWC..W...CWCCCWW.^CWWC^^^CW",
    "W.CWCCWC..W...CWCCCWW....WC^^^CW",
    "W.CWCCWWW.W...CW.^^WW....WC^^^CW",
    "W.CWC.WC.CW...CW.^WOWWW..W....CW",
    "W.CWW.WC.CW...CW.^^...W..WWWWO.W",
    "W.WWO.WC.CW...CW.^^...W..WC...CW",
    "W.WWW.WC.CW...CW....C.W..WC^^^CW",
    "W.OW.CWC.CW...CWWWWWW.W..WC^^^CW",
    "W.OW.CWC.WW...CWCCCCCCW..WC^^^CW",
    "W.OW.CWC.W....CW......WW.WC...CW",
    "W.OW.CWC.W..^^^^.W....WW.W..WWWW",
    "W.OW.CWC.WW.^^^^.W....W..W.....W",
    "W.OW.CWC..WCCCCCCWWWWWW..W.^^^.W",
    "W.OW.CWC..WWWWWWWWWCCCW..W.^^^.W",
    "W.OW.WWC.............CW.WW.^^^.W",
    "W.OW.OWCC.WOW........CW.OW.^^^.W",
    "W.OWCWWWWWWWWWWWWWWW.CW.WW.WWW.W",
    "W.CW.........CCCCW...CW........W",
    "WPCWCCCCCCCCW........CW...WWOW.W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ],

}

generator = MapGenerator(width=25, height=25)

for i in range(3, 20):
    LEVELS[i] = generator.generate()

if __name__ == "__main__":    
    for level_id in sorted(LEVELS.keys()):
        print(f"\n=== LEVEL {level_id} ({'手动设计' if level_id < 3 else '自动生成'}) ===")
        grid = LEVELS[level_id]
        
        for row in grid:
            print(row)