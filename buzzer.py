"""
Buzzer and audio warning management module.
Manages:
  - Heavy vehicle-style continuous warning buzzer during Hill Hold Assist (3 seconds)
  - Urgent pulsed rollback warning buzzer when vehicle rolls backward downhill on a slope
  - Sound ON/OFF setting
  - Frame-stable audio playback (sound does not restart every frame)
"""

import os
import pygame


class BuzzerManager:
    """Manages electronic vehicle warning buzzers and audio states."""

    STATE_IDLE = "IDLE"
    STATE_HHA = "HHA"
    STATE_ROLLBACK = "ROLLBACK"

    def __init__(self):
        self.sound_enabled = True
        self.current_state = self.STATE_IDLE
        self.initialized = False
        self.channel = None
        self.hha_buzzer = None
        self.rollback_buzzer = None

        self._init_audio()

    def _init_audio(self):
        """Initialize pygame mixer and load sound assets."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            self.channel = pygame.mixer.Channel(0)

            hha_path = os.path.join("assets", "sounds", "hha_buzzer.wav")
            rb_path = os.path.join("assets", "sounds", "rollback_warning.wav")

            if os.path.exists(hha_path):
                self.hha_buzzer = pygame.mixer.Sound(hha_path)
                self.hha_buzzer.set_volume(0.9)

            if os.path.exists(rb_path):
                self.rollback_buzzer = pygame.mixer.Sound(rb_path)
                self.rollback_buzzer.set_volume(0.95)

            self.initialized = True
        except Exception as e:
            print(f"Warning: Audio device initialization note: {e}")
            self.initialized = False

    def toggle_sound(self):
        """Toggle sound ON or OFF."""
        self.sound_enabled = not self.sound_enabled
        if not self.sound_enabled:
            self.stop_all()
        return self.sound_enabled

    def stop_all(self):
        """Immediately silence all buzzer channels."""
        if self.initialized and self.channel:
            try:
                self.channel.stop()
            except Exception:
                pass
        self.current_state = self.STATE_IDLE

    def update(self, hha_is_active, rollback_risk_active):
        """
        Update audio state based on simulation telemetry.
        Only triggers audio playback on state changes, preventing frame restarts.

        :param hha_is_active: True if Hill Hold Assist is currently active (holding).
        :param rollback_risk_active: True if vehicle is rolling backward downhill without braking.
        """
        if not self.sound_enabled or not self.initialized:
            if self.current_state != self.STATE_IDLE:
                self.stop_all()
            return

        # Determine target sound state based on priority
        # 1. HHA holding buzzer has highest priority during its 3-second hold window
        if hha_is_active:
            target_state = self.STATE_HHA
        # 2. Rollback urgent alert when vehicle rolls backward downhill on a slope
        elif rollback_risk_active:
            target_state = self.STATE_ROLLBACK
        else:
            target_state = self.STATE_IDLE

        # Prevent restarting sound if state has not changed
        if target_state == self.current_state:
            return

        # Handle transition
        if target_state == self.STATE_IDLE:
            self.stop_all()
        elif target_state == self.STATE_HHA:
            if self.channel and self.hha_buzzer:
                self.channel.stop()
                # Continuous loop for the entire duration of the hold
                self.channel.play(self.hha_buzzer, loops=-1)
            self.current_state = self.STATE_HHA
        elif target_state == self.STATE_ROLLBACK:
            if self.channel and self.rollback_buzzer:
                self.channel.stop()
                # Continuous urgent alarm loop while rollback risk persists
                self.channel.play(self.rollback_buzzer, loops=-1)
            self.current_state = self.STATE_ROLLBACK
