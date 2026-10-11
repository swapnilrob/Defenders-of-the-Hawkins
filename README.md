<p align="center">
  <img src="https://img.shields.io/badge/Python-OpenGL-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/OpenGL-3D_Rendering-5586A4?style=for-the-badge&logo=opengl&logoColor=white" alt="OpenGL" />
  <img src="https://img.shields.io/badge/GLUT-Windowing-FF6F00?style=for-the-badge" alt="GLUT" />
  <img src="https://img.shields.io/badge/Theme-Stranger_Things-D00000?style=for-the-badge" alt="Stranger Things" />
  <img src="https://img.shields.io/badge/Lines-1%2C145-yellow?style=for-the-badge" alt="1145 Lines" />
  <img src="https://img.shields.io/badge/License-Academic-lightgrey?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🔥 Defenders of the Hawkins</h1>

<p align="center">
  <strong>Protect Hawkins from the Upside Down. Choose your hero. Survive four levels. Save the world.</strong>
</p>

<p align="center">
  A <strong>Stranger Things</strong>-themed 3D arena shooter built from scratch with <strong>Python + OpenGL/GLUT</strong>. Choose from 5 playable characters — each with unique shooting speeds — and fight through 4 escalating levels of enemies: <strong>Demogorgons → Bats → Vecna → The Mind Flayer's Mixed Army</strong>. Features dual camera modes (Third-Person / First-Person), a cheat mode where <strong>Eleven</strong> fights alongside you with AI-controlled targeting, dynamic danger lighting, and a bonus life system for perfect clears.
</p>

---

## 📌 Why This Project?

Computer graphics courses teach transformation matrices and projection theory. This project applies those concepts to build something playable — a complete 3D game loop rendered in immediate-mode OpenGL, with no game engine, no sprite library, and no external assets. Every polygon is drawn from code.

The game demonstrates:

- **3D rendering pipeline** — perspective projection, model-view transformations, depth buffering
- **Dual camera systems** — Third-Person (orbit camera) and First-Person (gun-aligned) viewpoints
- **Orthographic HUD overlay** — score, health, and controls rendered as a 2D layer on top of the 3D scene
- **Real-time game loop** — GLUT idle callback driving continuous update → render cycles
- **AI companion behavior** — Eleven auto-targets the nearest enemy within detection range
- **State machine architecture** — menu → character select → playing → level complete → game over

---

## 🎮 Game Features

| Feature | Details |
|---------|---------|
| **5 Playable Characters** | Will (1.1x), Mike (1.0x), Dustin (1.3x), Max (1.4x), Steve (1.2x) — strength = shooting speed multiplier |
| **4 Levels** | Level 1: Demogorgons (12 enemies) → Level 2: Bats (15 enemies) → Level 3: Vecna (boss, 10 HP, shoots back) → Level 4: Mixed army (Vecna + Demogorgons + Bats) |
| **TPS / FPS Toggle** | Right-click or press F to switch between Third-Person and First-Person camera |
| **Cheat Mode (Eleven)** | Press C — Eleven appears beside you with AI auto-targeting and auto-fire, background shifts to safe blue |
| **Danger Lighting** | Background turns red when lives drop to 1; grid flashes red as warning |
| **Bonus Lives** | Clear a level without losing a life → +1 bonus life |
| **Vecna Boss Fight** | Vecna maintains distance (avoids collision), fires projectiles at the player, requires 10 hits to kill |
| **Boundary Walls** | 2400×2400 arena with visible walls — player and enemies are clamped inside |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         GAME STATE MACHINE                       │
│                                                                  │
│   ┌────────┐    SPACE    ┌──────────┐    all enemies   ┌──────┐ │
│   │  MENU  │───────────▶│ PLAYING  │──────────────────▶│LEVEL │ │
│   │        │◀───ESC──────│          │                   │CLEAR │ │
│   └────┬───┘             └────┬─────┘                   └──┬───┘ │
│        │ C                    │ lives=0                    │SPACE│
│   ┌────▼──────────┐     ┌────▼──────┐                     │     │
│   │  CHARACTER    │     │ GAME OVER │         next level◀──┘     │
│   │  SELECT      │     │           │                             │
│   └───────────────┘     └───────────┘                            │
├──────────────────────────────────────────────────────────────────┤
│                        RENDER PIPELINE                           │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │ Clear +     │──▶│ Setup Camera │──▶│ Draw 3D Scene        │  │
│  │ Background  │   │ (TPS or FPS) │   │ Grid + Walls         │  │
│  │ (dynamic)   │   │ gluLookAt    │   │ Player / FPS Gun     │  │
│  └─────────────┘   └──────────────┘   │ Eleven (if cheat)    │  │
│                                        │ Bullets + Enemies    │  │
│                                        └─────────┬────────────┘  │
│                                                   │              │
│                                        ┌──────────▼────────────┐ │
│                                        │ Draw HUD (Ortho 2D)  │ │
│                                        │ Score, Lives, Level   │ │
│                                        │ Controls, Camera Mode │ │
│                                        └───────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│                         UPDATE LOOP                              │
│                                                                  │
│  idle() → update():                                              │
│    ├── Process held keys (dt-based movement/rotation)            │
│    ├── Update bullet positions (player + Vecna projectiles)      │
│    ├── Spawn enemies on timer (per level_config spawn_rate)      │
│    ├── Update enemy AI (chase player / maintain distance)        │
│    ├── Update Eleven AI (auto-target + auto-fire if cheat)       │
│    ├── Check collisions (bullets↔enemies, enemies↔player)        │
│    └── Check level completion (all spawned + all dead)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Deep Dive

### Camera System

Two camera modes, both using `gluLookAt`:

**Third-Person (TPS)** — Orbit camera that follows the player:
```
cam_x = player_x - cos(player_rotation + camera_angle) × distance
cam_y = player_y - sin(player_rotation + camera_angle) × distance
cam_z = player_z + camera_height

Look at: player position + 30 units up (chest height)
```
Arrow keys rotate the orbit angle and adjust height.

**First-Person (FPS)** — Camera at player eye level, looking along gun direction:
```
Eye:    player position + 55 units up (head height)
Target: eye + cos/sin(player_rotation + gun_rotation) × 120 units forward
```
Arrow Left/Right rotate the gun independently of body rotation. A separate `draw_first_person_gun()` renders the weapon model in view space.

### Enemy AI

| Enemy | Behavior | Attack |
|-------|----------|--------|
| **Demogorgon** | Chases player directly, approach speed calculated from `spawn_distance / (approach_time × 60)` | Contact damage on collision |
| **Bats** | Faster chase (0.5 base speed), spawns in larger waves (15 total) | Contact damage on collision |
| **Vecna** | Maintains ~220-unit distance from player (`avoids_collision = True`), retreats if too close, advances if too far | Fires projectiles at player (`fire_rate: 100` frames) |
| **Level 4 Mixed** | 1 Vecna (2 HP) + 3 Demogorgons + 3 Bats simultaneously | Combined melee + ranged |

### Eleven AI (Cheat Mode)

When activated (press C), Eleven spawns as an AI companion:

1. **Positioning** — Follows player at a 60-unit offset, 90° to the right of player's facing direction
2. **Target acquisition** — Scans all active enemies within `eleven_detection_range` (250 units), picks the closest
3. **Auto-aim** — Calculates `atan2` angle to target, sets `eleven_rotation` and fires
4. **Fire rate** — Fires every `eleven_fire_rate` (200) frames, bullets deal 15 × level bonus (vs 10 for player)

### 3D Object Construction

All game objects are built from OpenGL primitives — no external models or textures:

| Object | Primitives Used |
|--------|----------------|
| **Player body** | `gluCylinder` (legs, arms, gun barrel) + `glutSolidCube` (torso) + `gluSphere` (head, muzzle) |
| **Demogorgon** | 10-point star via `GL_TRIANGLES` fan — alternating outer/inner radii |
| **Bats** | 3 triangles forming wing silhouette (center + left + right) |
| **Vecna** | Y-shaped figure from 3 `glutSolidCube` blocks (body + 2 arms at ±45°) |
| **Bullets** | `gluSphere` — yellow (player), pink (Eleven), red (Vecna) |
| **Arena** | `GL_QUADS` — 8×8 checkerboard floor (Phthalo Green + off-white) + 4 boundary walls |
| **Health bars** | `GL_QUADS` — red background + green fill proportional to remaining HP |

### Dual-State Lighting

Background color dynamically reflects game state:

```python
def compute_background_color():
    if cheat_mode_active:
        return (0.067, 0.067, 0.314)    # Safe blue (Eleven's protection)
    if lives <= 1:
        return (0.50, 0.10, 0.10)       # Danger red (critical health)
    return (0.05, 0.05, 0.10)           # Normal dark
```

Additionally, the floor grid flashes red when lives drop below 2, using a `grid_flash_timer` that alternates between red and normal colors every 10 frames for 100 frames total.

### Input System

The game uses a **tap-vs-hold** detection system for movement:

- **Tap A** → Instant 90° left turn | **Hold A** → Smooth continuous rotation (120°/sec)
- **Tap S** → Instant 180° turn | **Hold S** → Smooth backward movement
- **Hold W** → Smooth forward movement (180 units/sec)
- **Hold D** → Smooth continuous right rotation

Detection works by recording `KEY_DOWN_TIME` on press and comparing elapsed time against `HOLD_MOVE_THRESHOLD` (0.18s) — below threshold is a tap, above is a hold. Delta-time (`dt`) based movement ensures consistent speed regardless of frame rate.

---

## 🎯 Level Progression

| Level | Enemy | Count | HP | Speed | Special | Spawn Rate |
|-------|-------|-------|----|-------|---------|------------|
| 1 | Demogorgon | 12 | 1 | Slow (approach over 15s) | Contact damage | Every 240 frames |
| 2 | Bats | 15 | 1 | Medium (0.5) | Contact damage | Every 150 frames |
| 3 | Vecna | 1 | 10 | Fast (0.75) | Ranged attacks, maintains distance | Every 90 frames |
| 4 | Mixed | 7 | Varies | Varies | Vecna (2 HP) + Demogorgons + Bats | Every 100 frames |

**Scoring:** 10 points × current level per kill (15 × level for Eleven's kills)

**Bonus life:** Clear any level with 3+ lives remaining → +1 life

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.7+**
- **PyOpenGL** and **PyOpenGL-accelerate**

### 1. Clone the Repository

```bash
git clone https://github.com/swapnilrob/Defenders-of-the-Hawkins.git
cd Defenders-of-the-Hawkins
```

### 2. Install Dependencies

```bash
pip install PyOpenGL PyOpenGL-accelerate
```

> **Note:** On some systems you may also need GLUT libraries. On Ubuntu/Debian: `sudo apt install freeglut3-dev`. On macOS, GLUT is included with the system.

### 3. Run the Game

```bash
python "Final copy.py"
```

### 4. Controls

| Key | Action |
|-----|--------|
| `W` / `S` | Move forward / backward (hold) |
| `A` / `D` | Rotate left / right (tap = 90°, hold = smooth) |
| `Space` / `Left Click` | Fire |
| `Right Click` / `F` | Toggle TPS ↔ FPS camera |
| `C` | Toggle Cheat Mode (Eleven) |
| `Arrow Up/Down` | Adjust camera height (TPS) |
| `Arrow Left/Right` | Rotate camera orbit (TPS) / Aim gun (FPS) |
| `R` | Reset game |
| `ESC` | Return to menu |
| `1-5` | Select character (in character select screen) |

---

## 📁 Project Structure

```
Defenders-of-the-Hawkins/
├── Final copy.py       # Complete game — rendering, logic, AI, input (1,145 lines)
└── README.md           # This file
```

---

## 👥 Team

| Name | Contributions |
|------|---------------|
| Swapnil Rob (22299138) | Camera system — TPS orbit camera with angle/height controls and FPS gun-aligned camera with independent gun rotation; input system — tap-vs-hold detection using `KEY_DOWN_TIME` + threshold for dual-mode A/D controls, delta-time based movement; first-person gun rendering with world-space barrel positioning; game state machine (menu → character select → playing → level complete → game over) |
| Nafisa Hasan (22299141) | Enemy AI — chase behavior for Demogorgons/Bats, distance-maintaining AI for Vecna with ranged attack system; Eleven AI companion — auto-target acquisition within detection range, `atan2`-based aiming, auto-fire with cooldown; collision detection (bullet↔enemy, enemy↔player, Vecna projectile↔player); level progression and spawn system with `level_config` dictionary |
| Mehrab | 3D object construction — player model from OpenGL primitives (cylinders, cubes, spheres), Demogorgon star shape via triangle fan, bat wing silhouette, Vecna Y-figure from rotated cubes; arena rendering — 8×8 checkerboard floor with boundary walls; HUD overlay using orthographic projection switch; dynamic background color system (safe blue / danger red / normal dark) |

---

## 📄 Course Context

Developed for **CSE 423 — Computer Graphics** at **BRAC University** (Fall 2025). The project demonstrates practical application of OpenGL rendering concepts including perspective and orthographic projection, model-view transformations (`glTranslate`, `glRotate`, `glScale`), GLUT primitive rendering (`glutSolidCube`, `gluCylinder`, `gluSphere`), double-buffered animation with idle callbacks, depth testing, and real-time 3D camera control.

---

## 🧠 What We Learned

- **Immediate-mode OpenGL is verbose but transparent** — drawing every polygon manually (no VBOs, no shaders) makes the transformation pipeline fully visible: every `glPushMatrix` / `glPopMatrix` / `glTranslatef` / `glRotatef` corresponds directly to a matrix multiplication in the graphics pipeline
- **Camera math is the hardest part of 3D** — getting TPS orbit and FPS gun-aligned cameras both working required careful separation of player rotation, camera orbit angle, and gun rotation as three independent degrees of freedom
- **Orthographic overlay on perspective 3D** — the HUD switches to `gluOrtho2D` mid-frame, draws text, then restores the perspective matrix; this dual-projection technique is how real games render UI on top of 3D scenes
- **Delta-time movement prevents frame-rate dependency** — using `time.time()` deltas instead of fixed-step movement means the game plays at consistent speed regardless of rendering performance
- **AI doesn't need to be complex to be effective** — Eleven's targeting is just "find closest enemy within range, compute `atan2`, fire" — simple geometry that produces convincing companion behavior
