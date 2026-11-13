"""
Settings and configuration constants for the Hill Hold Assist Simulator.
"""

# Screen and Display Settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60
WINDOW_TITLE = "Hill Hold Assist Simulator - 2D Driving Simulator"

# Road Incline Geometry
ROAD_CENTER_X = 500.0         # Screen X coordinate of road pivot center
ROAD_CENTER_Y = 380.0         # Screen Y coordinate of road pivot center
ROAD_THICKNESS = 28.0         # Thickness of the asphalt road strip in pixels
MIN_SLOPE_DEG = -15.0         # Minimum slope (-15° = downhill)
MAX_SLOPE_DEG = 15.0          # Maximum slope (+15° = uphill)
SLOPE_STEP_DEG = 1.0          # Angle change per step (degrees)
INITIAL_SLOPE_DEG = 0.0       # Starts flat

# Vehicle Physics Parameters (Preserved)
CAR_MASS = 1200.0             # Vehicle mass (kg)
GRAVITY = 9.81                # Gravitational acceleration (m/s^2)
ENGINE_FORCE = 5800.0         # Forward drive force from accelerator (N)
BRAKE_FORCE = 8500.0          # Opposing braking force (N)
DRAG_COEFF = 0.38             # Aerodynamic drag factor
PIXELS_PER_METER = 20.0       # Scale: 20 pixels = 1 meter

# Hill Hold Assist (HHA) Parameters (Preserved)
HHA_HOLD_DURATION = 3.0       # Automatic hold duration in seconds
HHA_STANDSTILL_SPEED = 0.05   # Speed threshold (m/s) below which car is stopped
HHA_MIN_UPHILL_SLOPE = 0.1    # Minimum positive slope (degrees) for uphill detection

# Road Surface Condition Properties (Preserved)
SURFACES = {
    "DRY": {
        "name": "Dry Road",
        "grip_coeff": 1.0,              # Normal tyre-road friction
        "rolling_res_coeff": 0.015,      # Normal rolling resistance
        "color_road": (52, 54, 58),      # Clean modern asphalt
        "color_marking": (250, 250, 250),
        "desc": "Normal Grip (100%)",
    },
    "WET": {
        "name": "Wet Road",
        "grip_coeff": 0.55,             # Reduced grip
        "rolling_res_coeff": 0.018,      # Slightly increased water resistance
        "color_road": (35, 45, 54),      # Slick glossy wet asphalt
        "color_marking": (210, 225, 235),
        "desc": "Reduced Grip (55%)",
    },
    "ICE": {
        "name": "Ice Road",
        "grip_coeff": 0.12,             # Very low grip
        "rolling_res_coeff": 0.010,      # Slick low resistance
        "color_road": (210, 230, 242),   # Frosted pale ice
        "color_marking": (140, 175, 205),
        "desc": "Very Low Grip (12%)",
    },
    "GRAVEL": {
        "name": "Gravel Road",
        "grip_coeff": 0.65,             # Moderate loose-surface grip
        "rolling_res_coeff": 0.055,      # High rolling resistance from loose stones
        "color_road": (122, 100, 78),    # Earthy gravel brown
        "color_marking": (215, 205, 180),
        "desc": "Moderate Grip (65%), High Rolling Res",
    },
}

# Aesthetic Color Palette
COLOR_SKY_TOP = (165, 205, 245)
COLOR_SKY_BOTTOM = (215, 235, 255)
COLOR_MOUNTAIN_FAR = (145, 175, 205)
COLOR_MOUNTAIN_NEAR = (115, 150, 180)
COLOR_GRASS_TOP = (95, 175, 95)
COLOR_GRASS_BOTTOM = (65, 140, 65)

# Car Colors (Sleek Ruby Red Modern Profile)
COLOR_CAR_BODY = (215, 40, 40)
COLOR_CAR_ACCENT = (175, 25, 25)
COLOR_CAR_ROOF = (35, 35, 40)
COLOR_CAR_WINDOW = (195, 225, 250)
COLOR_CAR_WHEEL = (35, 35, 38)
COLOR_CAR_RIM = (210, 215, 225)
COLOR_CAR_HUB = (90, 95, 105)
COLOR_HEADLIGHT = (255, 250, 180)
COLOR_TAILLIGHT = (255, 35, 35)
COLOR_TAILLIGHT_DIM = (160, 20, 20)

# Minimal HUD Colors
COLOR_HUD_BG = (255, 255, 255, 240)
COLOR_HUD_BORDER = (215, 220, 230)
COLOR_TEXT_MAIN = (20, 25, 35)
COLOR_TEXT_MUTED = (110, 115, 125)
