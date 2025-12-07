# Starting file

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

# 1 = Wall, 0 = Path, 2 = Start
# will replace with random generator later
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

# --- CUBE DATA (Vertices & Texture Coords) ---
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

def create_dummy_texture():
    """
    Generates a simple 64x64 checkerboard texture byte array
    """
    textureData = []
    for i in range(64):
        for j in range(64):
            if (i // 8 + j // 8) % 2 == 0:
                textureData.extend([255, 255, 255]) # White
            else:
                textureData.extend([100, 100, 255]) # Blueish
    
    # Convert to bytes
    return bytes(textureData)

def load_texture():
    """ Load the texture into OpenGL """
    textureData = create_dummy_texture()
    width = 64
    height = 64

    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texid)
    # Note: GL_RGB because our dummy texture has 3 channels
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, textureData)

    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    return texid

def draw_cube():
    """ Draws a single textured cube """
    glBegin(GL_QUADS)
    for surface in surfaces:
        for i, vertex in enumerate(surface):
            glTexCoord2fv(tex_coords[i])
            glVertex3fv(vertices[vertex])
    glEnd()

def draw_maze():
    """ Loops through the map and draws walls where '1' is found """
    rows = len(maze_map)
    cols = len(maze_map[0])
    
    for r in range(rows):
        for c in range(cols):
            if maze_map[r][c] == 1:
                glPushMatrix()
                glTranslatef(c * 2, 0, r * 2) 
                draw_cube()
                glPopMatrix()

def draw_floor():
    """ Draws a large quad for the ground """
    glDisable(GL_TEXTURE_2D) # Turn off texture for the floor (or load a new one)
    glColor3f(0.2, 0.2, 0.2) # Dark Gray
    glBegin(GL_QUADS)
    glVertex3f(-100, -1, -100)
    glVertex3f(100, -1, -100)
    glVertex3f(100, -1, 100)
    glVertex3f(-100, -1, 100)
    glEnd()
    glEnable(GL_TEXTURE_2D) # Turn texture back on for walls
    glColor3f(1, 1, 1) # Reset color to white

def main():
    pygame.init()
    pygame.display.set_mode(DISPLAY_SIZE, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Maze HW Starter")

    # OpenGL Setup
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    
    # Perspective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (DISPLAY_SIZE[0]/DISPLAY_SIZE[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

    # Load Texture
    load_texture()

    # Player State
    # Start at (1, 1) in grid coords. 
    # Since cubes are width 2, real world position is grid * 2.
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
        # OpenGL uses Radians. 
        # sin/cos logic depends on how your 0 angle is aligned. 
        dx = math.sin(math.radians(player_yaw)) * MOVE_SPEED
        dz = -math.cos(math.radians(player_yaw)) * MOVE_SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            # Predict next position
            next_x = player_x + dx
            next_z = player_z + dz
            
            # Convert world coord to grid coord (divide by 2, round)
            grid_x = int(round(next_x / 2))
            grid_z = int(round(next_z / 2))

            # Collision Check
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
        
        # Calculate target (where we are looking)
        target_x = player_x + math.sin(math.radians(player_yaw))
        target_z = player_z - math.cos(math.radians(player_yaw))

        # gluLookAt(EyeX, EyeY, EyeZ,  TargetX, TargetY, TargetZ,  UpX, UpY, UpZ)
        gluLookAt(player_x, 0, player_z, target_x, 0, target_z, 0, 1, 0)

        # Render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        draw_floor()
        draw_maze()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()