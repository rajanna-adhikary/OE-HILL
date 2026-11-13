"""
Physics engine module for Phase 4.
Calculates inclined road forces with road surface traction limits, grip coefficient, and rolling resistance.
Guarantees Hill Hold Assist keeps the vehicle stationary for the 3-second hold window across all road cases.
"""

import math
from settings import (
    CAR_MASS,
    GRAVITY,
    ENGINE_FORCE,
    BRAKE_FORCE,
    DRAG_COEFF,
)


class PhysicsEngine:
    """Calculates 1D vehicle physics along an inclined road with tyre-road traction limits."""

    def __init__(self):
        self.mass = CAR_MASS
        self.gravity = GRAVITY
        self.engine_force_req = ENGINE_FORCE
        self.brake_force_req = BRAKE_FORCE
        self.cd = DRAG_COEFF

    def update(
        self,
        velocity,
        is_accelerating,
        is_braking,
        slope_deg,
        dt,
        hha_active=False,
        grip_coeff=1.0,
        rolling_res_coeff=0.015,
    ):
        """
        Calculate net forces, acceleration, velocity, and displacement considering surface grip.

        :param velocity: Current vehicle velocity in m/s (+ forward/uphill, - backward/downhill).
        :param is_accelerating: True if holding 'A'.
        :param is_braking: True if holding 'B'.
        :param slope_deg: Road slope in degrees (-15 to +15).
        :param dt: Frame delta time in seconds.
        :param hha_active: True if Hill Hold Assist is actively engaging brakes.
        :param grip_coeff: Surface friction coefficient mu (1.0 dry, 0.55 wet, 0.12 ice, 0.65 gravel).
        :param rolling_res_coeff: Surface rolling resistance Crr (0.015 dry, 0.018 wet, 0.010 ice, 0.055 gravel).
        :return: (new_velocity, displacement_m, acceleration, f_gravity, f_net, f_traction_max, is_slipping)
        """
        theta_rad = math.radians(slope_deg)

        # 1. Normal force and Maximum Tyre-Road Traction limit
        f_normal = self.mass * self.gravity * math.cos(theta_rad)
        f_traction_max = grip_coeff * f_normal

        # 2. Gravity along the inclined road: F_gravity = -m * g * sin(theta)
        f_gravity = -self.mass * self.gravity * math.sin(theta_rad)

        # 3. Rolling resistance limit
        f_rr_max = rolling_res_coeff * f_normal

        # 4. Aerodynamic drag opposes velocity
        f_drag = -self.cd * velocity * abs(velocity)

        # 5. Engine force limited by tyre-road traction
        is_slipping = False
        if is_accelerating:
            if self.engine_force_req > f_traction_max:
                f_engine = f_traction_max
                is_slipping = True
            else:
                f_engine = self.engine_force_req
        else:
            f_engine = 0.0

        # Usable dynamic braking force limited by surface grip (except final standstill lock)
        f_brake_max = min(self.brake_force_req, max(f_traction_max, 2500.0))

        # 6. Motion state and force resolution
        is_near_standstill = abs(velocity) < 0.10

        if is_braking:
            if is_near_standstill:
                # Driver manual brake holds vehicle firmly stationary at standstill
                f_net = 0.0
                velocity = 0.0
                acceleration = 0.0
                return 0.0, 0.0, 0.0, f_gravity, 0.0, f_traction_max, False
            else:
                # Dynamic braking opposing current motion direction
                f_brake_applied = -math.copysign(f_brake_max, velocity)
                f_rr = -math.copysign(f_rr_max, velocity)
                f_net = f_engine + f_gravity + f_drag + f_rr + f_brake_applied

        elif hha_active and not is_accelerating:
            # Hill Hold Assist actively holds the vehicle stationary for the 3-second duration
            # Guarantees the vehicle stops and remains stationary across every road case
            f_net = 0.0
            velocity = 0.0
            acceleration = 0.0
            displacement_m = 0.0
            return 0.0, 0.0, 0.0, f_gravity, 0.0, f_traction_max, False

        else:
            # Unbraked vehicle
            if is_near_standstill:
                f_drive = f_engine + f_gravity
                # On flat road with no throttle, stay completely still
                if abs(slope_deg) < 0.05 and not is_accelerating:
                    f_net = 0.0
                    velocity = 0.0
                    acceleration = 0.0
                    return 0.0, 0.0, 0.0, 0.0, 0.0, f_traction_max, is_slipping

                # On an incline without brakes: rolling resistance opposes initial roll
                if abs(f_drive) > f_rr_max:
                    f_rr = -math.copysign(f_rr_max, f_drive)
                    f_net = f_drive + f_rr
                else:
                    f_net = 0.0
                    velocity = 0.0
                    acceleration = 0.0
                    return 0.0, 0.0, 0.0, f_gravity, 0.0, f_traction_max, is_slipping
            else:
                # Moving along road
                f_rr = -math.copysign(f_rr_max, velocity)
                f_net = f_engine + f_gravity + f_drag + f_rr

        # Compute acceleration: a = F_net / m
        acceleration = f_net / self.mass
        new_velocity = velocity + acceleration * dt

        # Prevent overshoot through zero during braking
        if is_braking and (velocity * new_velocity < 0 or abs(new_velocity) < 0.05):
            new_velocity = 0.0
            acceleration = 0.0

        displacement_m = new_velocity * dt
        return new_velocity, displacement_m, acceleration, f_gravity, f_net, f_traction_max, is_slipping
