# src/maps.py
from map_generator import MapGenerator
# 0号测试关卡
# W = 墙, P = 玩家, . = 空地 (暂时只用这两个测试)

LEVELS = {
    0: [
    "WWWWWWWWWWWWWWW",
    "W.......WW...W",
    "W.WWWW..W..GWW",
    "W.WWW..WW..G.W",
    "W.WW..WW.....W",
    "W.W..WW......W",
    "W...WW.......W",
    "W..WWW.......W",
    "W........P...W",
    "WW..........DW",
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
    "W....W.WW....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "WW...WW.W....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "W....W.WW....W",
    "WW...W..W....W",
    "WW...W..W....W",
    "WW...WW.W....W",
    "WW...W..W....W",
    "W^...W..W....W",
    "W....W.WW....W",
    "W....W..W....W",
    "W....W..W....W",
    "W....Wv.W....W",
    "W....W..W....W",
    "W...OW..WO...W",
    "W...CW.WWO...W",
    "WP..CW......DW",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
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

for i in range(3, 8):
    LEVELS[i] = generator.generate()