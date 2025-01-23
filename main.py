import pygame
from pygame.locals import *
from OpenGL.GL import *
import json
import os
import random
from pygame.mixer import *

# modules
from globals import *
from objects import *


# variables
screenWidth = INITIAL_SCREEN_WIDTH
screenHeight = INITIAL_SCREEN_HEIGHT
groundLevel = INITIAL_GROUND_LEVEL
scale = 1.0

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
pygame.display.set_caption('Her Land')
icon = pygame.image.load('assets/icon.png') 
pygame.display.set_icon(icon)

# Initialize Pygame clock
clock = pygame.time.Clock()

# Enable blending to handle transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glBlendColor(1.0, 1.0, 1.0, 1.0)
glEnable(GL_TEXTURE_2D)


# Function to set up OpenGL with the current screen size
def setup_screen(width, height, sceneWidth, sceneHeight):
    global screen, groundLevel, screenWidth, screenHeight, camera
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
    ratio = width / height
    camera.scale = int(width / sceneWidth if ratio < 1 else height / sceneHeight)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_TEXTURE_2D)
    groundLevel = 0.65 * sceneHeight
    screenWidth = width
    screenHeight = height
    camera.updateBounds(screenWidth, screenHeight)



def play_sound(filename):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

DEBUG_FONT_SIZE = 18
font = pygame.font.Font("assets/fonts/elemental.ttf", DEBUG_FONT_SIZE)                                       

def drawText(x, y, text, color):         
    text_surface = font.render(text, True, color)
    texture_id, text_width, text_height = surface_to_texture(text_surface)
    start = vec2(x, y)
    end = start + vec2(text_width, text_height)
    draw_quad(texture_id, matrices["normal"], start, end)

# Render your debug info with OpenGL
def draw_debug_info():
    color = (255, 255, 255, 255)
    text = [
        f"FPS: {clock.get_fps():.2f}",
        f"pos: [x: {player.position.x:.0f} y: {player.position.y:.0f}]",
    ]
    for i in range(0, len(text)):
        drawText(4, 4 + i * DEBUG_FONT_SIZE, text[i], color) 


def surface_to_texture(text_surface):
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    width, height = text_surface.get_size()

    # Generate a new texture ID
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # Upload the texture data
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    return texture_id, width, height


def create_test_texture(color=(255, 0, 0, 255)):
    texture_surface = pygame.Surface((64, 64))
    texture_surface.fill(color)
    texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
    width, height = texture_surface.get_size()
    
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    
    return texture, width, height

test_texture = create_test_texture()

# Helper function to load textures
def load_texture(file):
    try:
        texture_surface = pygame.image.load(file)
        texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
        width, height = texture_surface.get_size()
        
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        
        print(f"Loaded texture: {file} ({width}x{height})")
        return texture, width, height
    except pygame.error as e:
        print(f"Failed to load texture: {file} - {e}")
        return test_texture


# Load texture paths from JSON
def load_textures_from_json(json_file):
    with open(json_file) as f:
        texture_map = json.load(f)

    textures = {}
    for key, value in texture_map.items():
        if isinstance(value, dict):
            textures[key] = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    textures[key][sub_key] = []
                    for entry in sub_value:
                        textures[key][sub_key].append(load_texture(os.path.join('assets/textures', entry)))
                else:
                    textures[key][sub_key] = load_texture(os.path.join('assets/textures', sub_value))

        else:
            textures[key] = load_texture(os.path.join('assets/textures', value))

    return textures

# Load sound paths from JSON
def load_sounds_from_json(json_file):
    with open(json_file) as f:
        sound_map = json.load(f)

    sounds = {}
    for key, value in sound_map.items():
        if isinstance(value, dict):
            sounds[key] = {}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    sounds[key][sub_key] = []
                    for entry in sub_value:
                        sounds[key][sub_key].append(os.path.join('assets/sounds', entry))
                else:
                    sounds[key][sub_key] = os.path.join('assets/sounds', sub_value)

        else:
            sounds[key] = os.path.join('assets/sounds', value)

    return sounds

# Load data from the JSON file
textures = load_textures_from_json('assets/textures.json')
sounds = load_sounds_from_json('assets/sounds.json')

# biome_name = random.choice(list(textures['background'].keys()))
biome_name = "star_meadow"
bg_source = textures['background'][biome_name]

biome_background_music = sounds["background_music"][biome_name]

background_layers = [BackgroundLayer(bg_source[i], speed = 1 - 1 / (i + 1), layer = i - len(bg_source)) for i in range(0, len(bg_source), 1)]

sceneWidth = background_layers[0].width
sceneHeight = background_layers[0].height

camera = Camera()

setup_screen(screenWidth, screenHeight, sceneWidth, sceneHeight)


player = PlayerObject(0, - textures['player'][2] * 2, textures['player'][1], textures['player'][2], textures['player'][0], 0, True)

ground_tiles = [[]]

# for x in range(-20, 20):
#     for y in range(0, 15):
#         tile_type = 'dirt'
#         if y == 0:
#             tile_type = 'grass'
#         if y > 6:
#             tile_type = 'stone'
#         ground_tiles.append(TileObject(x, y, textures['tiles'][tile_type][0], 1, tile_type))

# chunk_0_0 = [[TileObject(x, y, textures['tiles']["ground"][0], 1, "ground") for x in range(0, 15)] for y in range(0, 15)]
# map = [[None for _ in range(0, 7)] for _ in range(0, 7)]
# map[0][0] = chunk_0_0

# for u in range(0, 127):
#     for v in range(0, 127):          
#         cx, cy = int(u/8), int(v/8)
#         x, y = u%16, v%16
#         neighbours = [0,0,0,0] 
#         if(y > 0):   neighbours[0] = int(bool(map[cx][cy][x    ][y - 1]))
#         if(x > 0):   neighbours[1] = int(bool(map[cx][cy][x - 1][y    ]))
#         if(y < 127): neighbours[2] = int(bool(map[cx][cy][x    ][y + 1]))
#         if(x < 127): neighbours[3] = int(bool(map[cx][cy][x + 1][y    ]))
#         map[cx][cy][x][y].update_state(neighbours)


class MapManager:
    def __init__(self, map_size, chunk_size, textures):
        self.map_size = map_size
        self.chunk_size = chunk_size
        self.textures = textures
        self.map = [[None for _ in range(map_size)] for _ in range(map_size)]
        self.initialize_chunks()
    
    def initialize_chunks(self):
        # Initialize map with chunks of tiles
        for cx in range(self.map_size):
            for cy in range(self.map_size):
                self.map[cx][cy] = [[TileObject(x, y, self.textures['tiles']["ground"][0], 1, "ground") 
                                     for x in range(self.chunk_size)] 
                                     for y in range(self.chunk_size)]
    
    def get_tile(self, global_x, global_y):
        # Compute chunk and local tile coordinates
        cx, cy = global_x // self.chunk_size, global_y // self.chunk_size
        lx, ly = global_x % self.chunk_size, global_y % self.chunk_size
        return self.map[cx][cy][lx][ly]


    def update_tile(self, global_x, global_y):
        # Compute chunk and local tile coordinates
        cx, cy = global_x // self.chunk_size, global_y // self.chunk_size
        lx, ly = global_x % self.chunk_size, global_y % self.chunk_size
        
        # Get neighbor presence array
        neighbors = self.get_neighbors(cx, cy, lx, ly)
        
        # Update tile texture based on neighbors
        tile = self.map[cx][cy][lx][ly]
        tile.update_state(neighbors)
    
    def get_neighbors(self, cx, cy, lx, ly):
        # Determine neighbor presence: [top, left, bottom, right]
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]  # N, W, S, E
        neighbors = [0, 0, 0, 0]
        
        for i, (dx, dy) in enumerate(directions):
            nx, ny = lx + dx, ly + dy
            ncx, ncy = cx, cy
            
            # Adjust chunk index if neighbor goes out of bounds
            if nx < 0:
                ncx -= 1
                nx = self.chunk_size - 1
            elif nx >= self.chunk_size:
                ncx += 1
                nx = 0
            if ny < 0:
                ncy -= 1
                ny = self.chunk_size - 1
            elif ny >= self.chunk_size:
                ncy += 1
                ny = 0
            
            # Check if neighbor exists
            if 0 <= ncx < self.map_size and 0 <= ncy < self.map_size:
                neighbor_chunk = self.map[ncx][ncy]
                if neighbor_chunk is not None:
                    neighbors[i] = int(bool(neighbor_chunk[nx][ny]))
        
        return neighbors
    
    def update_chunk(self, chunk_x, chunk_y):
        # Update all tiles in the specified chunk
        for lx in range(self.chunk_size):
            for ly in range(self.chunk_size):
                self.update_tile(chunk_x * self.chunk_size + lx, chunk_y * self.chunk_size + ly)


# Create map manager
map_manager = MapManager(map_size=7, chunk_size=16, textures=textures)
map_manager.update_chunk(0, 0)

game_objects = [player]



# Load keybinds from JSON file
def load_keybinds(json_file):
    with open(json_file) as f:
        keybind_map = json.load(f)

    # Convert key names in the JSON file to Pygame key constants
    keybinds = {}
    for action, key_name in keybind_map.items():
        keybinds[action] = getattr(pygame, key_name)

    return keybinds

# Load keybinds from the JSON file
keybinds = load_keybinds('data/default_keybinds.json')

# Example of using the keybinds in your game loop
def handle_input(camera, player, interactable_objects, background_layers):
    keys = pygame.key.get_pressed()

    if keys[keybinds['move_left']]:
        player.move_left()
        for layer in background_layers:
            layer.scroll(-1, screenWidth)
        global follow_point
        camera.set_follow_point(FollowPoint.LEFT)

    if keys[keybinds['move_right']]:
        player.move_right() 
        for layer in background_layers:
            layer.scroll(1, screenWidth)
        camera.set_follow_point(FollowPoint.RIGHT)

    if keys[keybinds['jump']]:
        player.jump(interactable_objects)

    if keys[keybinds['crouch']]:
        player.crouch(True)
    else:
        player.crouch(False)
    
    if keys[keybinds['sprint']]:
        player.sprint()


# Main game loop
running = True

while running:
    dt = clock.tick() / 1000.0  # Конвертуємо час у секунди

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == VIDEORESIZE:
            # Handle window resize
            width, height = event.size
            setup_screen(width, height, sceneWidth, sceneHeight)

    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT)

    # Draw background layers
    for layer in sorted(background_layers, key = lambda l: l.layer):
        layer.scroll(0.5, screenWidth)
        layer.draw(screenWidth, screenHeight)


    current_regions = [int(player.position.x/10 + i) for i in range(-5, +5)]
    interactable_objects = []
    drawing_queue = []

    player_size = vec2(player.width, player.height)
    destination = vec2(2,2)*player.position - player.prev_position + player_size * 2
    
    for x in range(player.position.x - player_size.x, destination.x):
        for y in range(player.position.y - player_size.y, destination.y):
            tile = map_manager.get_tile(x, y)
            interactable_objects.append(tile)

            if camera.renderBounds.colliderect(tile.get_display_rect(camera)):
                drawing_queue.append(tile)

    if len(drawing_queue) > 0:
        drawing_queue.sort(key=lambda tile: tile.tile_type)
        prev_type = drawing_queue[0].tile_type
        glBindTexture(GL_TEXTURE_2D, drawing_queue[0].texture)
        glBegin(GL_QUADS)
        for tile in drawing_queue:
            if tile.tile_type != prev_type:
                glEnd()
                glBindTexture(GL_TEXTURE_2D, tile.texture)
                glBegin(GL_QUADS)
                prev_type = tile.tile_type
            start, end = tile.get_display_bounds(camera)
            set_quad(tile.get_uv_matrix(), start, end)
        glEnd()
            
    handle_input(camera, player, interactable_objects, background_layers)  
    player.update(interactable_objects, dt)
    camera.follow(player, dt)
    player.draw(camera)
    draw_debug_info()

    # Update display
    pygame.display.flip()

    if not pygame.mixer.music.get_busy():
        play_sound(random.choice(biome_background_music))

    # Limit the FPS
    clock.tick()

pygame.quit()
