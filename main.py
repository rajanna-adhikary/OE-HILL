"""
Hill Hold Assist Simulator - Main Application
Clean, polished 2D driving simulator for college demonstration.
Minimal UI showing strictly:
  - Speed
  - Slope angle
  - Road type
  - Hill Hold status
Keyboard controls shown in a small corner.
"""

import sys
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    WINDOW_TITLE,
    PIXELS_PER_METER,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
)
from road import Road
from car import Car
from physics import PhysicsEngine
from controls import Controls
from hill_hold import HillHoldAssist
from buzzer import BuzzerManager


def draw_hud(screen, font_speed, font_regular, font_badge, car, road, hha):
    """
    Render a clean, minimal dashboard in top-left showing ONLY:
      1. Speed
      2. Slope angle
      3. Road type
      4. Hill Hold status
    """
    # Card background (white with soft rounded corners and subtle shadow/border)
    panel_rect = pygame.Rect(20, 20, 310, 155)
    # Background surface with slight translucency
    card_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (255, 255, 255, 245), (0, 0, panel_rect.width, panel_rect.height), border_radius=10)
    pygame.draw.rect(card_surf, (215, 220, 230, 255), (0, 0, panel_rect.width, panel_rect.height), width=1, border_radius=10)
    screen.blit(card_surf, panel_rect.topleft)

    # 1. Speed (large and prominent)
    speed_kmh = car.get_speed_kmh()
    speed_surf = font_speed.render(f"{speed_kmh:.1f} km/h", True, COLOR_TEXT_MAIN)
    screen.blit(speed_surf, (panel_rect.x + 18, panel_rect.y + 12))

    # 2. Slope angle
    slope = road.slope_angle
    if slope > 0.05:
        slope_str = f"Slope: +{slope:.1f}\u00b0 (Uphill)"
        slope_color = (190, 50, 30)
    elif slope < -0.05:
        slope_str = f"Slope: {slope:.1f}\u00b0 (Downhill)"
        slope_color = (30, 95, 180)
    else:
        slope_str = "Slope: 0.0\u00b0 (Flat)"
        slope_color = COLOR_TEXT_MUTED

    slope_surf = font_regular.render(slope_str, True, slope_color)
    screen.blit(slope_surf, (panel_rect.x + 18, panel_rect.y + 50))

    # 3. Road type
    surf_props = road.get_surface_props()
    surf_surf = font_regular.render(f"Road: {surf_props['name']}", True, COLOR_TEXT_MAIN)
    screen.blit(surf_surf, (panel_rect.x + 18, panel_rect.y + 74))

    # 4. Hill Hold status badge
    hha_status = hha.get_status_text()
    if hha_status == "HILL HOLD: ACTIVE":
        badge_text = f"HILL HOLD: ACTIVE ({hha.hold_timer:.1f}s)"
        bg_col = (255, 242, 225)
        border_col = (230, 125, 15)
        text_col = (210, 110, 10)
    elif hha_status == "HILL HOLD: ON":
        badge_text = "HILL HOLD: ON"
        bg_col = (235, 250, 235)
        border_col = (45, 160, 55)
        text_col = (35, 140, 45)
    else:  # HILL HOLD: OFF
        badge_text = "HILL HOLD: OFF"
        bg_col = (242, 244, 248)
        border_col = (180, 185, 195)
        text_col = (120, 125, 135)

    badge_rect = pygame.Rect(panel_rect.x + 16, panel_rect.y + 104, panel_rect.width - 32, 36)
    pygame.draw.rect(screen, bg_col, badge_rect, border_radius=6)
    pygame.draw.rect(screen, border_col, badge_rect, width=2, border_radius=6)

    status_surf = font_badge.render(badge_text, True, text_col)
    status_rect = status_surf.get_rect(center=badge_rect.center)
    screen.blit(status_surf, status_rect)


def draw_controls_corner(screen, font_title, font_keys):
    """
    Render keyboard controls in a neat, small corner card (bottom-right).
    """
    width = 250
    height = 95
    x = SCREEN_WIDTH - width - 18
    y = SCREEN_HEIGHT - height - 16

    card_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (20, 24, 32, 220), (0, 0, width, height), border_radius=8)
    pygame.draw.rect(card_surf, (80, 85, 100, 180), (0, 0, width, height), width=1, border_radius=8)
    screen.blit(card_surf, (x, y))

    # Header
    title_surf = font_title.render("CONTROLS", True, (190, 200, 215))
    screen.blit(title_surf, (x + 12, y + 8))

    # Left column of shortcuts
    col1_lines = [
        "[A] Gas       [B] Brake",
        "[H] Hill Hold [M] Sound",
    ]
    # Right column / surface selection
    col2_lines = [
        "[1-4] Surface",
        "[LEFT/RIGHT] Slope",
        "[R] Reset   [ESC] Exit",
    ]

    curr_y = y + 28
    for line in ["[A] Gas        [B] Brake", "[H] Hill Hold  [M] Sound", "[1-4] Surface  [LEFT/RIGHT] Slope", "[R] Reset      [ESC] Exit"]:
        line_surf = font_keys.render(line, True, (230, 235, 245))
        screen.blit(line_surf, (x + 12, curr_y))
        curr_y += 15


def main():
    """Main game loop."""
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # System fonts for crisp rendering
    font_speed = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_regular = pygame.font.SysFont("Segoe UI", 15)
    font_badge = pygame.font.SysFont("Segoe UI", 15, bold=True)
    font_ctrl_title = pygame.font.SysFont("Segoe UI", 11, bold=True)
    font_ctrl_keys = pygame.font.SysFont("Consolas", 11)

    # Initialize simulation components
    road = Road()
    car = Car()
    physics = PhysicsEngine()
    controls = Controls()
    hha = HillHoldAssist()
    buzzer = BuzzerManager()

    # Visual bounds for camera tracking
    max_visual_dist = 220.0

    running = True
    while running:
        # Frame-rate independent delta time
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        # 1. Event Handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        controls.process_events(events)

        if controls.exit_pressed:
            running = False

        if controls.reset_pressed:
            car.reset()
            hha.reset()
            buzzer.stop_all()

        # Handle sound toggle (Key 'M')
        if controls.toggle_sound_pressed:
            buzzer.toggle_sound()

        # Handle road surface selection (Keys 1, 2, 3, 4)
        if controls.selected_surface:
            road.set_surface(controls.selected_surface)

        # Handle Hill Hold toggle (Key 'H')
        if controls.toggle_hha_pressed:
            hha.toggle()

        # Handle Slope angle adjustment (LEFT / RIGHT arrow keys)
        if controls.slope_delta != 0.0:
            road.adjust_slope(controls.slope_delta)

        # Continuous inputs (pedals & held arrows)
        controls.update_continuous_input(dt)

        # 2. Hill Hold Assist Update
        hha_active = hha.update(
            dt=dt,
            velocity=car.velocity,
            slope_deg=road.slope_angle,
            user_brake_pressed=controls.brake,
            throttle_pressed=controls.accelerate,
        )

        # 3. Vehicle Physics Update
        surf_props = road.get_surface_props()
        car.update(
            is_accelerating=controls.accelerate,
            is_braking=controls.brake,
            slope_deg=road.slope_angle,
            dt=dt,
            physics_engine=physics,
            hha_active=hha_active,
            grip_coeff=surf_props["grip_coeff"],
            rolling_res_coeff=surf_props["rolling_res_coeff"],
        )

        # 4. Rollback Risk Detection for Warning Buzzer
        rollback_risk = (
            abs(road.slope_angle) >= 0.5
            and not hha_active
            and not controls.brake
            and not controls.accelerate
            and (
                (road.slope_angle > 0 and car.velocity < -0.12)
                or (road.slope_angle < 0 and car.velocity > 0.12)
            )
        )

        # Update Buzzer sound manager (state-based, no frame restarts)
        buzzer.update(hha_is_active=hha_active, rollback_risk_active=rollback_risk)

        # 5. Camera positioning along the inclined road
        car_dist_px = car.world_distance_m * PIXELS_PER_METER
        if car_dist_px > max_visual_dist:
            camera_offset = car_dist_px - max_visual_dist
            screen_dist = max_visual_dist
        elif car_dist_px < -max_visual_dist:
            camera_offset = car_dist_px - (-max_visual_dist)
            screen_dist = -max_visual_dist
        else:
            camera_offset = 0.0
            screen_dist = car_dist_px

        # 6. Render Scene
        road.draw(screen, camera_dist=camera_offset)
        car.draw(screen, road, screen_dist_along_road=screen_dist, is_braking=controls.brake)

        # Minimal Dashboard in top-left
        draw_hud(screen, font_speed, font_regular, font_badge, car, road, hha)

        # Small Controls reference card in bottom-right corner
        draw_controls_corner(screen, font_ctrl_title, font_ctrl_keys)

        pygame.display.flip()

    buzzer.stop_all()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

# Vercel Serverless Function entrypoint compatibility
def app(environ, start_response):
    status = "200 OK"
    response_headers = [("Content-type", "text/html; charset=utf-8")]
    start_response(status, response_headers)
    try:
        with open("index.html", "rb") as f:
            return [f.read()]
    except Exception:
        return [b"Hill Hold Assist Simulator"]

handler = app
application = app

