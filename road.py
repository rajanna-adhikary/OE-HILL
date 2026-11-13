"""
Road module for the Hill Hold Assist Simulator.
Renders an aesthetically refined inclined road with clear visual slope feedback,
a horizontal reference horizon, and scrolling lane markings.
"""

import math
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    ROAD_CENTER_X,
    ROAD_CENTER_Y,
    ROAD_THICKNESS,
    MIN_SLOPE_DEG,
    MAX_SLOPE_DEG,
    INITIAL_SLOPE_DEG,
    SURFACES,
    COLOR_SKY_TOP,
    COLOR_SKY_BOTTOM,
    COLOR_MOUNTAIN_FAR,
    COLOR_MOUNTAIN_NEAR,
    COLOR_GRASS_TOP,
    COLOR_GRASS_BOTTOM,
)


class Road:
    """Represents an inclined road with adjustable slope angle (-15° to +15°) and surface types."""

    def __init__(self, initial_slope=INITIAL_SLOPE_DEG, initial_surface="DRY"):
        self.slope_angle = initial_slope
        self.surface_key = initial_surface
        self.center_x = ROAD_CENTER_X
        self.center_y = ROAD_CENTER_Y
        self.thickness = ROAD_THICKNESS
        self.dash_length = 42.0
        self.dash_gap = 28.0
        self.cycle_length = self.dash_length + self.dash_gap

        # Pre-generate static horizontal background mountain ridges for visual horizon reference
        self.mountain_points_far = [
            (0, 360), (120, 310), (260, 340), (420, 290), (580, 335),
            (740, 295), (880, 330), (1000, 305), (1000, 600), (0, 600)
        ]
        self.mountain_points_near = [
            (0, 380), (160, 330), (320, 360), (480, 320), (660, 355),
            (820, 315), (1000, 345), (1000, 600), (0, 600)
        ]

    def set_surface(self, surface_key):
        """Update current road surface condition (DRY, WET, ICE, GRAVEL)."""
        if surface_key in SURFACES:
            self.surface_key = surface_key

    def get_surface_props(self):
        """Return properties dictionary for current surface."""
        return SURFACES[self.surface_key]

    def adjust_slope(self, delta_degrees):
        """Increase or decrease slope angle, clamped between -15° and +15°."""
        self.slope_angle = max(MIN_SLOPE_DEG, min(MAX_SLOPE_DEG, self.slope_angle + delta_degrees))

    def get_unit_vectors(self):
        """
        Return (tangent_u, normal_down, normal_up).
        tangent_u points along the road forward (uphill if slope > 0).
        normal_down points into the road.
        normal_up points into the sky.
        """
        rad = math.radians(self.slope_angle)
        cos_t = math.cos(rad)
        sin_t = math.sin(rad)

        tangent_u = (cos_t, -sin_t)
        normal_down = (sin_t, cos_t)
        normal_up = (-sin_t, -cos_t)
        return tangent_u, normal_down, normal_up

    def get_road_point(self, distance_along_road):
        """
        Calculate screen coordinates (x, y) along the road line at a given distance from center.
        """
        tangent_u, _, _ = self.get_unit_vectors()
        x = self.center_x + distance_along_road * tangent_u[0]
        y = self.center_y + distance_along_road * tangent_u[1]
        return x, y

    def draw(self, surface, camera_dist=0.0):
        """
        Render sky gradient, distant horizontal horizon, inclined asphalt, and scrolling markings.
        """
        # 1. Sky gradient
        sky_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, COLOR_SKY_TOP, sky_rect)
        # Soft lower sky blend
        lower_sky = pygame.Rect(0, 150, SCREEN_WIDTH, SCREEN_HEIGHT - 150)
        pygame.draw.rect(surface, COLOR_SKY_BOTTOM, lower_sky)

        # 2. Horizontal background mountain silhouettes (provides true horizontal visual reference)
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_FAR, self.mountain_points_far)
        pygame.draw.polygon(surface, COLOR_MOUNTAIN_NEAR, self.mountain_points_near)

        tangent_u, normal_down, _ = self.get_unit_vectors()
        surf_props = self.get_surface_props()
        road_color = surf_props["color_road"]
        marking_color = surf_props["color_marking"]

        # Road endpoints spanning well past screen edges
        road_half_span = 720.0
        p_left = (
            self.center_x - road_half_span * tangent_u[0],
            self.center_y - road_half_span * tangent_u[1],
        )
        p_right = (
            self.center_x + road_half_span * tangent_u[0],
            self.center_y + road_half_span * tangent_u[1],
        )

        # 3. Ground polygon covering the region beneath the road
        ground_poly = [
            (-50, SCREEN_HEIGHT + 50),
            p_left,
            p_right,
            (SCREEN_WIDTH + 50, SCREEN_HEIGHT + 50),
        ]
        pygame.draw.polygon(surface, COLOR_GRASS_TOP, ground_poly)

        # 4. Inclined road surface strip
        t = self.thickness
        road_poly = [
            p_left,
            p_right,
            (p_right[0] + t * normal_down[0], p_right[1] + t * normal_down[1]),
            (p_left[0] + t * normal_down[0], p_left[1] + t * normal_down[1]),
        ]
        pygame.draw.polygon(surface, road_color, road_poly)

        # Top road edge line (solid)
        pygame.draw.line(surface, marking_color, p_left, p_right, 3)

        # Lower road edge curb line
        curb_p1 = (p_left[0] + t * normal_down[0], p_left[1] + t * normal_down[1])
        curb_p2 = (p_right[0] + t * normal_down[0], p_right[1] + t * normal_down[1])
        pygame.draw.line(surface, (80, 85, 90), curb_p1, curb_p2, 2)

        # 5. Dashed center lane markings along the incline
        dash_normal = (t * 0.5 * normal_down[0], t * 0.5 * normal_down[1])
        scroll_offset = -(camera_dist % self.cycle_length)
        d = -road_half_span + scroll_offset

        while d < road_half_span:
            d_start = d
            d_end = d + self.dash_length

            pt1 = (
                self.center_x + d_start * tangent_u[0] + dash_normal[0],
                self.center_y + d_start * tangent_u[1] + dash_normal[1],
            )
            pt2 = (
                self.center_x + d_end * tangent_u[0] + dash_normal[0],
                self.center_y + d_end * tangent_u[1] + dash_normal[1],
            )

            pygame.draw.line(surface, marking_color, pt1, pt2, 3)
            d += self.cycle_length
