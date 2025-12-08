import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# --- CONFIGURATION ---
DISPLAY_SIZE = (800, 600)
WALL_HEIGHT = 1.0
MOVE_SPEED = 0.1
TURN_SPEED = 2.0

# improting texture files for walls and floor
WALL_TEXTURE_FILE = "brown_age_by_darkwood67.jpg"
FLOOR_TEXTURE_FILE = "old_paper_by_darkwood67.jpg"

# 1 = Wall, 0 = Path, 2 = Start
maze_map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 1, 1, 1, 0, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 0, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# --- CUBE DATA ---
vertices = (
    (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
    (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
)

surfaces = (
    (0,1,2,3), (3,2,7,6), (6,7,5,4), 
    (4,5,1,0), (1,5,7,2), (4,0,3,6)
)

tex_coords = (
    (0,0), (1,0), (1,1), (0,1)
)

# Global variables to store texture IDs
wall_tex_id = None
floor_tex_id = None

def load_image_texture(filename):
    """ Loads an image file and converts it to an OpenGL texture ID """
    try:
        textureSurface = pygame.image.load(filename)
    except pygame.error as e:
        print(f"Error loading {filename}: {e}")
        print("Make sure the image file is in the same folder as this script!")
        pygame.quit()
        quit()

    textureData = pygame.image.tostring(textureSurface, "RGB", 1)
    width = textureSurface.get_width()
    height = textureSurface.get_height()

    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, textureData)

    # Set texture parameters to repeat (essential for the floor)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) # Linear looks smoother
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    
    return texid

def draw_cube():
    """ Draws a single textured cube using the currently bound texture """
    glBegin(GL_QUADS)
    for surface in surfaces:
        for i, vertex in enumerate(surface):
            glTexCoord2fv(tex_coords[i])
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_maze():
    """ Loops through the map and draws walls """
    glBindTexture(GL_TEXTURE_2D, wall_tex_id) # Bind the Wall Texture
    
    rows = len(maze_map)
    cols = len(maze_map[0])
    
    for r in range(rows):
        for c in range(cols):
            if maze_map[r][c] == 1:
                glPushMatrix()
                # Translate to grid position (c = x, r = z)
                glTranslatef(c * 2, 0, r * 2) 
                draw_cube()
                glPopMatrix()

def draw_floor():
    """ Draws a large quad for the ground with the floor texture """
    glBindTexture(GL_TEXTURE_2D, floor_tex_id)
    tile_count = 100 
    
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(-100, -1, -100)
    
    glTexCoord2f(tile_count, 0)
    glVertex3f(100, -1, -100)
    
    glTexCoord2f(tile_count, tile_count)
    glVertex3f(100, -1, 100)
    
    glTexCoord2f(0, tile_count)
    glVertex3f(-100, -1, 100)
    glEnd()

def main():
    global wall_tex_id, floor_tex_id
    
    pygame.init()
    pygame.display.set_mode(DISPLAY_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Textured Maze Game")

    # OpenGL Setup
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    
    # Perspective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (DISPLAY_SIZE[0]/DISPLAY_SIZE[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    # Load Textures
    wall_tex_id = load_image_texture(WALL_TEXTURE_FILE)
    floor_tex_id = load_image_texture(FLOOR_TEXTURE_FILE)

    # Player State
    player_x = 1 * 2 
    player_z = 1 * 2
    player_yaw = 90 # Angle in degrees

    clock = pygame.time.Clock()

    while True:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

        # Input & Movement
        keys = pygame.key.get_pressed()
        
        # Rotation
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_yaw -= TURN_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_yaw += TURN_SPEED

        # Calculate Movement Vector
        dx = math.sin(math.radians(player_yaw)) * MOVE_SPEED
        dz = -math.cos(math.radians(player_yaw)) * MOVE_SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            next_x = player_x + dx
            next_z = player_z + dz
            grid_x = int(round(next_x / 2))
            grid_z = int(round(next_z / 2))
            if maze_map[grid_z][grid_x] != 1:
                player_x = next_x
                player_z = next_z

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            next_x = player_x - dx
            next_z = player_z - dz
            grid_x = int(round(next_x / 2))
            grid_z = int(round(next_z / 2))
            if maze_map[grid_z][grid_x] != 1:
                player_x = next_x
                player_z = next_z

        # Camera Update
        glLoadIdentity()
        target_x = player_x + math.sin(math.radians(player_yaw))
        target_z = player_z - math.cos(math.radians(player_yaw))
        gluLookAt(player_x, 0, player_z, target_x, 0, target_z, 0, 1, 0)

        # Render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glColor3f(1, 1, 1) 
        
        draw_floor()
        draw_maze()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()