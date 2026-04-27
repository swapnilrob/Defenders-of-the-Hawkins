# ==========================================================
# Defenders of the Hawkins 

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time

# ==================== GAME STATE VARIABLES ====================
# Character selection
characters = ["Will", "Mike", "Dustin", "Max", "Steve"]
character_strengths = {"Will": 1.1, "Mike": 1.0, "Dustin": 1.3, "Max": 1.4, "Steve": 1.2}
selected_character = "Mike"
character_strength = character_strengths[selected_character]

# Game state
game_state = "menu"  
current_level = 1
score = 0
lives = 50
previous_lives = 50
bonus_lives_earned = 0

# Camera variables (TPV/FPS)
camera_mode = "TPS"   # TPS or FPS
camera_height = 320.0
camera_distance = 400.0
camera_angle = 0

fovY = 90
GRID_LENGTH = 1200 
GRID_TILES = 8
WALL_HEIGHT = 200.0
# Player variables (2D movement on XY plane, Z is height)
player_pos = [0.0, 0.0, 0.0]
player_rotation = 0.0   
gun_rotation = 0.0

# Mouse
mouse_last_x = None
mouse_last_y = None

# Eleven aiming (update hoise update_eleven)
eleven_rotation = 0.0
eleven_gun_rotation = 0.0
player_speed = 12.0
rotation_speed = 6.0

# A/D press vs hold 
last_a_time = 0.0
last_d_time = 0.0
hold_threshold = 0.18  # holding

# Keyboard hold/tap handling 
KEY_HELD = {}          # key -> bool
KEY_DOWN_TIME = {}     # key -> time.time() when pressed
HOLD_MOVE_THRESHOLD = 0.18  
MOVE_SPEED_PER_SEC = 180.0  
ROTATE_SPEED_PER_SEC = 120.0  # degrees per second when holding A/D
_last_move_time = time.time()

# Bullet variables
bullets = []
vecna_bullets = []
bullet_speed = 18.0
fire_cooldown = 0
max_fire_cooldown = 10

# Enemies
enemies = []
enemy_spawn_timer = 0
enemies_spawned_this_level = 0

# Cheat mode
cheat_mode_active = False
eleven_pos = [0.0, 0.0, 0.0]
eleven_fire_cooldown = 0
eleven_fire_rate = 200
eleven_detection_range = 250

# Grid flash variables
grid_flash_timer = 0
grid_flash_active = False
grid_color_normal = (0.3, 0.3, 0.4)
grid_color_red = (0.8, 0.2, 0.2)

# ==================== Enemy Shape Helpers ====================
def draw_star_2d_xy(cx=0.0, cy=0.0, outer_r=22.0, inner_r=9.0):
    points = []
    for i in range(10):
        ang = i * math.pi / 5.0
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))

    glBegin(GL_TRIANGLES)
    for i in range(10):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % 10]
        glVertex3f(cx, cy, 0.0)
        glVertex3f(x1, y1, 0.0)
        glVertex3f(x2, y2, 0.0)
    glEnd()

def draw_bat_triangles_2d_xy(scale=55.0):
    L = 0.3 * scale
    h = (math.sqrt(3.0) / 2.0) * L

    glBegin(GL_TRIANGLES)

    # Middle triangle 
    glVertex3f(0.0,  h, 0.0)
    glVertex3f(-L/2.0, 0.0, 0.0)
    glVertex3f( L/2.0, 0.0, 0.0)

    # Left triangle 
    glVertex3f(-L/2.0, 0.0, 0.0)
    glVertex3f(-L,0.0, 0.0)
    glVertex3f(-0.75*L, -h, 0.0)

    # Right triangle 
    glVertex3f( L/2.0, 0.0, 0.0)
    glVertex3f( L,0.0, 0.0)
    glVertex3f(0.75*L, -h, 0.0)

    glEnd()

# ==================== LEVEL CONFIG ====================
level_config = {
    1: {"type": "Demogorgon", "total_enemies": 12, "max_concurrent": 2, "health": 1,
        "base_speed": 0.1, "color": (0.5, 0.3, 0.2), "spawn_distance": 600, "approach_time": 15,
        "has_gun": False, "spawn_rate": 240},
    2: {"type": "Bats", "total_enemies": 15, "max_concurrent": 2, "health": 1,
        "base_speed": 0.5, "color": (0, 0, 0.5), "spawn_distance": 520, "approach_time": 12,
        "has_gun": False, "spawn_rate": 150},
    3: {"type": "Vecna", "total_enemies": 1, "max_concurrent": 1, "health": 10,
        "base_speed": 0.75, "color": (0.796, 0.255, 0.329), "spawn_distance": 520, "approach_time": 0,
        "has_gun": True, "spawn_rate": 90, "fire_rate": 100},
    4: {"type": "Mixed", "total_enemies": 10, "max_concurrent": 2, "spawn_distance": 520, "spawn_rate": 100}
}

# ========================================
def clamp_to_grid(x, y): #Can't go outside of the wall
    pad = 40
    mx = GRID_LENGTH - pad
    mn = -GRID_LENGTH + pad
    x = max(mn, min(mx, x))
    y = max(mn, min(mx, y))
    return x, y

def draw_vecna_Y_3d(scale=1.0):
    glPushMatrix()
    glScalef(scale, scale, scale)
    glColor3f(0.796, 0.255, 0.329)

    # Vertical
    glPushMatrix()
    glTranslatef(0, 0, 18)
    glScalef(10, 10, 36)
    glutSolidCube(1)
    glPopMatrix()

    # Left arm
    glPushMatrix()
    glTranslatef(-10, 0, 44)
    glRotatef(45, 0, 0, 1)   # rotate in XY plane
    glScalef(8, 8, 26)
    glutSolidCube(1)
    glPopMatrix()

    # Right arm
    glPushMatrix()
    glTranslatef(10, 0, 44)
    glRotatef(-45, 0, 0, 1)
    glScalef(8, 8, 26)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):  # text 
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ==================== GAME OBJECTS ====================
class Bullet:
    def __init__(self, x, y, z, angle, speed, is_eleven=False, is_vecna=False):
        self.x, self.y, self.z = x, y, z
        self.angle = angle
        self.speed = speed
        self.active = True
        self.is_eleven = is_eleven
        self.is_vecna = is_vecna

    def update(self): # Z height, so nai
        self.x += math.cos(math.radians(self.angle)) * self.speed
        self.y += math.sin(math.radians(self.angle)) * self.speed

        if abs(self.x) > GRID_LENGTH or abs(self.y) > GRID_LENGTH:
            self.active = False

    def draw(self):
        glPushMatrix()
        if self.is_eleven:
            glColor3f(1.0, 0.4, 0.8)
        elif self.is_vecna:
            glColor3f(0.8, 0.1, 0.1)
        else:
            glColor3f(1.0, 1.0, 0.0)

        glTranslatef(self.x, self.y, self.z)       
        gluSphere(gluNewQuadric(), 6, 10, 10)
        glPopMatrix()

class Enemy:
    def __init__(self, x, y, enemy_type, level):
        self.x, self.y = x, y
        self.z = 30
        self.type = enemy_type
        self.level = level
        self.active = True
        self.hit_cooldown = 0

        if level == 4:
            if enemy_type == "Vecna":
                self.health = 2
                self.color = (0.796, 0.255, 0.329)
                self.speed = 0.75
                self.has_gun = True
                self.fire_cooldown = 0
                self.fire_rate = 100
                self.avoids_collision = True
            elif enemy_type == "Demogorgon":
                self.health = 1
                self.color = (0.5, 0.3, 0.2)
                self.speed = 0.1
                self.has_gun = False
                self.avoids_collision = False
            else:
                self.health = 1
                self.color = (0.2, 0.2, 0.2)
                self.speed = 0.5
                self.has_gun = False
                self.avoids_collision = False
        else:
            cfg = level_config[level]
            self.health = cfg["health"]
            self.color = cfg["color"]
            self.speed = cfg["base_speed"]
            self.has_gun = cfg.get("has_gun", False)
            self.avoids_collision = (level == 3)
            if self.has_gun:
                self.fire_cooldown = 0
                self.fire_rate = cfg.get("fire_rate", 120)

    def update(self, px, py):
        dx = px - self.x
        dy = py - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if self.avoids_collision:
            target = 220
            if dist > target + 60 and dist > 0:
                nx = self.x + (dx/dist)*self.speed
                ny = self.y + (dy/dist)*self.speed
                self.x, self.y = clamp_to_grid(nx, ny)
            elif dist < target - 60 and dist > 0:
                nx = self.x - (dx/dist)*self.speed
                ny = self.y - (dy/dist)*self.speed
                self.x, self.y = clamp_to_grid(nx, ny)

            if self.has_gun:
                self.fire_cooldown -= 1
                if self.fire_cooldown <= 0:
                    self.fire_at_player(px, py)
                    self.fire_cooldown = self.fire_rate
        else:
            if dist > 25 and dist > 0:
                nx = self.x + (dx/dist)*self.speed
                ny = self.y + (dy/dist)*self.speed
                self.x, self.y = clamp_to_grid(nx, ny)

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

    def fire_at_player(self, px, py):
        global vecna_bullets
        ang = math.degrees(math.atan2(py - self.y, px - self.x))
        vecna_bullets.append(Bullet(self.x, self.y, self.z, ang, 10.0, is_vecna=True))

    def take_damage(self):
        self.health -= 1
        self.hit_cooldown = 10
        if self.health <= 0:
            self.active = False
            return True
        return False

    def draw(self):
        glPushMatrix()
        if self.hit_cooldown > 0:
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(*self.color)

        glTranslatef(self.x, self.y, self.z)

        # Enemy shapes:
        if self.type == "Demogorgon":
            glColor3f(0.5, 0.3, 0.2)
            glPushMatrix()
            glTranslatef(0, 0, 22)
            glRotatef(90, 1, 0, 0)
            draw_star_2d_xy(0.0, 0.0, 26.0, 11.0)
            glPopMatrix()

        elif self.type == "Bats":
            glColor3f(0.0, 0.0, 0.5)
            glPushMatrix()
            glTranslatef(0, 0, 24)
            glRotatef(90, 1, 0, 0)
            draw_bat_triangles_2d_xy(scale=70.0)
            glPopMatrix()

        else:  # Vecna
            glPushMatrix()
            glTranslatef(0, 0, 0)
            draw_vecna_Y_3d(scale=1.0)
            glPopMatrix()

        glPopMatrix()

def draw_enemy_health_bar(enemy):
    if enemy.level == 4:
        max_h = 5 if enemy.type == "Vecna" else 1
    else:
        max_h = level_config[enemy.level]["health"]
    bar_w = 36
    bar_h = 6
    health_w = bar_w * (enemy.health / max_h)

    glPushMatrix()
    glTranslatef(enemy.x, enemy.y, enemy.z + 45)

    glColor3f(0.8, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-bar_w/2, 0, 0)
    glVertex3f(bar_w/2, 0, 0)
    glVertex3f(bar_w/2, bar_h, 0)
    glVertex3f(-bar_w/2, bar_h, 0)
    glEnd()

    glColor3f(0.2, 0.8, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-bar_w/2, 0, 0)
    glVertex3f(-bar_w/2 + health_w, 0, 0)
    glVertex3f(-bar_w/2 + health_w, bar_h, 0)
    glVertex3f(-bar_w/2, bar_h, 0)
    glEnd()

    glPopMatrix()

# ==================== DRAWING ====================

def draw_grid():

    global grid_flash_timer, grid_flash_active

    if grid_flash_active:
        base = grid_color_red if (grid_flash_timer % 20 < 10) else grid_color_normal
        grid_flash_timer += 1
        if grid_flash_timer > 100:
            grid_flash_active = False
            grid_flash_timer = 0
    else:
        base = grid_color_normal

    half = GRID_LENGTH
    tiles = GRID_TILES
    tile = (2.0 * half) / tiles

    # --- Floor tiles ---
    glBegin(GL_QUADS)
    for i in range(tiles):
        for j in range(tiles):
            if (i + j) % 2 == 0:
                glColor3f(0.0, 0.42, 0.31)  # Phthalo Green
            else:
                glColor3f(0.96, 0.96, 0.92) # Off-white

            x0 = -half + i * tile
            y0 = -half + j * tile
            x1 = x0 + tile
            y1 = y0 + tile

            glVertex3f(x0, y0, 0)
            glVertex3f(x1, y0, 0)
            glVertex3f(x1, y1, 0)
            glVertex3f(x0, y1, 0)
    glEnd()

    # --- Boundary walls ---
    h = WALL_HEIGHT
    glBegin(GL_QUADS)
    # South wall (y=-half)
    glColor3f(0.502, 0, 0.126)
    glVertex3f(-half, -half, 0)
    glVertex3f( half, -half, 0)
    glVertex3f( half, -half, h)
    glVertex3f(-half, -half, h)

    # North wall (y=+half)
    glColor3f(0.502, 0, 0.126)
    glVertex3f( half,  half, 0)
    glVertex3f(-half,  half, 0)
    glVertex3f(-half,  half, h)
    glVertex3f( half,  half, h)

    # East wall (x=+half)
    glColor3f(0.502, 0, 0.126)
    glVertex3f( half, -half, 0)
    glVertex3f( half,  half, 0)
    glVertex3f( half,  half, h)
    glVertex3f( half, -half, h)

    # West wall (x=-half)
    glColor3f(0.502, 0, 0.126)
    glVertex3f(-half,  half, 0)
    glVertex3f(-half, -half, 0)
    glVertex3f(-half, -half, h)
    glVertex3f(-half,  half, h)
    glEnd()

def draw_player_model(pos, rot_deg, gun_rot_deg, is_eleven=False):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rot_deg, 0, 0, 1)

    # Fall over when game over
    if game_state == "game_over":
        glRotatef(90, 1, 0, 0)

    # --- legs ---
    glColor3f(0.13, 0.26, 0.71)  # blue pants
    for x_off in (10, -10):
        glPushMatrix()
        glTranslatef(x_off, 0, 0)
        gluCylinder(gluNewQuadric(), 6, 3, 28, 12, 6)
        glPopMatrix()

    # --- body ---
    if is_eleven:
        glColor3f(0.55, 0.30, 0.35)
    else:
        glColor3f(1.0, 0.5, 0.25)
    glPushMatrix()
    glTranslatef(0, 0, 35)
    glScalef(22, 14, 30)
    glutSolidCube(1)
    glPopMatrix()

    # --- head ---
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 60)
    gluSphere(gluNewQuadric(), 10, 16, 16)
    glPopMatrix()

    # --- arms ---
    if is_eleven:
        glColor3f(0.85, 0.75, 0.70)
    else:
        glColor3f(0.8, 0.7, 0.6)
    for y_off in (12, -12):
        glPushMatrix()
        glTranslatef(0, y_off, 45)
        glRotatef(90, 0, 1, 0)   # cylinder axis from z -> x
        gluCylinder(gluNewQuadric(), 3.5, 2.0, 18, 12, 2)
        glPopMatrix()

    # --- gun ---
    if game_state != "game_over":
        glColor3f(0.7, 0.7, 0.7)
        glPushMatrix()
        glRotatef(gun_rot_deg, 0, 0, 1)
        glTranslatef(18, 0, 38)
        glRotatef(90, 0, 1, 0)  # point gun forward along x
        gluCylinder(gluNewQuadric(), 3.0, 2.3, 22, 16, 2)
        glPopMatrix()

    glPopMatrix()

def draw_player():
    # Selected player
    draw_player_model(player_pos, player_rotation, gun_rotation, is_eleven=False)

def draw_eleven():
    # ONLY in cheat mode
    draw_player_model(eleven_pos, eleven_rotation, eleven_gun_rotation, is_eleven=True)

def _fp_gun_basis():
    ang = player_rotation + gun_rotation
    ang_r = math.radians(ang)
    cam_x = player_pos[0]
    cam_y = player_pos[1]
    cam_z = player_pos[2] + 55
    fx = math.cos(ang_r)
    fy = math.sin(ang_r)
    rx = -math.sin(ang_r)
    ry = math.cos(ang_r)
    return ang, ang_r, cam_x, cam_y, cam_z, fx, fy, rx, ry

def _fp_gun_base_and_muzzle():
    ang, ang_r, cam_x, cam_y, cam_z, fx, fy, rx, ry = _fp_gun_basis()

    forward = 28.0
    right = 14.0
    up = -10.0
    barrel_len = 15.0  
    base_x = cam_x + fx * forward + rx * right
    base_y = cam_y + fy * forward + ry * right
    base_z = cam_z + up

    muzzle_x = base_x + fx * barrel_len
    muzzle_y = base_y + fy * barrel_len
    muzzle_z = base_z

    return (base_x, base_y, base_z), (muzzle_x, muzzle_y, muzzle_z), ang

def draw_first_person_gun():

    if game_state == "game_over":
        return

    glPushMatrix()

    (base_x, base_y, base_z), _, ang = _fp_gun_base_and_muzzle()

    glTranslatef(base_x, base_y, base_z)
    glRotatef(ang, 0, 0, 1)

    # gun cylinder pointing forward
    glColor3f(0.7, 0.7, 0.7)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 3.2, 2.6, 18, 16, 2)

    # muzzle sphere
    glTranslatef(0, 0, 18)
    glColor3f(0.4, 0.4, 0.4)
    gluSphere(gluNewQuadric(), 2.6, 12, 12)

    glPopMatrix()

def draw_hud():
    enemy_name = "Mixed Enemies" if current_level == 4 else level_config[current_level]["type"]
    draw_text(10, 770, "Defenders of the Hawkins")
    draw_text(10, 740, f"Character: {selected_character} | Strength: {character_strength:.1f}x")
    draw_text(10, 710, f"Level {current_level}: {enemy_name}")
    draw_text(10, 680, f"Score: {score} | Lives: {lives}")
    draw_text(10, 650, f"Camera: {camera_mode} (Right Click and press F toggles)")
    draw_text(10, 620, f"Cheat Mode (Eleven): {'ON' if cheat_mode_active else 'OFF'}")
    draw_text(10, 40, "W/S: Move | A/D: Rotate | Space/LeftClick: Fire | C: Cheat | R: Reset")

def draw_menu():
    draw_text(350, 520, "DEFENDERS OF THE HAWKINS", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(400, 470, "Swapnil | Nafisa | Mehrab")
    draw_text(420, 420, "Press SPACE to Start")
    draw_text(400, 380, "Press C for Character Select")

def draw_character_select():
    draw_text(380, 600, "SELECT YOUR CHARACTER", GLUT_BITMAP_TIMES_ROMAN_24)
    y0 = 520
    for i, ch in enumerate(characters):
        strength = character_strengths[ch]
        prefix = ">> " if ch == selected_character else "   "
        draw_text(350, y0 - i*40, f"{prefix}{i+1}. {ch} - Strength: {strength}x")
    draw_text(350, 300, "Press 1-5 to select character")
    draw_text(350, 260, "Press SPACE to confirm and start")

def draw_game_over():
    draw_text(400, 450, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(420, 400, f"Final Score: {score}")
    draw_text(420, 350, f"Level Reached: {current_level}")
    draw_text(380, 300, "Press R to restart")
    draw_text(380, 270, "Press ESC for menu")

def draw_level_complete():
    draw_text(380, 450, "LEVEL COMPLETE!", GLUT_BITMAP_TIMES_ROMAN_24)
    draw_text(420, 400, f"Score: {score}")
    if bonus_lives_earned > 0:
        draw_text(340, 350, "BONUS! +1 Life (Perfect Clear!)")
    if current_level < 4:
        draw_text(370, 300, "Press SPACE for next level")
    else:
        draw_text(280, 600, "SUPERCALIFRAGILISTICEXPIALIDOCIOUS!",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(350, 300, "YOU SAVED HAWKINS!")
        draw_text(380, 270, "Press R to play again")
    draw_text(380, 240, "Press ESC for menu")

# ==================== GAME LOGIC ====================
def start_level(level):
    global current_level, enemies, vecna_bullets, bullets, enemy_spawn_timer, enemies_spawned_this_level
    current_level = level
    enemies = []
    bullets = []
    vecna_bullets = []
    enemy_spawn_timer = 0
    enemies_spawned_this_level = 0
def reset_game():
    KEY_HELD.clear()
    KEY_DOWN_TIME.clear()
    global game_state, current_level, score, lives, previous_lives, bonus_lives_earned
    global player_pos, player_rotation, gun_rotation
    global bullets, vecna_bullets, enemies
    global cheat_mode_active, eleven_fire_cooldown, fire_cooldown
    global camera_mode, camera_height, camera_distance, camera_angle
    global grid_flash_active, grid_flash_timer
    game_state = "menu"
    current_level = 1
    score = 0
    lives = 3
    previous_lives = 3
    bonus_lives_earned = 0
    player_pos = [0.0, 0.0, 0.0]
    player_rotation = 0.0
    gun_rotation = 0.0
    bullets = []
    vecna_bullets = []
    enemies = []
    cheat_mode_active = False
    eleven_fire_cooldown = 0
    fire_cooldown = 0
    camera_mode = "TPS"
    camera_height = 140.0
    camera_distance = 320.0
    camera_angle = 0
    grid_flash_active = False
    grid_flash_timer = 0
def spawn_enemy():
    global enemies, enemy_spawn_timer, enemies_spawned_this_level
    cfg = level_config[current_level]

    if current_level == 4:
        if enemies_spawned_this_level >= 7:
            return
        vecna_count = len([e for e in enemies if e.active and e.type == "Vecna"])
        demo_count = len([e for e in enemies if e.active and e.type == "Demogorgon"])
        bats_count = len([e for e in enemies if e.active and e.type == "Bats"])

        if vecna_count < 1:
            etype, dist = "Vecna", 600
        elif demo_count < 3:
            etype, dist = "Demogorgon", 520
        elif bats_count < 3:
            etype, dist = "Bats", 520
        else:
            return
    else:
        if enemies_spawned_this_level >= cfg["total_enemies"]:
            return
        active = len([e for e in enemies if e.active])
        if active >= cfg["max_concurrent"]:
            return
        etype, dist = cfg["type"], cfg["spawn_distance"]

    ang = random.uniform(0, 2*math.pi)
    max_dist = min(dist, GRID_LENGTH - 120)
    min_dist = max(260, GRID_LENGTH * 0.45)
    use_dist = random.uniform(min_dist, max_dist) if max_dist > min_dist else max_dist

    ex = player_pos[0] + math.cos(ang) * use_dist
    ey = player_pos[1] + math.sin(ang) * use_dist
    ex, ey = clamp_to_grid(ex, ey)

    new_enemy = Enemy(ex, ey, etype, current_level)
    if current_level in (1, 2) and cfg.get("approach_time", 0) > 0:
        frames = cfg["approach_time"] * 60
        if frames > 0:
            new_enemy.speed = dist / frames

    enemies.append(new_enemy)
    enemies_spawned_this_level += 1
    enemy_spawn_timer = 0

def fire_bullet(is_eleven=False, origin=None, angle=None):
    global fire_cooldown, bullets
    if is_eleven:
        ox, oy, oz = origin
        bullets.append(Bullet(ox, oy, oz, angle, bullet_speed, is_eleven=True))
        return

    if fire_cooldown > 0:
        return

    bullet_angle = player_rotation + gun_rotation

    # In FPS
    if camera_mode == "FPS":
        _, (mx, my, mz), bullet_angle = _fp_gun_base_and_muzzle()
        bullets.append(Bullet(mx, my, mz, bullet_angle, bullet_speed))
    else:
        ox = player_pos[0] + math.cos(math.radians(bullet_angle)) * 30
        oy = player_pos[1] + math.sin(math.radians(bullet_angle)) * 30
        oz = player_pos[2] + 30
        bullets.append(Bullet(ox, oy, oz, bullet_angle, bullet_speed))
    fire_cooldown = int(max_fire_cooldown / character_strength)

def update_eleven():    
    global eleven_pos, eleven_fire_cooldown
    offset_distance = 60
    offset_angle = player_rotation + 90
    eleven_pos[0] = player_pos[0] + math.cos(math.radians(offset_angle)) * offset_distance
    eleven_pos[1] = player_pos[1] + math.sin(math.radians(offset_angle)) * offset_distance
    eleven_pos[2] = player_pos[2]
    eleven_pos[0], eleven_pos[1] = clamp_to_grid(eleven_pos[0], eleven_pos[1])

    if eleven_fire_cooldown > 0:
        eleven_fire_cooldown -= 1

    if eleven_fire_cooldown <= 0:
        closest = None
        best = float("inf")
        for e in enemies:
            if not e.active:
                continue
            dx = e.x - eleven_pos[0]
            dy = e.y - eleven_pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < eleven_detection_range and dist < best:
                best = dist
                closest = e
        if closest:
            ang = math.degrees(math.atan2(closest.y - eleven_pos[1], closest.x - eleven_pos[0]))

            # Aim Eleven
            globals()['eleven_rotation'] = ang
            globals()['eleven_gun_rotation'] = 0.0

            fire_bullet(is_eleven=True, origin=(eleven_pos[0], eleven_pos[1], eleven_pos[2] + 30), angle=ang)
            eleven_fire_cooldown = eleven_fire_rate

def check_collisions():
    global score, lives, previous_lives, game_state, grid_flash_active, grid_flash_timer

    # player bullets vs enemies
    for b in bullets:
        if not b.active:
            continue
        for e in enemies:
            if not e.active:
                continue
            dx = b.x - e.x
            dy = b.y - e.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 30:
                b.active = False
                killed = e.take_damage()
                if killed:
                    bonus = 15 if b.is_eleven else 10
                    score += bonus * current_level

    # vecna bullets vs player
    for vb in vecna_bullets:
        if not vb.active:
            continue
        dx = vb.x - player_pos[0]
        dy = vb.y - player_pos[1]
        if math.sqrt(dx*dx + dy*dy) < 30:
            vb.active = False
            lives -= 1

            if lives < 2 and previous_lives >= 2 and not cheat_mode_active:
                grid_flash_active = True
                grid_flash_timer = 0
            previous_lives = lives
            if lives <= 0:
                game_state = "game_over"
    # enemies vs player (colision)
    for e in enemies:
        if not e.active or e.avoids_collision:
            continue
        dx = player_pos[0] - e.x
        dy = player_pos[1] - e.y
        if math.sqrt(dx*dx + dy*dy) < 40:
            e.active = False
            lives -= 1

            if lives < 2 and previous_lives >= 2 and not cheat_mode_active:
                grid_flash_active = True
                grid_flash_timer = 0
            previous_lives = lives
            if lives <= 0:
                game_state = "game_over"
def check_level_complete():
    global game_state, bonus_lives_earned, lives
    if current_level > 4:
        return

    cfg = level_config[current_level]
    active = len([e for e in enemies if e.active])

    if current_level == 4:
        all_spawned = enemies_spawned_this_level >= 7
    else:
        all_spawned = enemies_spawned_this_level >= cfg["total_enemies"]

    if all_spawned and active == 0:
        game_state = "level_complete"
        if lives >= 3:
            lives += 1
            bonus_lives_earned = 1

def update():
    global fire_cooldown, enemy_spawn_timer, vecna_bullets
    global player_rotation, player_pos

    if game_state != "playing":
        return

    #Continuous movement 
    global _last_move_time
    now = time.time()
    dt = now - _last_move_time
    _last_move_time = now

    # Avoid jumps
    if dt > 0.1:
        dt = 0.1

    # Only move if held long enough
    move_dx = 0.0
    move_dy = 0.0

    # Helper => movement in direction of an angle
    def _add_move(angle_deg, sign=1.0):
        nonlocal move_dx, move_dy
        ang = math.radians(angle_deg)
        move_dx += math.cos(ang) * MOVE_SPEED_PER_SEC * dt * sign
        move_dy += math.sin(ang) * MOVE_SPEED_PER_SEC * dt * sign

    # Forward/back
    if KEY_HELD.get(b'w'):
        if (now - KEY_DOWN_TIME.get(b'w', now)) >= HOLD_MOVE_THRESHOLD:
            _add_move(player_rotation, 1.0)

    if KEY_HELD.get(b's'):
        if (now - KEY_DOWN_TIME.get(b's', now)) >= HOLD_MOVE_THRESHOLD:
            _add_move(player_rotation, -1.0)

    # Hold A/D => slow rotation
    if KEY_HELD.get(b'a'):
        if (now - KEY_DOWN_TIME.get(b'a', now)) >= HOLD_MOVE_THRESHOLD:
            player_rotation += ROTATE_SPEED_PER_SEC * dt

    if KEY_HELD.get(b'd'):
        if (now - KEY_DOWN_TIME.get(b'd', now)) >= HOLD_MOVE_THRESHOLD:
            player_rotation -= ROTATE_SPEED_PER_SEC * dt

    # Normalize rotation after continuous change
    player_rotation %= 360.0

    if move_dx != 0.0 or move_dy != 0.0:
        nx = player_pos[0] + move_dx
        ny = player_pos[1] + move_dy
        player_pos[0], player_pos[1] = clamp_to_grid(nx, ny)

# cooldowns
    if fire_cooldown > 0:
        fire_cooldown -= 1

    # cheat mode
    if cheat_mode_active:
        update_eleven()

    # bullets update
    for b in bullets:
        b.update()
    bullets[:] = [b for b in bullets if b.active]

    for vb in vecna_bullets:
        vb.update()
    vecna_bullets[:] = [b for b in vecna_bullets if b.active]

    # spawn enemies over time
    enemy_spawn_timer += 1
    spawn_rate = level_config[current_level].get("spawn_rate", 120)
    if enemy_spawn_timer >= spawn_rate:
        spawn_enemy()

    # update enemies
    for e in enemies:
        if e.active:
            e.update(player_pos[0], player_pos[1])

    check_collisions()
    check_level_complete()

# ==================== INPUT HANDLERS ====================
def keyboardListener(key, x, y):
    global game_state, selected_character, character_strength
    global cheat_mode_active, current_level
    global player_rotation, gun_rotation

    # ESC key
    if key == b'\x1b':
        if game_state != "menu":
            game_state = "menu"
        glutPostRedisplay()
        return

    if game_state == "menu":
        if key == b' ':
            game_state = "playing"
            start_level(1)
        elif key == b'c' or key == b'C':
            game_state = "character_select"

    elif game_state == "character_select":
        if key in [b'1', b'2', b'3', b'4', b'5']:
            idx = int(chr(key[0])) - 1
            selected_character = characters[idx]
            character_strength = character_strengths[selected_character]
        elif key == b' ':
            game_state = "playing"
            start_level(1)
    elif game_state == "playing":


        # Movement control:
        if key in (b'w', b'W', b'a', b'A', b's', b'S', b'd', b'D'):
            k = bytes([key[0] + 32]) if b'A'[0] <= key[0] <= b'Z'[0] else key  # to lowercase
            if not KEY_HELD.get(k, False):
                KEY_HELD[k] = True
                KEY_DOWN_TIME[k] = time.time()
            glutPostRedisplay()
            return

        if key == b' ':
            fire_bullet()
        elif key == b'c' or key == b'C':
            cheat_mode_active = not cheat_mode_active
        elif key == b'f' or key == b'F':
            # Toggle TPS/FPS
            globals()['camera_mode'] = "FPS" if camera_mode == "TPS" else "TPS"

        # normalize rotation
        player_rotation %= 360.0

    elif game_state == "level_complete":
        if key == b' ':
            if current_level < 4:
                game_state = "playing"
                start_level(current_level + 1)
            else:
                reset_game()

    elif game_state == "game_over":
        if key == b'r' or key == b'R':
            reset_game()

    # Global reset
    if key == b'r' or key == b'R':
        if game_state != "game_over":
            reset_game()

    glutPostRedisplay()


def keyboardUpListener(key, x, y):
    global player_rotation
    # Only in gameplay
    if game_state != "playing":
        # normalize key to lowercase
        k = bytes([key[0] + 32]) if b'A'[0] <= key[0] <= b'Z'[0] else key
        KEY_HELD[k] = False
        KEY_DOWN_TIME.pop(k, None)
        return

    k = bytes([key[0] + 32]) if b'A'[0] <= key[0] <= b'Z'[0] else key
    KEY_HELD[k] = False
    t0 = KEY_DOWN_TIME.pop(k, None)
    if t0 is None:
        return

    held_time = time.time() - t0

    # Tap to rotate  A/S only
    if held_time <= HOLD_MOVE_THRESHOLD:
        if k == b'a':
            player_rotation += 90.0
        elif k == b's':
            player_rotation += 180.0

        # normalize
        player_rotation %= 360.0

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_height, camera_angle, gun_rotation

    if key == GLUT_KEY_UP:
        camera_height += 20
    elif key == GLUT_KEY_DOWN:
        camera_height -= 20
    elif key == GLUT_KEY_LEFT:
        # TPS rotates camera FPS rotates gun
        if camera_mode == "FPS":
            gun_rotation += rotation_speed
        else:
            camera_angle += 10
    elif key == GLUT_KEY_RIGHT:
        if camera_mode == "FPS":
            gun_rotation -= rotation_speed
        else:
            camera_angle -= 10

    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global camera_mode
    if game_state == "playing" and state == GLUT_DOWN:
        if button == GLUT_LEFT_BUTTON:
            fire_bullet()
        elif button == GLUT_RIGHT_BUTTON:
            camera_mode = "FPS" if camera_mode == "TPS" else "TPS"
    glutPostRedisplay()

# ==================== CAMERA ====================
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 3500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == "TPS":
        ang = player_rotation + camera_angle
        cam_x = player_pos[0] - math.cos(math.radians(ang)) * camera_distance
        cam_y = player_pos[1] - math.sin(math.radians(ang)) * camera_distance
        cam_z = player_pos[2] + camera_height

        gluLookAt(cam_x, cam_y, cam_z,
                  player_pos[0], player_pos[1], player_pos[2] + 30,
                  0, 0, 1)
    else:
        look_dist = 120
        look_ang = player_rotation + gun_rotation
        lx = player_pos[0] + math.cos(math.radians(look_ang)) * look_dist
        ly = player_pos[1] + math.sin(math.radians(look_ang)) * look_dist

        gluLookAt(player_pos[0], player_pos[1], player_pos[2] + 55,
                  lx, ly, player_pos[2] + 55,
                  0, 0, 1)

# ==================== RENDER LOOP ====================
def compute_background_color():
    if cheat_mode_active:
        return (0.066667, 0.066667, 0.313725)  # blue
    if lives <= 1:
        return (0.50, 0.10, 0.10)  # danger red
    
    return (0.05, 0.05, 0.10)      # normal dark

def showScreen():
    bg = compute_background_color()
    glClearColor(bg[0], bg[1], bg[2], 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    if game_state == "menu":
        draw_menu()

    elif game_state == "character_select":
        draw_character_select()

    elif game_state == "game_over":
        draw_game_over()

    elif game_state == "level_complete":
        draw_level_complete()

    elif game_state == "playing":
        setupCamera()
        draw_grid()

        if camera_mode == "TPS":
            draw_player()
        else:
            draw_first_person_gun()

        if cheat_mode_active:
            draw_eleven()

        for b in bullets:
            if b.active:
                b.draw()
        for vb in vecna_bullets:
            if vb.active:
                vb.draw()
        for e in enemies:
            if e.active:
                e.draw()

        draw_hud()

    glutSwapBuffers()

def idle():
    update()
    glutPostRedisplay()

# ==================== MAIN ====================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Defenders of the Hawkins")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()