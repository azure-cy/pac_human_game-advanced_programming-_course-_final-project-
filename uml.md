graph TD
    Main[main.py] --> Game[game.py]
    Game --> Level[level.py]
    Game --> UI[ui.py]
    
    Level --> Maps[maps.py]
    Level --> Sprites[sprites.py]
    Level --> Particles[particles.py]
    Level --> Camera[camera.py]
    Level --> AssetFactory[assets.py]
    
    Maps --> MapGen[map_generator.py]
    
    Sprites --> AssetFactory
    Particles --> AssetFactory
    
    style AssetFactory fill:#f9f,stroke:#333,stroke-width:2px
    style Level fill:#bbf,stroke:#333,stroke-width:2px

classDiagram
    %% ================= 核心控制类 =================
    class Game {
        +screen : Surface
        +clock : Clock
        +current_level_index : int
        +game_state : str
        +level : Level
        +ui : UI
        +run()
        +restart_level()
        +next_level()
    }

    class Level {
        +display_surface : Surface
        +visible_sprites : CameraGroup
        +obstacle_sprites : Group
        +damage_sprites : Group
        +player : Player
        -_build_level()
        +trigger_particle()
        -_check_game_status()
        +run()
    }

    class MapGenerator {
        +raw_grid : list
        +width : int
        +height : int
        +generate() : list
        -_apply_random_flip()
        -_find_random_empty_spot()
        -_place_door_far_away()
        -_solve_sliding_path()
    }

    %% ================= 资源工厂 (享元模式) =================
    class AssetFactory {
        -_trail_cache : dict
        -_coin_cache : list
        -_tile_cache : dict
        +get_trail_assets()$
        +get_coin_assets()$
        +create_tile()$
        +create_spike_bullet()$
        -_draw_border()$
    }

    %% ================= 实体类 (Sprites) =================
    class Sprite {
        <<Pygame>>
    }

    class BaseStaticSprite {
        +image : Surface
        +rect : Rect
    }

    class Wall {
        +color : Color
    }

    class Door {
        +color : Color
    }

    class Player {
        +direction : Vector2
        +speed : int
        +status : str
        +move_start_time : int
        -_input()
        -_move()
        -_handle_collision()
        -_update_image_layer()
    }

    class Ghost {
        +direction : Vector2
        +speed : int
        +wall_grid : set
        +find_dir()
        +update()
    }

    class Trap {
        +status : str
        +cooldown_timer : int
        +direction : Vector2
        -_detect_player()
        -_trigger()
    }

    class Spike {
        +state : str
        +dist : int
        -_handle_extending()
        -_handle_retracting()
    }

    class Cocoon {
        +is_triggered : bool
        +trigger_time : int
        +update()
    }

    class Coin {
        +frames : list
        +idx : float
        +update()
    }

    %% ================= 特效类 =================
    class TrailSprite {
        +timer : int
        +update()
    }

    class BubbleSprite {
        +direction : Vector2
        +timer : int
        +update()
    }

    %% ================= 关系定义 =================
    %% 继承关系
    Sprite <|-- BaseStaticSprite
    Sprite <|-- Player
    Sprite <|-- Ghost
    Sprite <|-- Trap
    Sprite <|-- Spike
    Sprite <|-- Cocoon
    Sprite <|-- Coin
    Sprite <|-- TrailSprite
    Sprite <|-- BubbleSprite

    BaseStaticSprite <|-- Wall
    BaseStaticSprite <|-- Door

    %% 组合与依赖关系
    Game *-- Level : contains
    Level *-- Player : manages
    Level ..> MapGenerator : uses
    Level ..> AssetFactory : uses
    
    %% 实体间的交互
    Cocoon ..> Ghost : spawns
    Trap ..> Spike : spawns
    Player ..> TrailSprite : spawns
    Player ..> BubbleSprite : spawns
    
    %% 工厂依赖
    Player ..> AssetFactory
    Ghost ..> AssetFactory
    Wall ..> AssetFactory
    Trap ..> AssetFactory