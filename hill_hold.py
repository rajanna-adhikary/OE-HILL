"""
Hill Hold Assist (HHA) module for Phase 3 & Phase 4.
Manages automatic brake retention to prevent rollback on slopes across all road conditions.
"""

from settings import HHA_HOLD_DURATION


class HillHoldAssist:
    """Simulates automotive automatic Hill Hold Assist logic."""

    def __init__(self):
        self.enabled = True
        self.is_ready = False
        self.is_active = False
        self.hold_timer = 0.0
        self.hold_duration = HHA_HOLD_DURATION
        self.was_braking = False

    def toggle(self):
        """Toggle Hill Hold Assist enabled state on or off."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.reset()
        return self.enabled

    def reset(self):
        """Reset internal states and cancel any active hold."""
        self.is_ready = False
        self.is_active = False
        self.hold_timer = 0.0
        self.was_braking = False

    def update(self, dt, velocity, slope_deg, user_brake_pressed, throttle_pressed):
        """
        Update the Hill Hold Assist system state.

        :param dt: Delta time in seconds.
        :param velocity: Current vehicle velocity in m/s.
        :param slope_deg: Current road slope in degrees.
        :param user_brake_pressed: True if driver is holding 'B'.
        :param throttle_pressed: True if driver is holding 'A'.
        :return: True if Hill Hold is actively holding the vehicle stationary, False otherwise.
        """
        if not self.enabled:
            self.reset()
            return False

        # If driver presses accelerator, immediately release hold
        if throttle_pressed:
            self.is_active = False
            self.is_ready = False
            self.hold_timer = 0.0

        if user_brake_pressed:
            # While driver holds manual brake, cancel any auto-hold
            self.is_active = False
            self.hold_timer = 0.0

            # When the vehicle is stopped or brought to standstill while braking, arm Hill Hold
            if abs(velocity) <= 0.20:
                self.is_ready = True
        else:
            # Driver released brake pedal: if system was ready, automatically activate!
            if self.was_braking and self.is_ready and not throttle_pressed:
                self.is_active = True
                self.hold_timer = self.hold_duration
                self.is_ready = False

            # If actively holding, count down the 3-second hold window
            if self.is_active:
                self.hold_timer -= dt
                if self.hold_timer <= 0.0:
                    self.is_active = False
                    self.hold_timer = 0.0

        self.was_braking = user_brake_pressed
        return self.is_active

    def get_status_text(self):
        """
        Return the exact simple status text:
          - HILL HOLD: OFF
          - HILL HOLD: ACTIVE
          - HILL HOLD: ON
        """
        if not self.enabled:
            return "HILL HOLD: OFF"
        if self.is_active:
            return "HILL HOLD: ACTIVE"
        return "HILL HOLD: ON"
