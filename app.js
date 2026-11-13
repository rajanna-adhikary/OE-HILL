/**
 * Hill Hold Assist (HHA) Driving Simulator - Web Engine
 * Pixel-perfect canvas port of the Python/Pygame simulator.
 * Preserves 100% of the original frontend visuals, physics formulations,
 * state machines, and audio warning systems.
 */

// ==========================================
// 1. SIMULATION SETTINGS & CONSTANTS
// ==========================================
const SCREEN_WIDTH = 1000;
const SCREEN_HEIGHT = 600;
const FPS = 60;

const ROAD_CENTER_X = 500.0;
const ROAD_CENTER_Y = 380.0;
const ROAD_THICKNESS = 28.0;
const MIN_SLOPE_DEG = -15.0;
const MAX_SLOPE_DEG = 15.0;
const SLOPE_STEP_DEG = 1.0;
const INITIAL_SLOPE_DEG = 0.0;

const CAR_MASS = 1200.0;          // Vehicle mass in kg
const GRAVITY = 9.81;             // m/s^2
const ENGINE_FORCE = 5800.0;      // N
const BRAKE_FORCE = 8500.0;       // N
const DRAG_COEFF = 0.38;          // Aerodynamic drag
const PIXELS_PER_METER = 20.0;    // 20 px = 1 meter
const HHA_HOLD_DURATION = 3.0;    // seconds

const SURFACES = {
  DRY: {
    name: "Dry Road",
    grip_coeff: 1.0,
    rolling_res_coeff: 0.015,
    color_road: "rgb(52, 54, 58)",
    color_marking: "rgb(250, 250, 250)",
    desc: "Normal Grip (100%)",
  },
  WET: {
    name: "Wet Road",
    grip_coeff: 0.55,
    rolling_res_coeff: 0.018,
    color_road: "rgb(35, 45, 54)",
    color_marking: "rgb(210, 225, 235)",
    desc: "Reduced Grip (55%)",
  },
  ICE: {
    name: "Ice Road",
    grip_coeff: 0.12,
    rolling_res_coeff: 0.010,
    color_road: "rgb(210, 230, 242)",
    color_marking: "rgb(140, 175, 205)",
    desc: "Very Low Grip (12%)",
  },
  GRAVEL: {
    name: "Gravel Road",
    grip_coeff: 0.65,
    rolling_res_coeff: 0.055,
    color_road: "rgb(122, 100, 78)",
    color_marking: "rgb(215, 205, 180)",
    desc: "Moderate Grip (65%)",
  },
};

// Aesthetic Colors
const COLOR_SKY_TOP = "rgb(165, 205, 245)";
const COLOR_SKY_BOTTOM = "rgb(215, 235, 255)";
const COLOR_MOUNTAIN_FAR = "rgb(145, 175, 205)";
const COLOR_MOUNTAIN_NEAR = "rgb(115, 150, 180)";
const COLOR_GRASS_TOP = "rgb(95, 175, 95)";

const COLOR_CAR_BODY = "rgb(215, 40, 40)";
const COLOR_CAR_ACCENT = "rgb(175, 25, 25)";
const COLOR_CAR_ROOF = "rgb(35, 35, 40)";
const COLOR_CAR_WINDOW = "rgb(195, 225, 250)";
const COLOR_CAR_WHEEL = "rgb(35, 35, 38)";
const COLOR_CAR_RIM = "rgb(210, 215, 225)";
const COLOR_CAR_HUB = "rgb(90, 95, 105)";
const COLOR_HEADLIGHT = "rgb(255, 250, 180)";
const COLOR_TAILLIGHT = "rgb(255, 35, 35)";
const COLOR_TAILLIGHT_DIM = "rgb(160, 20, 20)";

const COLOR_TEXT_MAIN = "rgb(20, 25, 35)";
const COLOR_TEXT_MUTED = "rgb(110, 115, 125)";

// Helper function for rounded rectangles in Canvas
function drawRoundedRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

// ==========================================
// 2. ROAD MODULE
// ==========================================
class Road {
  constructor(initialSlope = INITIAL_SLOPE_DEG, initialSurface = "DRY") {
    this.slope_angle = initialSlope;
    this.surface_key = initialSurface;
    this.center_x = ROAD_CENTER_X;
    this.center_y = ROAD_CENTER_Y;
    this.thickness = ROAD_THICKNESS;
    this.dash_length = 42.0;
    this.dash_gap = 28.0;
    this.cycle_length = this.dash_length + this.dash_gap;

    this.mountain_points_far = [
      [0, 360], [120, 310], [260, 340], [420, 290], [580, 335],
      [740, 295], [880, 330], [1000, 305], [1000, 600], [0, 600]
    ];
    this.mountain_points_near = [
      [0, 380], [160, 330], [320, 360], [480, 320], [660, 355],
      [820, 315], [1000, 345], [1000, 600], [0, 600]
    ];
  }

  setSurface(key) {
    if (SURFACES[key]) {
      this.surface_key = key;
    }
  }

  getSurfaceProps() {
    return SURFACES[this.surface_key];
  }

  adjustSlope(delta) {
    this.slope_angle = Math.max(MIN_SLOPE_DEG, Math.min(MAX_SLOPE_DEG, this.slope_angle + delta));
  }

  getUnitVectors() {
    const rad = (this.slope_angle * Math.PI) / 180.0;
    const cos_t = Math.cos(rad);
    const sin_t = Math.sin(rad);

    const tangent_u = [cos_t, -sin_t];
    const normal_down = [sin_t, cos_t];
    const normal_up = [-sin_t, -cos_t];
    return { tangent_u, normal_down, normal_up };
  }

  getRoadPoint(distAlongRoad) {
    const { tangent_u } = this.getUnitVectors();
    const x = this.center_x + distAlongRoad * tangent_u[0];
    const y = this.center_y + distAlongRoad * tangent_u[1];
    return [x, y];
  }

  draw(ctx, cameraDist = 0.0) {
    // 1. Sky Gradient & lower sky
    ctx.fillStyle = COLOR_SKY_TOP;
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    ctx.fillStyle = COLOR_SKY_BOTTOM;
    ctx.fillRect(0, 150, SCREEN_WIDTH, SCREEN_HEIGHT - 150);

    // 2. Far Mountain Silhouette
    ctx.fillStyle = COLOR_MOUNTAIN_FAR;
    ctx.beginPath();
    ctx.moveTo(this.mountain_points_far[0][0], this.mountain_points_far[0][1]);
    for (let i = 1; i < this.mountain_points_far.length; i++) {
      ctx.lineTo(this.mountain_points_far[i][0], this.mountain_points_far[i][1]);
    }
    ctx.closePath();
    ctx.fill();

    // Near Mountain Silhouette
    ctx.fillStyle = COLOR_MOUNTAIN_NEAR;
    ctx.beginPath();
    ctx.moveTo(this.mountain_points_near[0][0], this.mountain_points_near[0][1]);
    for (let i = 1; i < this.mountain_points_near.length; i++) {
      ctx.lineTo(this.mountain_points_near[i][0], this.mountain_points_near[i][1]);
    }
    ctx.closePath();
    ctx.fill();

    const { tangent_u, normal_down } = this.getUnitVectors();
    const surf_props = this.getSurfaceProps();
    const road_color = surf_props.color_road;
    const marking_color = surf_props.color_marking;

    const road_half_span = 720.0;
    const p_left = [
      this.center_x - road_half_span * tangent_u[0],
      this.center_y - road_half_span * tangent_u[1],
    ];
    const p_right = [
      this.center_x + road_half_span * tangent_u[0],
      this.center_y + road_half_span * tangent_u[1],
    ];

    // 3. Ground beneath road
    ctx.fillStyle = COLOR_GRASS_TOP;
    ctx.beginPath();
    ctx.moveTo(-50, SCREEN_HEIGHT + 50);
    ctx.lineTo(p_left[0], p_left[1]);
    ctx.lineTo(p_right[0], p_right[1]);
    ctx.lineTo(SCREEN_WIDTH + 50, SCREEN_HEIGHT + 50);
    ctx.closePath();
    ctx.fill();

    // 4. Inclined road surface strip
    const t = this.thickness;
    const road_poly = [
      p_left,
      p_right,
      [p_right[0] + t * normal_down[0], p_right[1] + t * normal_down[1]],
      [p_left[0] + t * normal_down[0], p_left[1] + t * normal_down[1]],
    ];

    ctx.fillStyle = road_color;
    ctx.beginPath();
    ctx.moveTo(road_poly[0][0], road_poly[0][1]);
    for (let i = 1; i < road_poly.length; i++) {
      ctx.lineTo(road_poly[i][0], road_poly[i][1]);
    }
    ctx.closePath();
    ctx.fill();

    // Top road edge line (solid)
    ctx.strokeStyle = marking_color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(p_left[0], p_left[1]);
    ctx.lineTo(p_right[0], p_right[1]);
    ctx.stroke();

    // Lower road curb line
    ctx.strokeStyle = "rgb(80, 85, 90)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(p_left[0] + t * normal_down[0], p_left[1] + t * normal_down[1]);
    ctx.lineTo(p_right[0] + t * normal_down[0], p_right[1] + t * normal_down[1]);
    ctx.stroke();

    // 5. Dashed center lane markings along the incline
    const dash_normal = [t * 0.5 * normal_down[0], t * 0.5 * normal_down[1]];
    const scroll_offset = -((cameraDist % this.cycle_length + this.cycle_length) % this.cycle_length);
    let d = -road_half_span + scroll_offset;

    ctx.strokeStyle = marking_color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    while (d < road_half_span) {
      const d_start = d;
      const d_end = d + this.dash_length;

      const pt1 = [
        this.center_x + d_start * tangent_u[0] + dash_normal[0],
        this.center_y + d_start * tangent_u[1] + dash_normal[1],
      ];
      const pt2 = [
        this.center_x + d_end * tangent_u[0] + dash_normal[0],
        this.center_y + d_end * tangent_u[1] + dash_normal[1],
      ];

      ctx.moveTo(pt1[0], pt1[1]);
      ctx.lineTo(pt2[0], pt2[1]);
      d += this.cycle_length;
    }
    ctx.stroke();
  }
}

// ==========================================
// 3. VEHICLE DYNAMICS MODULE
// ==========================================
class Car {
  constructor() {
    this.length = 104;
    this.height = 34;
    this.wheel_radius = 10.0;
    this.wheel_base_half = 28.0;

    this.world_distance_m = 0.0;
    this.velocity = 0.0;
    this.acceleration = 0.0;
    this.f_gravity = 0.0;
    this.f_net = 0.0;
    this.f_traction_max = 0.0;
    this.is_slipping = false;
    this.wheel_angle = 0.0;
  }

  reset() {
    this.world_distance_m = 0.0;
    this.velocity = 0.0;
    this.acceleration = 0.0;
    this.f_gravity = 0.0;
    this.f_net = 0.0;
    this.wheel_angle = 0.0;
    this.is_slipping = false;
  }

  getSpeedKmh() {
    return Math.abs(this.velocity) * 3.6;
  }

  update(isAccelerating, isBraking, slopeDeg, dt, physicsEngine, hhaActive, gripCoeff, rollingResCoeff) {
    const res = physicsEngine.update(
      this.velocity,
      isAccelerating,
      isBraking,
      slopeDeg,
      dt,
      hhaActive,
      gripCoeff,
      rollingResCoeff
    );

    this.velocity = res.velocity;
    this.acceleration = res.acceleration;
    this.f_gravity = res.f_gravity;
    this.f_net = res.f_net;
    this.f_traction_max = res.f_traction_max;
    this.is_slipping = res.is_slipping;
    this.world_distance_m += res.displacement_m;

    // Wheel rotation accumulation
    const disp_px = res.displacement_m * PIXELS_PER_METER;
    const delta_angle_deg = (disp_px / this.wheel_radius) * (180.0 / Math.PI);
    this.wheel_angle = (this.wheel_angle + delta_angle_deg) % 360.0;
  }

  _drawAlloyWheel(ctx, cx, cy, rotationDeg) {
    const r = this.wheel_radius;

    // 1. Dark rubber tyre
    ctx.fillStyle = COLOR_CAR_WHEEL;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();

    // Tread ring highlight
    ctx.strokeStyle = "rgb(55, 58, 65)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 2. Silver alloy rim
    const rim_r = 6.5;
    ctx.fillStyle = COLOR_CAR_RIM;
    ctx.beginPath();
    ctx.arc(cx, cy, rim_r, 0, Math.PI * 2);
    ctx.fill();

    // 3. 5 Rotating alloy spokes
    const rad_rot = (rotationDeg * Math.PI) / 180.0;
    ctx.strokeStyle = "rgb(90, 95, 105)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = rad_rot + i * ((2.0 * Math.PI) / 5.0);
      const spoke_x = cx + Math.cos(angle) * (rim_r - 0.5);
      const spoke_y = cy + Math.sin(angle) * (rim_r - 0.5);
      ctx.moveTo(cx, cy);
      ctx.lineTo(spoke_x, spoke_y);
    }
    ctx.stroke();

    // 4. Central axle cap
    ctx.fillStyle = COLOR_CAR_HUB;
    ctx.beginPath();
    ctx.arc(cx, cy, 2, 0, Math.PI * 2);
    ctx.fill();
  }

  draw(ctx, road, screenDistAlongRoad, isBraking = false) {
    const [road_x, road_y] = road.getRoadPoint(screenDistAlongRoad);
    const { tangent_u, normal_up } = road.getUnitVectors();

    // 1. Soft contact shadow on road
    const shadow_start = [
      road_x - (this.length * 0.45) * tangent_u[0],
      road_y - (this.length * 0.45) * tangent_u[1],
    ];
    const shadow_end = [
      road_x + (this.length * 0.45) * tangent_u[0],
      road_y + (this.length * 0.45) * tangent_u[1],
    ];

    ctx.strokeStyle = "rgb(25, 25, 28)";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(shadow_start[0], shadow_start[1]);
    ctx.lineTo(shadow_end[0], shadow_end[1]);
    ctx.stroke();

    // 2. Draw Aerodynamic Vehicle Body
    const body_height_offset = 17.0;
    const body_center_x = road_x + body_height_offset * normal_up[0];
    const body_center_y = road_y + body_height_offset * normal_up[1];

    ctx.save();
    ctx.translate(body_center_x, body_center_y);
    // Rotate counter-clockwise with positive slope angle (matching Pygame)
    ctx.rotate((-road.slope_angle * Math.PI) / 180.0);
    ctx.translate(-52, -17); // Local origin to top-left of 104x34 box

    // 2.1 Roof / Cabin profile
    ctx.fillStyle = COLOR_CAR_ROOF;
    ctx.beginPath();
    ctx.moveTo(22, 20);
    ctx.lineTo(36, 4);
    ctx.lineTo(68, 4);
    ctx.lineTo(82, 20);
    ctx.closePath();
    ctx.fill();

    // 2.2 Main Ruby Red Metallic Body
    ctx.fillStyle = COLOR_CAR_BODY;
    ctx.beginPath();
    ctx.moveTo(4, 20);
    ctx.lineTo(8, 15);
    ctx.lineTo(22, 17);
    ctx.lineTo(82, 17);
    ctx.lineTo(98, 20);
    ctx.lineTo(102, 26);
    ctx.lineTo(88, 26);
    ctx.lineTo(82, 22);
    ctx.lineTo(68, 26);
    ctx.lineTo(42, 26);
    ctx.lineTo(38, 22);
    ctx.lineTo(24, 26);
    ctx.lineTo(2, 26);
    ctx.closePath();
    ctx.fill();

    // Lower skirt accent
    ctx.fillStyle = COLOR_CAR_ACCENT;
    ctx.beginPath();
    ctx.moveTo(2, 25);
    ctx.lineTo(102, 25);
    ctx.lineTo(100, 28);
    ctx.lineTo(4, 28);
    ctx.closePath();
    ctx.fill();

    // 2.3 Tinted Windows
    ctx.fillStyle = COLOR_CAR_WINDOW;
    // Front window
    ctx.beginPath();
    ctx.moveTo(54, 18);
    ctx.lineTo(54, 6);
    ctx.lineTo(66, 6);
    ctx.lineTo(78, 18);
    ctx.closePath();
    ctx.fill();

    // Rear window
    ctx.beginPath();
    ctx.moveTo(26, 18);
    ctx.lineTo(38, 6);
    ctx.lineTo(51, 6);
    ctx.lineTo(51, 18);
    ctx.closePath();
    ctx.fill();

    // B-Pillar divider
    ctx.strokeStyle = "rgb(40, 42, 48)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(52, 6);
    ctx.lineTo(52, 19);
    ctx.stroke();

    // 2.4 Headlight (LED projector)
    ctx.fillStyle = COLOR_HEADLIGHT;
    ctx.beginPath();
    ctx.moveTo(98, 20);
    ctx.lineTo(103, 23);
    ctx.lineTo(99, 25);
    ctx.lineTo(95, 22);
    ctx.closePath();
    ctx.fill();

    // 2.5 Taillight / Active Brake light
    const taillightColor = isBraking ? COLOR_TAILLIGHT : COLOR_TAILLIGHT_DIM;
    ctx.fillStyle = taillightColor;
    drawRoundedRect(ctx, 3, 18, 5, 6, 2);
    ctx.fill();

    if (isBraking) {
      ctx.fillStyle = "rgb(255, 120, 120)";
      drawRoundedRect(ctx, 2, 19, 3, 4, 1);
      ctx.fill();
    }

    ctx.restore();

    // 3. Rotating Alloy Wheels
    const rw_center_x = road_x - this.wheel_base_half * tangent_u[0] + this.wheel_radius * normal_up[0];
    const rw_center_y = road_y - this.wheel_base_half * tangent_u[1] + this.wheel_radius * normal_up[1];

    const fw_center_x = road_x + this.wheel_base_half * tangent_u[0] + this.wheel_radius * normal_up[0];
    const fw_center_y = road_y + this.wheel_base_half * tangent_u[1] + this.wheel_radius * normal_up[1];

    this._drawAlloyWheel(ctx, rw_center_x, rw_center_y, this.wheel_angle);
    this._drawAlloyWheel(ctx, fw_center_x, fw_center_y, this.wheel_angle);
  }
}

// ==========================================
// 4. PHYSICS ENGINE MODULE
// ==========================================
class PhysicsEngine {
  constructor() {
    this.mass = CAR_MASS;
    this.gravity = GRAVITY;
    this.engine_force_req = ENGINE_FORCE;
    this.brake_force_req = BRAKE_FORCE;
    this.cd = DRAG_COEFF;
  }

  update(velocity, isAccelerating, isBraking, slopeDeg, dt, hhaActive = false, gripCoeff = 1.0, rollingResCoeff = 0.015) {
    const theta_rad = (slopeDeg * Math.PI) / 180.0;

    // 1. Normal force and traction limit
    const f_normal = this.mass * this.gravity * Math.cos(theta_rad);
    const f_traction_max = gripCoeff * f_normal;

    // 2. Incline gravity force: F_gravity = -m * g * sin(theta)
    const f_gravity = -this.mass * this.gravity * Math.sin(theta_rad);

    // 3. Rolling resistance limit
    const f_rr_max = rollingResCoeff * f_normal;

    // 4. Aerodynamic drag
    const f_drag = -this.cd * velocity * Math.abs(velocity);

    // 5. Engine force limited by traction
    let f_engine = 0.0;
    let is_slipping = false;

    if (isAccelerating) {
      if (this.engine_force_req > f_traction_max) {
        f_engine = f_traction_max;
        is_slipping = true;
      } else {
        f_engine = this.engine_force_req;
      }
    }

    const f_brake_max = Math.min(this.brake_force_req, Math.max(f_traction_max, 2500.0));
    const is_near_standstill = Math.abs(velocity) < 0.10;
    let f_net = 0.0;

    if (isBraking) {
      if (is_near_standstill) {
        return {
          velocity: 0.0,
          displacement_m: 0.0,
          acceleration: 0.0,
          f_gravity,
          f_net: 0.0,
          f_traction_max,
          is_slipping: false,
        };
      } else {
        const sign = Math.sign(velocity) || 1;
        const f_brake_applied = -sign * f_brake_max;
        const f_rr = -sign * f_rr_max;
        f_net = f_engine + f_gravity + f_drag + f_rr + f_brake_applied;
      }
    } else if (hhaActive && !isAccelerating) {
      // Hill Hold Assist active lock
      return {
        velocity: 0.0,
        displacement_m: 0.0,
        acceleration: 0.0,
        f_gravity,
        f_net: 0.0,
        f_traction_max,
        is_slipping: false,
      };
    } else {
      // Unbraked vehicle
      if (is_near_standstill) {
        const f_drive = f_engine + f_gravity;
        if (Math.abs(slopeDeg) < 0.05 && !isAccelerating) {
          return {
            velocity: 0.0,
            displacement_m: 0.0,
            acceleration: 0.0,
            f_gravity: 0.0,
            f_net: 0.0,
            f_traction_max,
            is_slipping,
          };
        }

        if (Math.abs(f_drive) > f_rr_max) {
          const sign = Math.sign(f_drive) || 1;
          const f_rr = -sign * f_rr_max;
          f_net = f_drive + f_rr;
        } else {
          return {
            velocity: 0.0,
            displacement_m: 0.0,
            acceleration: 0.0,
            f_gravity,
            f_net: 0.0,
            f_traction_max,
            is_slipping,
          };
        }
      } else {
        const sign = Math.sign(velocity) || 1;
        const f_rr = -sign * f_rr_max;
        f_net = f_engine + f_gravity + f_drag + f_rr;
      }
    }

    let acceleration = f_net / this.mass;
    let new_velocity = velocity + acceleration * dt;

    if (isBraking && (velocity * new_velocity < 0 || Math.abs(new_velocity) < 0.05)) {
      new_velocity = 0.0;
      acceleration = 0.0;
    }

    const displacement_m = new_velocity * dt;
    return {
      velocity: new_velocity,
      displacement_m,
      acceleration,
      f_gravity,
      f_net,
      f_traction_max,
      is_slipping,
    };
  }
}

// ==========================================
// 5. HILL HOLD ASSIST STATE MACHINE
// ==========================================
class HillHoldAssist {
  constructor() {
    this.enabled = true;
    this.is_ready = false;
    this.is_active = false;
    this.hold_timer = 0.0;
    this.hold_duration = HHA_HOLD_DURATION;
    this.was_braking = false;
  }

  toggle() {
    this.enabled = !this.enabled;
    if (!this.enabled) {
      this.reset();
    }
    return this.enabled;
  }

  reset() {
    this.is_ready = false;
    this.is_active = false;
    this.hold_timer = 0.0;
    this.was_braking = false;
  }

  update(dt, velocity, slopeDeg, userBrakePressed, throttlePressed) {
    if (!this.enabled) {
      this.reset();
      return false;
    }

    if (throttlePressed) {
      this.is_active = false;
      this.is_ready = false;
      this.hold_timer = 0.0;
    }

    if (userBrakePressed) {
      this.is_active = false;
      this.hold_timer = 0.0;
      if (Math.abs(velocity) <= 0.20) {
        this.is_ready = true;
      }
    } else {
      if (this.was_braking && this.is_ready && !throttlePressed) {
        this.is_active = true;
        this.hold_timer = this.hold_duration;
        this.is_ready = false;
      }

      if (this.is_active) {
        this.hold_timer -= dt;
        if (this.hold_timer <= 0.0) {
          this.is_active = false;
          this.hold_timer = 0.0;
        }
      }
    }

    this.was_braking = userBrakePressed;
    return this.is_active;
  }

  getStatusText() {
    if (!this.enabled) return "HILL HOLD: OFF";
    if (this.is_active) return "HILL HOLD: ACTIVE";
    return "HILL HOLD: ON";
  }
}

// ==========================================
// 6. AUDIO & BUZZER MANAGER (Web Audio + Files)
// ==========================================
class BuzzerManager {
  constructor() {
    this.sound_enabled = true;
    this.current_state = "IDLE";
    this.audioContext = null;
    this.activeOsc = null;
    this.activeGain = null;
    this.audioHha = null;
    this.audioRollback = null;
    this.useSynth = false;

    this._initAudio();
  }

  _initAudio() {
    try {
      this.audioHha = new Audio("assets/sounds/hha_buzzer.wav");
      this.audioHha.loop = true;

      this.audioRollback = new Audio("assets/sounds/rollback_warning.wav");
      this.audioRollback.loop = true;
    } catch (e) {
      this.useSynth = true;
    }
  }

  _ensureWebAudio() {
    if (!this.audioContext) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioContext = new AudioCtx();
      }
    }
    if (this.audioContext && this.audioContext.state === "suspended") {
      this.audioContext.resume();
    }
  }

  toggleSound() {
    this.sound_enabled = !this.sound_enabled;
    if (!this.sound_enabled) {
      this.stopAll();
    }
    return this.sound_enabled;
  }

  stopAll() {
    if (this.audioHha) {
      this.audioHha.pause();
      this.audioHha.currentTime = 0;
    }
    if (this.audioRollback) {
      this.audioRollback.pause();
      this.audioRollback.currentTime = 0;
    }

    if (this.activeOsc) {
      try {
        this.activeOsc.stop();
        this.activeOsc.disconnect();
      } catch (e) {}
      this.activeOsc = null;
    }
    if (this.activeGain) {
      try {
        this.activeGain.disconnect();
      } catch (e) {}
      this.activeGain = null;
    }

    this.current_state = "IDLE";
  }

  _playSynth(type) {
    this._ensureWebAudio();
    if (!this.audioContext) return;

    this.stopAll();
    const ctx = this.audioContext;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (type === "HHA") {
      // 680 Hz Continuous Electronic Warning Tone
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(680, ctx.currentTime);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
    } else if (type === "ROLLBACK") {
      // Urgent Pulsed Dual-Tone (1150 / 1450 Hz)
      osc.type = "square";
      osc.frequency.setValueAtTime(1150, ctx.currentTime);
      
      const now = ctx.currentTime;
      for (let i = 0; i < 40; i++) {
        const t = now + i * 0.12;
        osc.frequency.setValueAtTime(1450, t);
        osc.frequency.setValueAtTime(1150, t + 0.06);
      }
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
    }

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();

    this.activeOsc = osc;
    this.activeGain = gain;
  }

  update(hhaIsActive, rollbackRiskActive) {
    if (!this.sound_enabled) {
      if (this.current_state !== "IDLE") {
        this.stopAll();
      }
      return;
    }

    let target_state = "IDLE";
    if (hhaIsActive) {
      target_state = "HHA";
    } else if (rollbackRiskActive) {
      target_state = "ROLLBACK";
    }

    if (target_state === this.current_state) return;

    this.stopAll();

    if (target_state === "HHA") {
      if (this.audioHha && !this.useSynth) {
        this.audioHha.play().catch(() => this._playSynth("HHA"));
      } else {
        this._playSynth("HHA");
      }
      this.current_state = "HHA";
    } else if (target_state === "ROLLBACK") {
      if (this.audioRollback && !this.useSynth) {
        this.audioRollback.play().catch(() => this._playSynth("ROLLBACK"));
      } else {
        this._playSynth("ROLLBACK");
      }
      this.current_state = "ROLLBACK";
    }
  }
}

// ==========================================
// 7. HUD & ON-CANVAS CONTROLS RENDERING
// ==========================================
function drawHUD(ctx, car, road, hha) {
  // Top-left dashboard card
  const panel_x = 20;
  const panel_y = 20;
  const panel_w = 310;
  const panel_h = 155;

  ctx.save();
  // Translucent card background
  ctx.fillStyle = "rgba(255, 255, 255, 0.96)";
  drawRoundedRect(ctx, panel_x, panel_y, panel_w, panel_h, 10);
  ctx.fill();

  ctx.strokeStyle = "rgb(215, 220, 230)";
  ctx.lineWidth = 1;
  ctx.stroke();

  // 1. Speed (large and prominent)
  const speed_kmh = car.getSpeedKmh();
  ctx.fillStyle = COLOR_TEXT_MAIN;
  ctx.font = "bold 26px 'Segoe UI', -apple-system, sans-serif";
  ctx.fillText(`${speed_kmh.toFixed(1)} km/h`, panel_x + 18, panel_y + 36);

  // 2. Slope angle
  const slope = road.slope_angle;
  let slope_str, slope_color;
  if (slope > 0.05) {
    slope_str = `Slope: +${slope.toFixed(1)}° (Uphill)`;
    slope_color = "rgb(190, 50, 30)";
  } else if (slope < -0.05) {
    slope_str = `Slope: ${slope.toFixed(1)}° (Downhill)`;
    slope_color = "rgb(30, 95, 180)";
  } else {
    slope_str = "Slope: 0.0° (Flat)";
    slope_color = COLOR_TEXT_MUTED;
  }

  ctx.fillStyle = slope_color;
  ctx.font = "15px 'Segoe UI', -apple-system, sans-serif";
  ctx.fillText(slope_str, panel_x + 18, panel_y + 68);

  // 3. Road Surface Type
  const surf_props = road.getSurfaceProps();
  ctx.fillStyle = COLOR_TEXT_MAIN;
  ctx.font = "15px 'Segoe UI', -apple-system, sans-serif";
  ctx.fillText(`Road: ${surf_props.name}`, panel_x + 18, panel_y + 92);

  // 4. Hill Hold Status Badge
  const hha_status = hha.getStatusText();
  let badge_text, bg_col, border_col, text_col;

  if (hha_status === "HILL HOLD: ACTIVE") {
    badge_text = `HILL HOLD: ACTIVE (${hha.hold_timer.toFixed(1)}s)`;
    bg_col = "rgb(255, 242, 225)";
    border_col = "rgb(230, 125, 15)";
    text_col = "rgb(210, 110, 10)";
  } else if (hha_status === "HILL HOLD: ON") {
    badge_text = "HILL HOLD: ON";
    bg_col = "rgb(235, 250, 235)";
    border_col = "rgb(45, 160, 55)";
    text_col = "rgb(35, 140, 45)";
  } else {
    badge_text = "HILL HOLD: OFF";
    bg_col = "rgb(242, 244, 248)";
    border_col = "rgb(180, 185, 195)";
    text_col = "rgb(120, 125, 135)";
  }

  const badge_x = panel_x + 16;
  const badge_y = panel_y + 106;
  const badge_w = panel_w - 32;
  const badge_h = 36;

  ctx.fillStyle = bg_col;
  drawRoundedRect(ctx, badge_x, badge_y, badge_w, badge_h, 6);
  ctx.fill();

  ctx.strokeStyle = border_col;
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = text_col;
  ctx.font = "bold 15px 'Segoe UI', -apple-system, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(badge_text, badge_x + badge_w / 2, badge_y + badge_h / 2);

  ctx.restore();
}

function drawControlsCorner(ctx) {
  // Bottom-right shortcut card
  const width = 250;
  const height = 95;
  const x = SCREEN_WIDTH - width - 18;
  const y = SCREEN_HEIGHT - height - 16;

  ctx.save();
  ctx.fillStyle = "rgba(20, 24, 32, 0.86)";
  drawRoundedRect(ctx, x, y, width, height, 8);
  ctx.fill();

  ctx.strokeStyle = "rgba(80, 85, 100, 0.71)";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Header
  ctx.fillStyle = "rgb(190, 200, 215)";
  ctx.font = "bold 11px 'Segoe UI', -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText("CONTROLS", x + 12, y + 8);

  // Key instructions
  ctx.fillStyle = "rgb(230, 235, 245)";
  ctx.font = "11px Consolas, monospace";

  const lines = [
    "[A] Gas        [B] Brake",
    "[H] Hill Hold  [M] Sound",
    "[1-4] Surface  [LEFT/RIGHT] Slope",
    "[R] Reset      [ESC] Exit",
  ];

  let curr_y = y + 26;
  for (const line of lines) {
    ctx.fillText(line, x + 12, curr_y);
    curr_y += 15;
  }

  ctx.restore();
}

// ==========================================
// 8. APPLICATION MAIN CONTROLLER
// ==========================================
class SimulatorApp {
  constructor() {
    this.canvas = document.getElementById("simCanvas");
    this.ctx = this.canvas.getContext("2d");

    this.road = new Road();
    this.car = new Car();
    this.physics = new PhysicsEngine();
    this.hha = new HillHoldAssist();
    this.buzzer = new BuzzerManager();

    this.inputAccelerate = false;
    this.inputBrake = false;
    this.keyLeftHeld = false;
    this.keyRightHeld = false;
    this.holdTimer = 0.0;
    this.repeatDelay = 0.25;
    this.repeatInterval = 0.06;

    this.maxVisualDist = 220.0;
    this.lastTimestamp = performance.now();

    this._bindEvents();
    this._bindDOMButtons();
    this._startLoop();
  }

  _bindEvents() {
    window.addEventListener("keydown", (e) => {
      this.buzzer._ensureWebAudio();

      if (e.key === "a" || e.key === "A") {
        this.inputAccelerate = true;
        this._updatePedalUI("gas", true);
      }
      if (e.key === "b" || e.key === "B") {
        this.inputBrake = true;
        this._updatePedalUI("brake", true);
      }
      if (e.key === "h" || e.key === "H") {
        this.hha.toggle();
        this._updateToggleButtonUI();
      }
      if (e.key === "m" || e.key === "M") {
        this.buzzer.toggleSound();
        this._updateSoundButtonUI();
      }
      if (e.key === "r" || e.key === "R") {
        this.reset();
      }
      if (e.key === "1") this.road.setSurface("DRY");
      if (e.key === "2") this.road.setSurface("WET");
      if (e.key === "3") this.road.setSurface("ICE");
      if (e.key === "4") this.road.setSurface("GRAVEL");

      if (e.key === "ArrowLeft") {
        this.road.adjustSlope(-1.0);
        this.keyLeftHeld = true;
      }
      if (e.key === "ArrowRight") {
        this.road.adjustSlope(1.0);
        this.keyRightHeld = true;
      }

      this._updateSurfaceButtonsUI();
    });

    window.addEventListener("keyup", (e) => {
      if (e.key === "a" || e.key === "A") {
        this.inputAccelerate = false;
        this._updatePedalUI("gas", false);
      }
      if (e.key === "b" || e.key === "B") {
        this.inputBrake = false;
        this._updatePedalUI("brake", false);
      }
      if (e.key === "ArrowLeft") this.keyLeftHeld = false;
      if (e.key === "ArrowRight") this.keyRightHeld = false;
    });

    // Handle audio unlock on first user gesture
    document.addEventListener("click", () => this.buzzer._ensureWebAudio(), { once: true });
    document.addEventListener("touchstart", () => this.buzzer._ensureWebAudio(), { once: true });
  }

  _bindDOMButtons() {
    // Gas Pedal (Hold)
    const btnGas = document.getElementById("btnGas");
    if (btnGas) {
      const startGas = (e) => {
        e.preventDefault();
        this.buzzer._ensureWebAudio();
        this.inputAccelerate = true;
        this._updatePedalUI("gas", true);
      };
      const endGas = (e) => {
        e.preventDefault();
        this.inputAccelerate = false;
        this._updatePedalUI("gas", false);
      };
      btnGas.addEventListener("pointerdown", startGas);
      btnGas.addEventListener("pointerup", endGas);
      btnGas.addEventListener("pointercancel", endGas);
      btnGas.addEventListener("pointerleave", endGas);
    }

    // Brake Pedal (Hold)
    const btnBrake = document.getElementById("btnBrake");
    if (btnBrake) {
      const startBrake = (e) => {
        e.preventDefault();
        this.buzzer._ensureWebAudio();
        this.inputBrake = true;
        this._updatePedalUI("brake", true);
      };
      const endBrake = (e) => {
        e.preventDefault();
        this.inputBrake = false;
        this._updatePedalUI("brake", false);
      };
      btnBrake.addEventListener("pointerdown", startBrake);
      btnBrake.addEventListener("pointerup", endBrake);
      btnBrake.addEventListener("pointercancel", endBrake);
      btnBrake.addEventListener("pointerleave", endBrake);
    }

    // Slope Adjustment Buttons
    document.getElementById("btnSlopeDown")?.addEventListener("click", () => {
      this.road.adjustSlope(-1.0);
    });
    document.getElementById("btnSlopeUp")?.addEventListener("click", () => {
      this.road.adjustSlope(1.0);
    });

    // Slope Presets
    document.getElementById("presetFlat")?.addEventListener("click", () => {
      this.road.slope_angle = 0.0;
    });
    document.getElementById("presetUphill")?.addEventListener("click", () => {
      this.road.slope_angle = 12.0;
    });
    document.getElementById("presetDownhill")?.addEventListener("click", () => {
      this.road.slope_angle = -10.0;
    });

    // Surface Selection
    ["DRY", "WET", "ICE", "GRAVEL"].forEach((key) => {
      const btn = document.getElementById(`btnSurf_${key}`);
      btn?.addEventListener("click", () => {
        this.road.setSurface(key);
        this._updateSurfaceButtonsUI();
      });
    });

    // Toggle HHA
    document.getElementById("btnToggleHHA")?.addEventListener("click", () => {
      this.hha.toggle();
      this._updateToggleButtonUI();
    });

    // Toggle Sound
    document.getElementById("btnToggleSound")?.addEventListener("click", () => {
      this.buzzer.toggleSound();
      this._updateSoundButtonUI();
    });

    // Reset
    document.getElementById("btnReset")?.addEventListener("click", () => {
      this.reset();
    });

    this._updateSurfaceButtonsUI();
    this._updateToggleButtonUI();
    this._updateSoundButtonUI();
  }

  _updatePedalUI(pedal, active) {
    const el = document.getElementById(pedal === "gas" ? "btnGas" : "btnBrake");
    if (el) {
      if (active) el.classList.add("active-pressed");
      else el.classList.remove("active-pressed");
    }
  }

  _updateSurfaceButtonsUI() {
    ["DRY", "WET", "ICE", "GRAVEL"].forEach((key) => {
      const btn = document.getElementById(`btnSurf_${key}`);
      if (btn) {
        if (this.road.surface_key === key) btn.classList.add("active");
        else btn.classList.remove("active");
      }
    });
  }

  _updateToggleButtonUI() {
    const btn = document.getElementById("btnToggleHHA");
    if (btn) {
      btn.textContent = this.hha.enabled ? "Hill Hold: ON" : "Hill Hold: OFF";
      btn.className = `btn btn-toggle ${this.hha.enabled ? "active" : "inactive"}`;
    }
  }

  _updateSoundButtonUI() {
    const btn = document.getElementById("btnToggleSound");
    if (btn) {
      btn.textContent = this.buzzer.sound_enabled ? "Sound: ON" : "Sound: OFF";
      btn.className = `btn btn-toggle ${this.buzzer.sound_enabled ? "active" : "inactive"}`;
    }
  }

  reset() {
    this.car.reset();
    this.hha.reset();
    this.buzzer.stopAll();
  }

  _startLoop() {
    const frame = (timestamp) => {
      const dtMs = timestamp - this.lastTimestamp;
      this.lastTimestamp = timestamp;

      // Delta time in seconds, clamped to 0.05 max
      let dt = dtMs / 1000.0;
      if (dt > 0.05) dt = 0.05;
      if (dt <= 0.0) dt = 1.0 / 60.0;

      this._update(dt);
      this._render();
      this._updateTelemetryUI();

      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  _update(dt) {
    // Continuous slope holding
    if (this.keyLeftHeld || this.keyRightHeld) {
      this.holdTimer += dt;
      if (this.holdTimer > this.repeatDelay) {
        const dir = this.keyLeftHeld ? -1.0 : 1.0;
        this.road.adjustSlope(dir * (dt / this.repeatInterval));
      }
    } else {
      this.holdTimer = 0.0;
    }

    // 1. Update Hill Hold Assist
    const hhaActive = this.hha.update(
      dt,
      this.car.velocity,
      this.road.slope_angle,
      this.inputBrake,
      this.inputAccelerate
    );

    // 2. Update Vehicle Physics
    const surfProps = this.road.getSurfaceProps();
    this.car.update(
      this.inputAccelerate,
      this.inputBrake,
      this.road.slope_angle,
      dt,
      this.physics,
      hhaActive,
      surfProps.grip_coeff,
      surfProps.rolling_res_coeff
    );

    // 3. Rollback risk detection for warning buzzer
    const rollbackRisk =
      Math.abs(this.road.slope_angle) >= 0.5 &&
      !hhaActive &&
      !this.inputBrake &&
      !this.inputAccelerate &&
      ((this.road.slope_angle > 0 && this.car.velocity < -0.12) ||
        (this.road.slope_angle < 0 && this.car.velocity > 0.12));

    this.buzzer.update(hhaActive, rollbackRisk);
  }

  _render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    // Camera offset along road
    const car_dist_px = this.car.world_distance_m * PIXELS_PER_METER;
    let camera_offset = 0.0;
    let screen_dist = car_dist_px;

    if (car_dist_px > this.maxVisualDist) {
      camera_offset = car_dist_px - this.maxVisualDist;
      screen_dist = this.maxVisualDist;
    } else if (car_dist_px < -this.maxVisualDist) {
      camera_offset = car_dist_px - -this.maxVisualDist;
      screen_dist = -this.maxVisualDist;
    }

    // Draw scene
    this.road.draw(ctx, camera_offset);
    this.car.draw(ctx, this.road, screen_dist, this.inputBrake);

    // HUD & Controls
    drawHUD(ctx, this.car, this.road, this.hha);
    drawControlsCorner(ctx);
  }

  _updateTelemetryUI() {
    const setElem = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setElem("telemSpeed", `${this.car.getSpeedKmh().toFixed(1)} km/h`);
    setElem("telemSlope", `${this.road.slope_angle.toFixed(1)}°`);
    setElem("telemGravity", `${this.car.f_gravity.toFixed(0)} N`);
    setElem("telemNetForce", `${this.car.f_net.toFixed(0)} N`);
    setElem("telemTraction", `${this.car.f_traction_max.toFixed(0)} N`);
    setElem("telemHHA", this.hha.getStatusText());
  }
}

// Boot application when DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  window.app = new SimulatorApp();
});
