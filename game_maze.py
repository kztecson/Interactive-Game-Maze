import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import time

DISPLAY_SIZE = (800, 600)
MAZE_WIDTH = 12 
MAZE_HEIGHT = 12 
MOVE_SPEED = 0.1
TURN_SPEED = 2.0

# Textures
WALL_TEXTURE_FILE = "wall_texture.jpg"
FLOOR_TEXTURE_FILE = "floor_texture.jpg"
EYE_TEXTURE_FILE = "red_eye_texture.png" 
TRAP_TEXTURE_FILE = "rust_texture.jpg" 

# Globals
maze_map = []
spheres = [] 
traps = [] 
powerups = [] 
pyramids = [] 
start_time = 0
final_time = 0
game_over = False 
game_font = None 
big_font = None 
maze_display_list = None
show_minimap = False 
show_legend = False 
show_icons = False 
diamond_rot = 0 

# Game States
blindness_active = False
blindness_start_time = 0
speed_boost_active = False
speed_boost_end_time = 0
launch_active = False 
launch_start_time = 0
slow_walk_active = False 

# Maze generation
def generate_maze(width, height):
    real_w = width * 2 + 1
    real_h = height * 2 + 1
    maze = [[1 for _ in range(real_w)] for _ in range(real_h)]
    def get_neighbors(r, c):
        neighbors = []
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 < nr < real_h and 0 < nc < real_w and maze[nr][nc] == 1:
                neighbors.append((nr, nc))
        return neighbors

    stack = [(1, 1)]
    maze[1][1] = 0
    
    while stack:
        current_r, current_c = stack[-1]
        neighbors = get_neighbors(current_r, current_c)
        if neighbors:
            next_r, next_c = random.choice(neighbors)
            wall_r = current_r + (next_r - current_r) // 2
            wall_c = current_c + (next_c - current_c) // 2
            maze[wall_r][wall_c] = 0
            maze[next_r][next_c] = 0
            stack.append((next_r, next_c))
        else:
            stack.pop()
    maze[1][1] = 2
    maze[real_h-2][real_w-2] = 3 
    return maze

def place_random_eyes(maze):
    eye_list = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if r < 4 and c < 4: continue
            if maze[r][c] in [0, 2, 3]: 
                if random.random() < 0.05: 
                    eye_list.append([c * 2, r * 2])
    return eye_list

def place_random_traps(maze):
    trap_list = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if r < 4 and c < 4: continue
            if maze[r][c] == 0: 
                if random.random() < 0.1: 
                    trap_list.append((r, c)) 
    return trap_list

def place_random_powerups(maze, occupied_set):
    cyl_list = []
    new_occupied = occupied_set.copy()
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if r < 4 and c < 4: continue
            if maze[r][c] == 0: 
                if (r, c) not in new_occupied:
                    if random.random() < 0.05: 
                        cyl_list.append([c * 2, r * 2])
                        new_occupied.add((r, c))
    return cyl_list, new_occupied

def place_random_pyramids(maze, occupied_set):
    pyr_list = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if r < 4 and c < 4: continue
            if maze[r][c] == 0: 
                if (r, c) not in occupied_set:
                    if random.random() < 0.03: 
                        pyr_list.append([c * 2, r * 2])
    return pyr_list

def get_random_spawn(maze):
    while True:
        r = random.randint(0, len(maze)-1)
        c = random.randint(0, len(maze[0])-1)
        if r < 4 and c < 4: continue
        if maze[r][c] != 1:
            return c * 2, r * 2

# Cube Data
vertices = ((1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
            (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1))
surfaces = ((0,1,2,3), (3,2,7,6), (6,7,5,4), (4,5,1,0), (1,5,7,2), (4,0,3,6))
normals = ((0, 0, -1), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0), (0, -1, 0))
tex_coords = ((0,0), (1,0), (1,1), (0,1))

wall_tex_id = None
floor_tex_id = None
eye_tex_id = None
trap_tex_id = None

def load_image_texture(filename):
    try:
        textureSurface = pygame.image.load(filename)
    except pygame.error as e:
        print(f"Error loading {filename}: {e}")
        pygame.quit(); quit()
    textureData = pygame.image.tostring(textureSurface, "RGB", 1)
    width = textureSurface.get_width()
    height = textureSurface.get_height()
    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, textureData)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texid

def draw_cube():
    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glNormal3fv(normals[i])
        for j, vertex in enumerate(surface):
            glTexCoord2fv(tex_coords[j])
            glVertex3fv(vertices[vertex])
    glEnd()

def create_maze_display_list():
    new_list_id = glGenLists(1)
    glNewList(new_list_id, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, wall_tex_id)
    rows = len(maze_map)
    cols = len(maze_map[0])
    for r in range(rows):
        for c in range(cols):
            if maze_map[r][c] == 1:
                glPushMatrix()
                glTranslatef(c * 2, 0, r * 2) 
                draw_cube()
                glPopMatrix()
    glEndList()
    return new_list_id

def is_looking_at(px, pz, pyaw, sx, sz):
    to_sphere_x = sx - px
    to_sphere_z = sz - pz
    dist = math.sqrt(to_sphere_x**2 + to_sphere_z**2)
    if dist == 0 or dist > 15: return False 
    to_sphere_x /= dist
    to_sphere_z /= dist
    cam_x = math.sin(math.radians(pyaw))
    cam_z = -math.cos(math.radians(pyaw))
    dot = to_sphere_x * cam_x + to_sphere_z * cam_z
    return dot > 0.9

def draw_spheres(player_x, player_z, player_yaw):
    glBindTexture(GL_TEXTURE_2D, eye_tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    quadric = gluNewQuadric()
    gluQuadricTexture(quadric, GL_TRUE)
    
    for sphere in spheres:
        sx, sz = sphere[0], sphere[1]
        
        glPushMatrix()
        glTranslatef(sx, -0.3, sz)
        dx = player_x - sx
        dz = player_z - sz
        angle = math.degrees(math.atan2(dx, dz)) + 180
        glRotatef(angle, 0, 1, 0)
        glRotatef(90, 1, 0, 0)
        
        glColor4f(1, 1, 1, 1)
        gluSphere(quadric, 0.3, 32, 32)
        glPopMatrix()
    
    glDisable(GL_BLEND)

def draw_powerups():
    glDisable(GL_TEXTURE_2D)
    glMaterialfv(GL_FRONT, GL_EMISSION, [1.0, 1.0, 0.0, 1.0])
    glColor3f(1.0, 1.0, 0.0) 
    
    quadric = gluNewQuadric()
    bob_height = math.sin(time.time() * 5.0) * 0.1
    
    for p in powerups:
        px, pz = p[0], p[1]
        glPushMatrix()
        glTranslatef(px, -0.7 + bob_height, pz) 
        glRotatef(diamond_rot, 0, 1, 0) 
        gluSphere(quadric, 0.2, 32, 32)
        glPopMatrix()
        
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1) 

def draw_pyramids():
    glDisable(GL_TEXTURE_2D)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.5, 0.0, 0.8, 1.0])
    glColor3f(0.5, 0.0, 0.8) 
    bob_height = math.sin(time.time() * 3.0) * 0.1
    
    for p in pyramids:
        px, pz = p[0], p[1]
        glPushMatrix()
        glTranslatef(px, -0.7 + bob_height, pz)
        glRotatef(diamond_rot, 0, 1, 0) 
        glScalef(0.4, 0.4, 0.4) 
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 1, 0); glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1)
        glVertex3f(0, 1, 0); glVertex3f(1, -1, 1); glVertex3f(1, -1, -1)
        glVertex3f(0, 1, 0); glVertex3f(1, -1, -1); glVertex3f(-1, -1, -1)
        glVertex3f(0, 1, 0); glVertex3f(-1, -1, -1); glVertex3f(-1, -1, 1)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1); glVertex3f(1, -1, -1); glVertex3f(-1, -1, -1)
        glEnd()
        glPopMatrix()

    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1) 

def draw_diamond():
    global diamond_rot
    diamond_rot = (diamond_rot + 2) % 360
    finish_r = len(maze_map) - 2
    finish_c = len(maze_map[0]) - 2
    x = finish_c * 2
    z = finish_r * 2
    glPushMatrix()
    glTranslatef(x, 0, z) 
    glRotatef(diamond_rot, 0, 1, 0) 
    glScalef(0.5, 0.5, 0.5) 
    glDisable(GL_TEXTURE_2D)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 1.0, 0.0, 1]) 
    glColor3f(0.0, 1.0, 0.0) 
    glBegin(GL_TRIANGLES)
    # Top
    glVertex3f(0, 1, 0); glVertex3f(1, 0, 0); glVertex3f(0, 0, 1)
    glVertex3f(0, 1, 0); glVertex3f(0, 0, 1); glVertex3f(-1, 0, 0)
    glVertex3f(0, 1, 0); glVertex3f(-1, 0, 0); glVertex3f(0, 0, -1)
    glVertex3f(0, 1, 0); glVertex3f(0, 0, -1); glVertex3f(1, 0, 0)
    # Bottom
    glVertex3f(0, -1, 0); glVertex3f(0, 0, 1); glVertex3f(1, 0, 0)
    glVertex3f(0, -1, 0); glVertex3f(-1, 0, 0); glVertex3f(0, 0, 1)
    glVertex3f(0, -1, 0); glVertex3f(0, 0, -1); glVertex3f(-1, 0, 0)
    glVertex3f(0, -1, 0); glVertex3f(1, 0, 0); glVertex3f(0, 0, -1)
    glEnd()
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    glEnable(GL_TEXTURE_2D)
    glPopMatrix()
    return x, z 

def draw_floor():
    glBindTexture(GL_TEXTURE_2D, floor_tex_id)
    tile_count = 100 
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0, 0); glVertex3f(-100, -1, -100)
    glTexCoord2f(tile_count, 0); glVertex3f(100, -1, -100)
    glTexCoord2f(tile_count, tile_count); glVertex3f(100, -1, 100)
    glTexCoord2f(0, tile_count); glVertex3f(-100, -1, 100)
    glEnd()

def draw_traps():
    glBindTexture(GL_TEXTURE_2D, trap_tex_id)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    for (r, c) in traps:
        x = c * 2
        z = r * 2
        y = -0.99 
        glTexCoord2f(0, 0); glVertex3f(x - 1, y, z - 1)
        glTexCoord2f(1, 0); glVertex3f(x + 1, y, z - 1)
        glTexCoord2f(1, 1); glVertex3f(x + 1, y, z + 1)
        glTexCoord2f(0, 1); glVertex3f(x - 1, y, z + 1)
    glEnd()

def set_ortho_projection():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, DISPLAY_SIZE[0], 0, DISPLAY_SIZE[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def restore_perspective_projection():
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D) 
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_hud_menu(elapsed, px, pz):
    if game_over: return 

    set_ortho_projection()
    
    menu_w, menu_h, margin = 220, 220, 20
    
    glDisable(GL_TEXTURE_2D)
    glColor4f(0, 0, 0, 0.5) 
    glBegin(GL_QUADS)
    glVertex2f(margin, DISPLAY_SIZE[1] - margin)
    glVertex2f(margin + menu_w, DISPLAY_SIZE[1] - margin)
    glVertex2f(margin + menu_w, DISPLAY_SIZE[1] - margin - menu_h)
    glVertex2f(margin, DISPLAY_SIZE[1] - margin - menu_h)
    glEnd()

    glColor4f(1, 1, 1, 1) 
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(margin, DISPLAY_SIZE[1] - margin)
    glVertex2f(margin + menu_w, DISPLAY_SIZE[1] - margin)
    glVertex2f(margin + menu_w, DISPLAY_SIZE[1] - margin - menu_h)
    glVertex2f(margin, DISPLAY_SIZE[1] - margin - menu_h)
    glEnd()

    lines = [f"Time: {elapsed}s", f"Pos: {int(px/2)}, {int(pz/2)}", "----------------", "[R] Reset", "[G] New Maze", "[M] Toggle Map", "[L] Legend", "[Z] Slow Walk"]
    
    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1)
    start_y = margin + 10
    
    for i, line in enumerate(lines):
        text_surface = game_font.render(line, True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", 1)
        w, h = text_surface.get_width(), text_surface.get_height()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        x_pos = margin + 15
        y_pos = DISPLAY_SIZE[1] - start_y - (i * 25) - h
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
        glTexCoord2f(1, 0); glVertex2f(x_pos + w, y_pos)
        glTexCoord2f(1, 1); glVertex2f(x_pos + w, y_pos + h)
        glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + h)
        glEnd()
        glDeleteTextures(1, [tex_id])

    restore_perspective_projection()

def draw_legend():
    if not show_legend or game_over: return

    set_ortho_projection()
    
    legend_w, legend_h = 320, 180
    center_x = DISPLAY_SIZE[0] / 2 - legend_w / 2
    center_y = DISPLAY_SIZE[1] / 2 - legend_h / 2
    
    glDisable(GL_TEXTURE_2D)
    glColor4f(0, 0, 0, 0.8) 
    glBegin(GL_QUADS)
    glVertex2f(center_x, center_y); glVertex2f(center_x + legend_w, center_y)
    glVertex2f(center_x + legend_w, center_y + legend_h); glVertex2f(center_x, center_y + legend_h)
    glEnd()
    
    glColor4f(1, 1, 1, 1)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(center_x, center_y); glVertex2f(center_x + legend_w, center_y)
    glVertex2f(center_x + legend_w, center_y + legend_h); glVertex2f(center_x, center_y + legend_h)
    glEnd()

    lines = ["LEGEND:", "Eyeball = TELEPORTS YOU", "Rusty Floor = SLOWS YOU", "Yellow Sphere = SPEED BOOST", "Purple Pyramid = MAP VIEW"]
    
    glEnable(GL_TEXTURE_2D)
    start_text_y = center_y + legend_h - 30
    
    for i, line in enumerate(lines):
        color = (255, 255, 0, 255) if i == 0 else (255, 255, 255, 255)
        if i == 1: color = (200, 50, 50, 255) # Red
        elif i == 2: color = (200, 150, 100, 255) # Rusty
        elif i == 3: color = (255, 255, 0, 255) # Yellow
        elif i == 4: color = (200, 0, 255, 255) # Purple
        else: color = (255, 255, 255, 255) # White

        text_surface = game_font.render(line, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", 1)
        w, h = text_surface.get_width(), text_surface.get_height()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        x_pos = center_x + 20
        y_pos = start_text_y - (i * 30)
        
        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
        glTexCoord2f(1, 0); glVertex2f(x_pos + w, y_pos)
        glTexCoord2f(1, 1); glVertex2f(x_pos + w, y_pos + h)
        glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + h)
        glEnd()
        glDeleteTextures(1, [tex_id])

    restore_perspective_projection()

def draw_blindness_effect():
    global blindness_active
    
    if not blindness_active: return
    
    current_time = time.time()
    diff = current_time - blindness_start_time
    
    # 3.0 seconds total (0.5 in, 2.5 out)
    alpha = 0
    if diff < 0.5:
        alpha = diff / 0.5 
    elif diff < 3.0:
        alpha = 1.0 - ((diff - 0.5) / 2.5) 
    else:
        blindness_active = False
        return

    set_ortho_projection()
    glDisable(GL_TEXTURE_2D)
    glColor4f(0, 0, 0, alpha)
    
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(DISPLAY_SIZE[0], 0)
    glVertex2f(DISPLAY_SIZE[0], DISPLAY_SIZE[1]); glVertex2f(0, DISPLAY_SIZE[1])
    glEnd()
    
    restore_perspective_projection()

def draw_victory_screen():
    set_ortho_projection()
    
    glDisable(GL_TEXTURE_2D)
    glColor4f(0, 0, 0, 0.8) 
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(DISPLAY_SIZE[0], 0)
    glVertex2f(DISPLAY_SIZE[0], DISPLAY_SIZE[1]); glVertex2f(0, DISPLAY_SIZE[1])
    glEnd()
    
    lines = [
        "MAZE COMPLETED!",
        f"Total Time: {final_time} seconds",
        "",
        "Press [R] to Restart",
        "Press [G] for New Maze",
        "Press [ESC] to Quit"
    ]
    
    glEnable(GL_TEXTURE_2D)
    glColor3f(0.0, 1.0, 0.0) 
    
    center_x = DISPLAY_SIZE[0] / 2
    start_y = DISPLAY_SIZE[1] / 2 + 100
    
    for i, line in enumerate(lines):
        font = big_font if i == 0 else game_font
        color = (0, 255, 0, 255) if i == 0 else (255, 255, 255, 255)
        
        if line == "": continue

        text_surface = font.render(line, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", 1)
        w, h = text_surface.get_width(), text_surface.get_height()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        x_pos = center_x - (w / 2)
        y_pos = start_y - (i * 50)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
        glTexCoord2f(1, 0); glVertex2f(x_pos + w, y_pos)
        glTexCoord2f(1, 1); glVertex2f(x_pos + w, y_pos + h)
        glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + h)
        glEnd()
        glDeleteTextures(1, [tex_id])

    restore_perspective_projection()

def draw_minimap(px, pz):
    if not show_minimap or game_over: return

    set_ortho_projection()
    
    cell_size = 6
    map_w = len(maze_map[0]) * cell_size
    map_h = len(maze_map) * cell_size
    margin = 20
    
    start_x = DISPLAY_SIZE[0] - map_w - margin
    start_y = DISPLAY_SIZE[1] - map_h - margin
    
    glDisable(GL_TEXTURE_2D)
    
    # Background
    glColor4f(0.85, 0.75, 0.55, 0.9) 
    glBegin(GL_QUADS)
    glVertex2f(start_x - 5, start_y - 5); glVertex2f(start_x + map_w + 5, start_y - 5)
    glVertex2f(start_x + map_w + 5, start_y + map_h + 5); glVertex2f(start_x - 5, start_y + map_h + 5)
    glEnd()
    
    # Border
    glColor4f(0.3, 0.2, 0.1, 1.0) 
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(start_x - 5, start_y - 5); glVertex2f(start_x + map_w + 5, start_y - 5)
    glVertex2f(start_x + map_w + 5, start_y + map_h + 5); glVertex2f(start_x - 5, start_y + map_h + 5)
    glEnd()

    rows = len(maze_map)
    cols = len(maze_map[0])
    
    # Draw Walls and Start
    glBegin(GL_QUADS)
    for r in range(rows):
        for c in range(cols):
            cell_type = maze_map[r][c]
            
            if cell_type == 1: glColor3f(0.2, 0.2, 0.2) # Walls Dark Grey
            elif cell_type == 2: glColor3f(0, 0, 1) # Start Blue
            elif cell_type == 3: glColor3f(0, 1, 0) # End Green
            else: continue 
            
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size ) 
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
    glEnd()
    
    # Draw Map Icons
    if show_icons:
        # Draw Traps
        glBegin(GL_QUADS)
        glColor3f(0.8, 0.4, 0.1)
        for (r, c) in traps:
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size )
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
        glEnd()

        # Draw Eyes
        glBegin(GL_QUADS)
        glColor3f(0.6, 0, 0)
        for sphere in spheres:
            c = sphere[0] / 2
            r = sphere[1] / 2
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size )
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
        glEnd()

        # Draw Speed Powerups
        glBegin(GL_QUADS)
        glColor3f(1, 1, 0)
        for p in powerups:
            c = p[0] / 2
            r = p[1] / 2
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size )
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
        glEnd()

        # Draw Launch Pyramids
        glBegin(GL_QUADS)
        glColor3f(0.6, 0, 0.8)
        for p in pyramids:
            c = p[0] / 2
            r = p[1] / 2
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size )
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
        glEnd()
    
    # Player Dot
    player_grid_x = px / 2
    player_grid_z = pz / 2
    p_x = start_x + (player_grid_x * cell_size)
    p_y = start_y + ((rows - 1 - player_grid_z) * cell_size)
    
    glColor3f(1.0, 0, 0) 
    glBegin(GL_QUADS)
    glVertex2f(p_x - 1, p_y - 1); glVertex2f(p_x + cell_size + 1, p_y - 1)
    glVertex2f(p_x + cell_size + 1, p_y + cell_size + 1); glVertex2f(p_x - 1, p_y + cell_size + 1)
    glEnd()
    
    # Toggle Info Text
    glEnable(GL_TEXTURE_2D)
    glColor3f(1, 1, 1)
    text_surface = game_font.render("[X] Toggle Icons", True, (255, 255, 255, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", 1)
    w, h = text_surface.get_width(), text_surface.get_height()
    
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    x_pos = start_x + (map_w / 2) - (w / 2)
    y_pos = start_y - h - 5
    
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x_pos, y_pos)
    glTexCoord2f(1, 0); glVertex2f(x_pos + w, y_pos)
    glTexCoord2f(1, 1); glVertex2f(x_pos + w, y_pos + h)
    glTexCoord2f(0, 1); glVertex2f(x_pos, y_pos + h)
    glEnd()
    glDeleteTextures(1, [tex_id])

    restore_perspective_projection()

def main():
    global wall_tex_id, floor_tex_id, eye_tex_id, trap_tex_id, maze_map, spheres, traps, powerups, pyramids, start_time, game_font, big_font, maze_display_list, show_minimap, show_legend, show_icons, game_over, final_time, blindness_active, speed_boost_active, speed_boost_end_time, launch_active, launch_start_time, slow_walk_active

    pygame.init()
    pygame.display.set_mode(DISPLAY_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Horror Maze")

    game_font = pygame.font.SysFont("Arial", 18, bold=True) 
    big_font = pygame.font.SysFont("Arial", 40, bold=True) 

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Init Fog
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 2.0)
    glFogf(GL_FOG_END, 15.0)
    
    # Init Light
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.05)
    
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (DISPLAY_SIZE[0]/DISPLAY_SIZE[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    wall_tex_id = load_image_texture(WALL_TEXTURE_FILE)
    floor_tex_id = load_image_texture(FLOOR_TEXTURE_FILE)
    eye_tex_id = load_image_texture(EYE_TEXTURE_FILE)
    trap_tex_id = load_image_texture(TRAP_TEXTURE_FILE) 

    maze_map = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)
    
    # Generate Objects sequentially to prevent overlap
    traps = place_random_traps(maze_map)
    occupied = set(traps) # Start tracking occupied spots
    
    powerups, occupied = place_random_powerups(maze_map, occupied)
    pyramids = place_random_pyramids(maze_map, occupied)
    spheres = place_random_eyes(maze_map) # Eyes are separate
    
    maze_display_list = create_maze_display_list() 
    start_time = time.time()
    
    player_x = 1 * 2
    player_z = 1 * 2
    player_yaw = 90

    clock = pygame.time.Clock()

    while True:
        if not game_over:
            current_time = time.time()
            elapsed = int(current_time - start_time)
        else:
            elapsed = final_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); return
                
                # Active controls
                if event.key == pygame.K_r:
                    player_x = 2
                    player_z = 2
                    player_yaw = 90
                    start_time = time.time()
                    game_over = False 
                    blindness_active = False
                    speed_boost_active = False
                    launch_active = False
                    slow_walk_active = False
                
                if event.key == pygame.K_g:
                    maze_map = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)
                    
                    traps = place_random_traps(maze_map)
                    occupied = set(traps)
                    powerups, occupied = place_random_powerups(maze_map, occupied)
                    pyramids = place_random_pyramids(maze_map, occupied)
                    spheres = place_random_eyes(maze_map)
                    
                    maze_display_list = create_maze_display_list() 
                    player_x = 2
                    player_z = 2
                    player_yaw = 90
                    start_time = time.time()
                    game_over = False
                    blindness_active = False
                    speed_boost_active = False
                    launch_active = False
                    slow_walk_active = False
                
                if event.key == pygame.K_m:
                    show_minimap = not show_minimap
                
                if event.key == pygame.K_x:
                    show_icons = not show_icons
                
                if event.key == pygame.K_z:
                    slow_walk_active = not slow_walk_active
                
                # Toggle Legend
                if event.key == pygame.K_l:
                    show_legend = not show_legend

        # Movement
        if not game_over and not launch_active:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: player_yaw -= TURN_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player_yaw += TURN_SPEED

            # Check Powerup Collision
            for p in powerups[:]:
                dist_p = math.sqrt((player_x - p[0])**2 + (player_z - p[1])**2)
                if dist_p < 0.5:
                    powerups.remove(p)
                    speed_boost_active = True
                    speed_boost_end_time = time.time() + 2
            
            # Check Pyramid Collision
            for p in pyramids[:]:
                dist_p = math.sqrt((player_x - p[0])**2 + (player_z - p[1])**2)
                if dist_p < 0.5:
                    pyramids.remove(p)
                    launch_active = True
                    launch_start_time = time.time()

            current_speed = MOVE_SPEED
            
            # Apply modifiers
            if speed_boost_active:
                current_speed = MOVE_SPEED * 2.0 
                if time.time() > speed_boost_end_time:
                    speed_boost_active = False
            else:
                grid_x = int(round(player_x / 2))
                grid_z = int(round(player_z / 2))
                if (grid_z, grid_x) in traps:
                    current_speed = MOVE_SPEED * 0.3 
            
            # Apply Slow Walk
            if slow_walk_active:
                current_speed *= 0.5

            dx = math.sin(math.radians(player_yaw)) * current_speed
            dz = -math.cos(math.radians(player_yaw)) * current_speed
            buffer = 0.25 

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                next_x = player_x + dx; next_z = player_z + dz
                check_x = next_x + math.copysign(buffer, dx); check_z = next_z + math.copysign(buffer, dz)
                if maze_map[int(round(check_z/2))][int(round(check_x/2))] != 1:
                    player_x = next_x; player_z = next_z

            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                next_x = player_x - dx; next_z = player_z - dz
                check_x = next_x - math.copysign(buffer, dx); check_z = next_z - math.copysign(buffer, dz)
                if maze_map[int(round(check_z/2))][int(round(check_x/2))] != 1:
                    player_x = next_x; player_z = next_z
            
            # Teleport
            for sphere in spheres:
                sx, sz = sphere[0], sphere[1]
                dist_eye = math.sqrt((player_x - sx)**2 + (player_z - sz)**2)
                
                if dist_eye < 0.5 and not blindness_active:
                    blindness_active = True
                    blindness_start_time = time.time()
                    new_x, new_z = get_random_spawn(maze_map)
                    player_x, player_z = new_x, new_z

        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))
        
        # Use bright map view when launched
        if launch_active:
            glFogfv(GL_FOG_COLOR, (0, 0, 0, 1))
            glFogf(GL_FOG_START, 20.0) # Push fog back
            glFogf(GL_FOG_END, 60.0) 
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1.0))
            glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        else:
            glFogfv(GL_FOG_COLOR, (0, 0, 0, 1)) 
            glFogf(GL_FOG_START, 2.0)
            glFogf(GL_FOG_END, 15.0)
            glLightfv(GL_LIGHT0, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0)) 
            glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.7, 0.6, 1.0)) 

        cam_y = 0.0
        if launch_active:
            # Launch: 4 seconds
            t = time.time() - launch_start_time
            if t < 0.5:
                cam_y = (t / 0.5) * 20.0
            elif t < 3.5:
                cam_y = 20.0
            elif t < 4.0:
                cam_y = 20.0 - ((t - 3.5) / 0.5) * 20.0
            else:
                launch_active = False
                cam_y = 0.0

        target_x = player_x + math.sin(math.radians(player_yaw))
        target_z = player_z - math.cos(math.radians(player_yaw))
        gluLookAt(player_x, cam_y, player_z, target_x, 0, target_z, 0, 1, 0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1, 1, 1) 
        glEnable(GL_TEXTURE_2D)
        
        draw_floor()
        draw_traps() 
        glCallList(maze_display_list)
        draw_spheres(player_x, player_z, player_yaw)
        draw_powerups() 
        draw_pyramids() # Draw Pyramids
        
        # Diamond
        dia_x, dia_z = draw_diamond()
        
        # Collision
        dist_to_diamond = math.sqrt((player_x - dia_x)**2 + (player_z - dia_z)**2)
        if dist_to_diamond < 0.5 and not game_over:
            game_over = True
            final_time = elapsed

        draw_hud_menu(elapsed, player_x, player_z)
        draw_minimap(player_x, player_z)
        draw_legend() 
        draw_blindness_effect()
        
        if game_over:
            draw_victory_screen()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()