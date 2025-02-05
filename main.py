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

import os
current_file_directory = os.path.dirname(os.path.abspath(__file__))
def get_abs_path(path):
    return (current_file_directory + "/" + path).replace("\\", "/").replace("//", "/")

# variables
screenWidth = INITIAL_SCREEN_WIDTH
screenHeight = INITIAL_SCREEN_HEIGHT
groundLevel = INITIAL_GROUND_LEVEL
scale = 1.0

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
pygame.display.set_caption('Her Land')
icon = pygame.image.load(get_abs_path('assets/icon.png')) 
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
    filename = get_abs_path(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

DEBUG_FONT_SIZE = 18
font = pygame.font.Font(get_abs_path('/assets/fonts/elemental.ttf'), DEBUG_FONT_SIZE)                                       

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
        f"pos: [x: {player.position.x/TILE_SIZE:.0f} y: {player.position.y/TILE_SIZE:.0f}]",
        f"vel: [x: {player.get_velocity().x:} y: {player.get_velocity().y:}]",
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
        file = get_abs_path(file)
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
    json_file = get_abs_path(json_file)

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
    json_file = get_abs_path(json_file)

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

# setup_screen(screenWidth, screenHeight, screenWidth, screenHeight)
# there will be a loading scree

def get_texture(texture_key):
    return textures[texture_key][0]

def draw(obj, camera):
    start, end = obj.get_display_bounds(camera)
    draw_quad(obj.texture, obj.get_uv(), start, end)

# Load data from the JSON file
textures = load_textures_from_json('assets/textures.json')
sounds = load_sounds_from_json('assets/sounds.json')

# biome_name = random.choice(list(textures['background'].keys()))
biome_name = "star_meadow"
bg_source = textures['background'][biome_name]

biome_background_music = sounds["background_music"][biome_name]

background_layers = [BackgroundLayer(bg_source[i], speed = 0.1*(1 - 1 / (i + 1)), layer = i - len(bg_source)) for i in range(0, len(bg_source), 1)]

sceneWidth = background_layers[0].width
sceneHeight = background_layers[0].height

camera = Camera()

setup_screen(screenWidth, screenHeight, sceneWidth, sceneHeight)



player = Player(TILE_SIZE, textures['player'][2]*-10, textures['player'][1], textures['player'][2], textures['player'][0], 0) 


# Create map manager
map_manager = MapManager(map_size=1, chunk_size=16, textures=textures)
map_manager.update_chunk(0, 0)

environment = Environment(map_manager)


# Load keybinds from JSON file
def load_keybinds(json_file):
    json_file = get_abs_path(json_file)

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
def handle_input(dt, camera, player, background_layers):
    keys = pygame.key.get_pressed()

    if keys[keybinds['move_left']]:
        player.move_left(dt)
        # for layer in background_layers:
        #     layer.scroll(-100*dt, screenWidth)
        # camera.set_follow_point(FollowPoint.LEFT)

    if keys[keybinds['move_right']]:
        player.move_right(dt) 
        # for layer in background_layers:
        #     layer.scroll(100*dt, screenWidth)
        # camera.set_follow_point(FollowPoint.RIGHT)

    if keys[keybinds['jump']]:
        player.jump()

    # if keys[keybinds['crouch']]:
    #     player.crouch(True)
    # else:
    #     player.crouch(False)
    
    # if keys[keybinds['sprint']]:
    #     player.sprint()



# Main game loop
running = True


# !!!!!
# threading
# for future, so game wont do unexpected things after window wasn't in focus
# !!!!!

# def game_logic_thread(running, client):
#     while running:
#         # Update game logic here
#         pass

# def game_render_thread(running, client):
#     while running:
#         # Render game here
#         pass

# threading.Thread(target=game_logic_thread, args=(running, client,), daemon=True).start()
# threading.Thread(target=game_render_thread, args=(running, client,), daemon=True).start()

selected_object = None
time_after_loading = 0
player_loaded = False
while running:
    dt = clock.tick() / 1000.0  # Конвертуємо час у секунди



        

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == VIDEORESIZE:
            # Handle window resize
            width, height = event.size
            setup_screen(width, height, sceneWidth, sceneHeight)

        if event.type == pygame.MOUSEBUTTONDOWN:  # Detect mouse button press
            mouse_x, mouse_y = pygame.mouse.get_pos()  # Get mouse position
            print(f"Mouse clicked at: ({mouse_x}, {mouse_y})")

            # Call a function with the coordinates
            def handle_click(x, y):
                print(f"Handling click at {x}, {y}")

            handle_click(mouse_x, mouse_y)

    # Clear the screen
    glClear(GL_COLOR_BUFFER_BIT)

    # Draw background layers
    for layer in sorted(background_layers, key = lambda l: l.layer):
        layer.scroll(camera.offset.x, screenWidth)
        layer.draw(camera, screenWidth, screenHeight)



    environment.update(dt, sub_steps=4)

    # Update the map
    cx, cy, lx, ly = map_manager.get_local_coords(player.position.x, player.position.y)
    map_manager.update_chunk(cx, cy)
    
    if lx < map_manager.chunk_size/2: 
        map_manager.update_chunk(cx - 1, cy)
    else: 
        map_manager.update_chunk(cx + 1, cy)

    if ly < map_manager.chunk_size/2: 
        map_manager.update_chunk(cx, cy - 1)
    else: 
        map_manager.update_chunk(cx, cy + 1)

    screen_size = vec2(screenWidth, screenHeight)
    start = vec2i.from_vec2(((vec2() - camera.offset) / TILE_SIZE) / camera.get_scale()) - vec2i(3, 3)
    end = vec2i.from_vec2(((screen_size - camera.offset) / TILE_SIZE) / camera.get_scale()) + vec2i(3, 3)
    # print(start, end)
    for x in range(start.x, end.x):
        for y in range(start.y, end.y):
            tile = map_manager.get_tile(x, y)
            if tile is not None:
                draw_quad(textures['tiles'][tile.tile_type][0], tile.get_uv(), *tile.get_display_bounds(camera))
            
    handle_input(dt, camera, player, background_layers)  
    # player.update(dt)

    if not player_loaded:
        if time_after_loading > 3:
            environment.add_body(player)
            player_loaded = True
        else:
            time_after_loading += dt
        camera.follow(map_manager.get_tile(0,0), dt)
    else:
        camera.follow(player, dt)


    for body in environment.bodies:
        draw(body, camera)

    mouse_pos = ((vec2(*pygame.mouse.get_pos()) - camera.offset) / TILE_SIZE) / camera.get_scale()
    mouse_pos = vec2i(math.floor(mouse_pos.x), math.floor(mouse_pos.y))
    selection_pos = mouse_pos
    
    selected_object = map_manager.get_tile(selection_pos.x, selection_pos.y)
    if selected_object is not None:
        start, end = selected_object.get_display_bounds(camera)
        draw_quad(textures["ui"]["selection"][0], matrices["normal"], start, end)
        draw_quad(textures["ui"]["selection"][0], matrices["reflected_vertical"], start, end)
        draw_quad(textures["ui"]["selection"][0], matrices["reflected_horisontal"], start, end)
        draw_quad(textures["ui"]["selection"][0], matrices["reflected_vertical_horisontal"], start, end)
    else :
        glColor(1,1,1,0.5)
        draw_quad(
            textures["tiles"]["ground"][0], 
            matrices["normal"], 
            vec2((selection_pos.x) * TILE_SIZE * camera.get_scale(), selection_pos.y * TILE_SIZE * camera.get_scale()), 
            vec2((selection_pos.x + 1) * TILE_SIZE * camera.get_scale(), (selection_pos.y + 1) * TILE_SIZE * camera.get_scale())
        )
        glColor(1,1,1,1)

    mouse_clicked = pygame.mouse.get_pressed()
    if mouse_clicked[0]:
        map_manager.set_tile(selection_pos.x, selection_pos.y, "ground")

    elif mouse_clicked[2] and selected_object is not None:
        map_manager.delete_tile(selection_pos.x, selection_pos.y)

    draw_debug_info()

    # Update display
    pygame.display.flip()

    if not pygame.mixer.music.get_busy():
        play_sound(random.choice(biome_background_music))

    # Limit the FPS
    # clock.tick()

pygame.quit()


