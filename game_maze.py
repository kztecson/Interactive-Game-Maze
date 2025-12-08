import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import time

# Config
DISPLAY_SIZE = (800, 600)
MAZE_WIDTH = 12 
MAZE_HEIGHT = 12 
MOVE_SPEED = 0.1
TURN_SPEED = 2.0

# Textures
WALL_TEXTURE_FILE = "brown_age_by_darkwood67.jpg"
FLOOR_TEXTURE_FILE = "old_paper_by_darkwood67.jpg"
EYE_TEXTURE_FILE = "ZEGAME_OLHO.png" 

# Globals
maze_map = []
spheres = []
start_time = 0
final_time = 0
game_over = False 
game_font = None 
big_font = None 
maze_display_list = None
show_minimap = False 
diamond_rot = 0 

# Generate Maze
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
            if maze[r][c] in [0, 2, 3]: 
                if random.random() < 0.05: 
                    eye_list.append((c * 2, r * 2))
    return eye_list

# Cube Data
vertices = ((1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
            (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1))
surfaces = ((0,1,2,3), (3,2,7,6), (6,7,5,4), (4,5,1,0), (1,5,7,2), (4,0,3,6))
normals = ((0, 0, -1), (-1, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0), (0, -1, 0))
tex_coords = ((0,0), (1,0), (1,1), (0,1))

wall_tex_id = None
floor_tex_id = None
eye_tex_id = None

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

def draw_spheres(player_x, player_z):
    glBindTexture(GL_TEXTURE_2D, eye_tex_id)
    quadric = gluNewQuadric()
    gluQuadricTexture(quadric, GL_TRUE)
    for (sx, sz) in spheres:
        glPushMatrix()
        glTranslatef(sx, -0.3, sz)
        dx = player_x - sx
        dz = player_z - sz
        angle = math.degrees(math.atan2(dx, dz)) + 180
        glRotatef(angle, 0, 1, 0)
        glRotatef(90, 1, 0, 0)
        gluSphere(quadric, 0.3, 32, 32)
        glPopMatrix()

def draw_diamond():
    """ Draws a glowing red diamond at the finish """
    global diamond_rot
    diamond_rot = (diamond_rot + 2) % 360
    
    # Find finish
    finish_r = len(maze_map) - 2
    finish_c = len(maze_map[0]) - 2
    
    x = finish_c * 2
    z = finish_r * 2
    
    glPushMatrix()
    glTranslatef(x, 0, z) 
    glRotatef(diamond_rot, 0, 1, 0) 
    glScalef(0.5, 0.5, 0.5) 

    glDisable(GL_TEXTURE_2D)
    
    # Red Glow and Color
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.8, 0.0, 0.0, 1]) 
    glColor3f(0.8, 0.0, 0.0) 

    # Draw Octahedron
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

    # Reset Emission
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

# --- 2D UI ---

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
    
    menu_w, menu_h, margin = 220, 160, 20
    
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

    lines = [f"Time: {elapsed}s", f"Pos: {int(px/2)}, {int(pz/2)}", "----------------", "[R] Reset", "[G] New Maze", "[M] Toggle Map"]
    
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

def draw_victory_screen():
    set_ortho_projection()
    
    # Darken Background
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
    glColor3f(0.8, 0.0, 0.0) # Red Text for victory
    
    center_x = DISPLAY_SIZE[0] / 2
    start_y = DISPLAY_SIZE[1] / 2 + 100
    
    for i, line in enumerate(lines):
        font = big_font if i == 0 else game_font
        # Title is Red, rest is White
        color = (200, 0, 0, 255) if i == 0 else (255, 255, 255, 255)
        
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
    glColor4f(0.85, 0.75, 0.55, 0.9) 
    glBegin(GL_QUADS)
    glVertex2f(start_x - 5, start_y - 5); glVertex2f(start_x + map_w + 5, start_y - 5)
    glVertex2f(start_x + map_w + 5, start_y + map_h + 5); glVertex2f(start_x - 5, start_y + map_h + 5)
    glEnd()
    
    glColor4f(0.3, 0.2, 0.1, 1.0) 
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(start_x - 5, start_y - 5); glVertex2f(start_x + map_w + 5, start_y - 5)
    glVertex2f(start_x + map_w + 5, start_y + map_h + 5); glVertex2f(start_x - 5, start_y + map_h + 5)
    glEnd()

    rows = len(maze_map)
    cols = len(maze_map[0])
    
    glBegin(GL_QUADS)
    for r in range(rows):
        for c in range(cols):
            cell_type = maze_map[r][c]
            
            if cell_type == 1: glColor3f(0.35, 0.25, 0.15) 
            elif cell_type == 2: glColor3f(0, 0.5, 0) 
            elif cell_type == 3: glColor3f(0.8, 0.2, 0.2) 
            else: continue 
            
            x = start_x + (c * cell_size)
            y = start_y + ( (rows - 1 - r) * cell_size ) 
            glVertex2f(x, y); glVertex2f(x + cell_size, y); glVertex2f(x + cell_size, y + cell_size); glVertex2f(x, y + cell_size)
    glEnd()
    
    player_grid_x = px / 2
    player_grid_z = pz / 2
    p_x = start_x + (player_grid_x * cell_size)
    p_y = start_y + ((rows - 1 - player_grid_z) * cell_size)
    
    glColor3f(0.9, 0, 0) 
    glBegin(GL_QUADS)
    glVertex2f(p_x - 1, p_y - 1); glVertex2f(p_x + cell_size + 1, p_y - 1)
    glVertex2f(p_x + cell_size + 1, p_y + cell_size + 1); glVertex2f(p_x - 1, p_y + cell_size + 1)
    glEnd()

    restore_perspective_projection()

def main():
    global wall_tex_id, floor_tex_id, eye_tex_id, maze_map, spheres, start_time, game_font, big_font, maze_display_list, show_minimap, game_over, final_time

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
    
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (0, 0, 0, 1))
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 2.0)
    glFogf(GL_FOG_END, 15.0)
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.1, 0.1, 0.1, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.7, 0.6, 1.0))
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.05)
    
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (DISPLAY_SIZE[0]/DISPLAY_SIZE[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    wall_tex_id = load_image_texture(WALL_TEXTURE_FILE)
    floor_tex_id = load_image_texture(FLOOR_TEXTURE_FILE)
    eye_tex_id = load_image_texture(EYE_TEXTURE_FILE)

    maze_map = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)
    spheres = place_random_eyes(maze_map)
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
                
                if event.key == pygame.K_g:
                    maze_map = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)
                    spheres = place_random_eyes(maze_map)
                    maze_display_list = create_maze_display_list() 
                    player_x = 2
                    player_z = 2
                    player_yaw = 90
                    start_time = time.time()
                    game_over = False
                
                if event.key == pygame.K_m:
                    show_minimap = not show_minimap

        # Movement
        if not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: player_yaw -= TURN_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player_yaw += TURN_SPEED

            dx = math.sin(math.radians(player_yaw)) * MOVE_SPEED
            dz = -math.cos(math.radians(player_yaw)) * MOVE_SPEED
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

        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))
        
        target_x = player_x + math.sin(math.radians(player_yaw))
        target_z = player_z - math.cos(math.radians(player_yaw))
        gluLookAt(player_x, 0, player_z, target_x, 0, target_z, 0, 1, 0)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glColor3f(1, 1, 1) 
        glEnable(GL_TEXTURE_2D)
        
        draw_floor()
        glCallList(maze_display_list)
        draw_spheres(player_x, player_z)
        
        # Diamond
        dia_x, dia_z = draw_diamond()
        
        # Collision
        dist_to_diamond = math.sqrt((player_x - dia_x)**2 + (player_z - dia_z)**2)
        if dist_to_diamond < 0.5 and not game_over:
            game_over = True
            final_time = elapsed

        draw_hud_menu(elapsed, player_x, player_z)
        draw_minimap(player_x, player_z)
        
        if game_over:
            draw_victory_screen()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()