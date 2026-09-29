WIDTH, HEIGHT = 1280, 720
FPS = 60

GRAVITY = 2200.0
MIN_SPEED = 180.0
MAX_SPEED = 900.0
JUMP_VELOCITY = -900.0
FLIP_SPEED = 7.5
LAND_TOLERANCE = 1.0
GROUND_OFFSET = 4

COIN_VALUE = 10
COIN_RADIUS = 12
TRICK_FLIP_BONUS = 100
COMBO_SPEED_BOOST = 0.08
MAX_COMBO_MULT = 5

# --- буст за трюки ---
BOOST_PER_FLIP   = 60.0     # +vx и +потолок за каждый полный оборот
BOOST_DECAY      = 12.0     # сколько буста «испаряется» в секунду
MAX_SPEED_BOOST  = 500.0    # потолок буста поверх MAX_SPEED

# --- Wall Ride ---
WALL_RIDE_SPEED = 400.0        # скорость подъёма по стене
WALL_RIDE_DURATION = 1.2       # макс. время скольжения по стене

# --- Grind Rail ---
GRIND_SPEED = 600.0            # скорость на тросе
GRIND_BREAK_CHANCE = 0.15      # шанс обрыва троса за секунду

# --- Balloon Bounce ---
BALLOON_BOUNCE_VELOCITY = -1400.0  # сила отскока от шара
BALLOON_RADIUS = 40

# --- Wingsuit ---
WINGSUIT_DURATION = 2.5        # длительность полёта
WINGSUIT_SPEED_BOOST = 150.0   # прибавка к скорости
WINGSUIT_FALL_SPEED = 120.0    # скорость падения в wingsuit

# --- Lemur ---
LEMUR_SPEED = 350.0
LEMUR_SPAWN_DELAY = 1.5        # через сколько секунд после падения появляется
LEMUR_CATCH_DISTANCE = 60.0

# --- Biomes ---
BIOME_DUNES_END = 2000.0       # метров
BIOME_CANYONS_END = 5000.0     # метров 
