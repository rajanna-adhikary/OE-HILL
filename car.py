"""
Car module for the Hill Hold Assist Simulator.
Renders a polished, modern 2D side-view vehicle with rotating alloy wheels,
brake light activation, and alignment with the inclined road.
"""

import math
import pygame
from settings import (
    PIXELS_PER_METER,
    COLOR_CAR_BODY,
    COLOR_CAR_ACCENT,
    COLOR_CAR_ROOF,
    COLOR_CAR_WINDOW,
    COLOR_CAR_WHEEL,
    COLOR_CAR_RIM,
    COLOR_CAR_HUB,
    COLOR_HEADLIGHT,
    COLOR_TAILLIGHT,
    COLOR_TAILLIGHT_DIM,
)


class Car:
    """Represents the player vehicle on an inclined road surface with rotating wheels."""

    def __init__(self):
        self.length = 104
        self.height = 34
        self.wheel_radius = 10.0
        self.wheel_base_half = 28.0   # Half-distance between front and rear axles

        self.world_distance_m = 0.0   # Distance along road in meters (0 = center)
        self.velocity = 0.0           # In m/s (+ forward/uphill, - backward/downhill)
        self.acceleration = 0.0       # In m/s^2
        self.f_gravity = 0.0          # Current gravity force (N)
        self.f_net = 0.0              # Current net force (N)
        self.f_traction_max = 0.0     # Maximum available traction from surface grip (N)
        self.is_slipping = False      # True if tyres are slipping / grip is exceeded

        # Wheel rotation angle in degrees (accumulates as car moves)
        self.wheel_angle = 0.0

        # Pre-render car body without wheels (wheels are rendered dynamically to rotate)
        self.body_surface_normal = self._create_body_surface(braking=False)
        self.body_surface_braking = self._create_body_surface(braking=True)

    def _create_body_surface(self, braking=False):
        """Pre-render a sleek, modern aerodynamic vehicle body."""
        surf = pygame.Surface((self.length, self.height), pygame.SRCALPHA)

        # 1. Aerodynamic Roof / Cabin Profile
        roof_points = [
            (22, 20),   # Rear base of pillar
            (36, 4),    # Rear roof start
            (68, 4),    # Front roof edge
            (82, 20),   # Front windshield base on hood
        ]
        pygame.draw.polygon(surf, COLOR_CAR_ROOF, roof_points)

        # 2. Main Aerodynamic Chassis (Ruby Red Metallic)
        # Lower main body polygon
        body_points = [
            (4, 20),    # Rear bumper top
            (8, 15),    # Rear deck lid
            (22, 17),   # Base of rear window
            (82, 17),   # Base of windshield
            (98, 20),   # Front hood nose
            (102, 26),  # Front lower bumper
            (88, 26),   # Front wheel arch right
            (82, 22),   # Front wheel arch top
            (68, 26),   # Front wheel arch left
            (42, 26),   # Underbody / side skirt
            (38, 22),   # Rear wheel arch top
            (24, 26),   # Rear wheel arch left
            (2, 26),    # Rear lower bumper
        ]
        pygame.draw.polygon(surf, COLOR_CAR_BODY, body_points)

        # Lower side skirt accent line
        pygame.draw.polygon(
            surf,
            COLOR_CAR_ACCENT,
            [(2, 25), (102, 25), (100, 28), (4, 28)]
        )

        # 3. Tinted Aerodynamic Windows with Sky Reflection
        # Front side window
        front_window = [
            (54, 18),
            (54, 6),
            (66, 6),
            (78, 18),
        ]
        # Rear side window
        rear_window = [
            (26, 18),
            (38, 6),
            (51, 6),
            (51, 18),
        ]
        pygame.draw.polygon(surf, COLOR_CAR_WINDOW, front_window)
        pygame.draw.polygon(surf, COLOR_CAR_WINDOW, rear_window)

        # Window frames and B-pillar divider
        pygame.draw.line(surf, (40, 42, 48), (52, 6), (52, 19), 3)

        # 4. Front Headlight (Sleek Projector LED)
        pygame.draw.polygon(
            surf,
            COLOR_HEADLIGHT,
            [(98, 20), (103, 23), (99, 25), (95, 22)]
        )

        # 5. Rear Taillight / Brake Light
        # When braking, illuminates vivid bright red; otherwise subtle ruby red
        taillight_color = COLOR_TAILLIGHT if braking else COLOR_TAILLIGHT_DIM
        pygame.draw.rect(surf, taillight_color, (3, 18, 5, 6), border_radius=2)
        if braking:
            # Active brake light glow
            pygame.draw.rect(surf, (255, 120, 120), (2, 19, 3, 4), border_radius=1)

        return surf

    def reset(self):
        """Reset vehicle to center position with zero velocity and forces."""
        self.world_distance_m = 0.0
        self.velocity = 0.0
        self.acceleration = 0.0
        self.f_gravity = 0.0
        self.f_net = 0.0
        self.wheel_angle = 0.0
        self.is_slipping = False

    def update(
        self,
        is_accelerating,
        is_braking,
        slope_deg,
        dt,
        physics_engine,
        hha_active=False,
        grip_coeff=1.0,
        rolling_res_coeff=0.015,
    ):
        """
        Advance vehicle physics and accumulate physical wheel rotation.
        """
        new_vel, displacement_m, accel, f_grav, f_net, f_trac_max, slipping = physics_engine.update(
            velocity=self.velocity,
            is_accelerating=is_accelerating,
            is_braking=is_braking,
            slope_deg=slope_deg,
            dt=dt,
            hha_active=hha_active,
            grip_coeff=grip_coeff,
            rolling_res_coeff=rolling_res_coeff,
        )
        self.velocity = new_vel
        self.acceleration = accel
        self.f_gravity = f_grav
        self.f_net = f_net
        self.f_traction_max = f_trac_max
        self.is_slipping = slipping
        self.world_distance_m += displacement_m

        # Calculate wheel rotation from displacement (Requirement 3)
        # Delta angle = displacement_pixels / wheel_radius (in radians)
        disp_px = displacement_m * PIXELS_PER_METER
        # For a car facing right: moving forward rotates clockwise (+angle in math coordinates)
        delta_angle_deg = (disp_px / self.wheel_radius) * (180.0 / math.pi)
        self.wheel_angle = (self.wheel_angle + delta_angle_deg) % 360.0

    def get_speed_kmh(self):
        """Return speed in km/h (positive magnitude)."""
        return abs(self.velocity) * 3.6

    def _draw_alloy_wheel(self, surface, center_x, center_y, rotation_deg):
        """
        Render a rotating alloy wheel with rubber tyre, silver rim, 5 alloy spokes, and axle hub.
        """
        cx = int(center_x)
        cy = int(center_y)
        r = int(self.wheel_radius)

        # 1. Dark rubber tyre
        pygame.draw.circle(surface, COLOR_CAR_WHEEL, (cx, cy), r)
        # Tyre tread outer ring highlight
        pygame.draw.circle(surface, (55, 58, 65), (cx, cy), r, width=1)

        # 2. Silver alloy inner rim
        rim_r = 6.5
        pygame.draw.circle(surface, COLOR_CAR_RIM, (cx, cy), int(rim_r))

        # 3. 5 Alloy spokes rotating with the vehicle motion
        rad_rot = math.radians(rotation_deg)
        for i in range(5):
            angle = rad_rot + i * (2.0 * math.pi / 5.0)
            spoke_end_x = cx + math.cos(angle) * (rim_r - 0.5)
            spoke_end_y = cy + math.sin(angle) * (rim_r - 0.5)
            pygame.draw.line(surface, (90, 95, 105), (cx, cy), (int(spoke_end_x), int(spoke_end_y)), 2)

        # 4. Central axle cap
        pygame.draw.circle(surface, COLOR_CAR_HUB, (cx, cy), 2)

    def draw(self, surface, road, screen_dist_along_road, is_braking=False):
        """
        Draw vehicle body rotated to slope angle, with rotating alloy wheels touching the road line.
        """
        # Road contact point directly below vehicle center
        road_x, road_y = road.get_road_point(screen_dist_along_road)
        tangent_u, _, normal_up = road.get_unit_vectors()

        # 1. Soft contact shadow on the road
        shadow_start = (
            int(road_x - (self.length * 0.45) * tangent_u[0]),
            int(road_y - (self.length * 0.45) * tangent_u[1]),
        )
        shadow_end = (
            int(road_x + (self.length * 0.45) * tangent_u[0]),
            int(road_y + (self.length * 0.45) * tangent_u[1]),
        )
        pygame.draw.line(surface, (25, 25, 28), shadow_start, shadow_end, 4)

        # 2. Vehicle body (select active brake light surface if braking)
        base_body = self.body_surface_braking if is_braking else self.body_surface_normal
        rotated_body = pygame.transform.rotate(base_body, road.slope_angle)

        # Position body center above the road
        body_height_offset = 17.0
        body_center_x = road_x + body_height_offset * normal_up[0]
        body_center_y = road_y + body_height_offset * normal_up[1]

        rect = rotated_body.get_rect(center=(int(body_center_x), int(body_center_y)))
        surface.blit(rotated_body, rect)

        # 3. Rotating Alloy Wheels
        # Rear and front axle centers are exactly wheel_radius (10 px) above the road line
        rw_center_x = road_x - self.wheel_base_half * tangent_u[0] + self.wheel_radius * normal_up[0]
        rw_center_y = road_y - self.wheel_base_half * tangent_u[1] + self.wheel_radius * normal_up[1]

        fw_center_x = road_x + self.wheel_base_half * tangent_u[0] + self.wheel_radius * normal_up[0]
        fw_center_y = road_y + self.wheel_base_half * tangent_u[1] + self.wheel_radius * normal_up[1]

        # Draw both rotating wheels
        self._draw_alloy_wheel(surface, rw_center_x, rw_center_y, self.wheel_angle)
        self._draw_alloy_wheel(surface, fw_center_x, fw_center_y, self.wheel_angle)
