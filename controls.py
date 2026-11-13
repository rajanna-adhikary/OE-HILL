"""
Controls module for Phase 4 + Buzzer Integration.
Maps:
  - '1' -> Select Dry road
  - '2' -> Select Wet road
  - '3' -> Select Ice road
  - '4' -> Select Gravel road
  - 'A' (Hold) -> Accelerator
  - 'B' (Hold) -> Brake
  - 'H' (Press) -> Enable / Disable Hill Hold Assist
  - 'M' (Press) -> Toggle Buzzer Sound ON / OFF
  - 'LEFT' arrow -> Decrease slope angle
  - 'RIGHT' arrow -> Increase slope angle
  - 'R' (Press) -> Reset
  - 'ESC' (Press) -> Exit
"""

import pygame


class Controls:
    """Processes driver inputs, surface selections, audio toggles, and slope adjustments."""

    def __init__(self):
        self.accelerate = False
        self.brake = False
        self.reset_pressed = False
        self.exit_pressed = False
        self.toggle_hha_pressed = False
        self.toggle_sound_pressed = False
        self.slope_delta = 0.0
        self.selected_surface = None

        # Holding repeat timer for LEFT / RIGHT arrow keys
        self._hold_timer = 0.0
        self._repeat_delay = 0.25
        self._repeat_interval = 0.06

    def process_events(self, events):
        """Handle discrete key presses for surface selection, audio, reset, exit, HHA, and slope."""
        self.reset_pressed = False
        self.exit_pressed = False
        self.toggle_hha_pressed = False
        self.toggle_sound_pressed = False
        self.slope_delta = 0.0
        self.selected_surface = None

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 or event.key == pygame.K_KP1:
                    self.selected_surface = "DRY"
                elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                    self.selected_surface = "WET"
                elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                    self.selected_surface = "ICE"
                elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                    self.selected_surface = "GRAVEL"
                elif event.key == pygame.K_h:
                    self.toggle_hha_pressed = True
                elif event.key == pygame.K_m:
                    self.toggle_sound_pressed = True
                elif event.key == pygame.K_r:
                    self.reset_pressed = True
                elif event.key == pygame.K_ESCAPE:
                    self.exit_pressed = True
                elif event.key == pygame.K_LEFT:
                    self.slope_delta -= 1.0
                elif event.key == pygame.K_RIGHT:
                    self.slope_delta += 1.0

    def update_continuous_input(self, dt):
        """Update held-down pedals and held arrow keys with repeat rate."""
        keys = pygame.key.get_pressed()
        self.accelerate = keys[pygame.K_a]
        self.brake = keys[pygame.K_b]

        # Handle smooth holding of LEFT / RIGHT arrow keys
        left_held = keys[pygame.K_LEFT]
        right_held = keys[pygame.K_RIGHT]

        if left_held or right_held:
            self._hold_timer += dt
            if self._hold_timer > self._repeat_delay:
                step_direction = -1.0 if left_held else 1.0
                self.slope_delta += step_direction * (dt / self._repeat_interval)
        else:
            self._hold_timer = 0.0
