import random
import json
import pygame
from pygame.locals import *
from OpenGL.GL import *

from PIL import Image
import numpy as np
from perlin_noise import PerlinNoise

from objects import *

# Define the tile registry
tile_registry = {
    "grass": "assets/textures/grass.png",
    "ground": "assets/textures/ground.png",
    "stone": "assets/textures/stone.png"
}

# Load a texture from a file
def load_texture(file):
    texture_surface = pygame.image.load(file)
    texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
    width, height = texture_surface.get_size()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    return texture, width, height

def generate_terrain(width, height, biome, output_file):
    terrain = {
        "biome": biome,
        "tiles": []
    }

    for y in range(height):
        for x in range(width):
            tile_id = random.choice(list(tile_registry.keys()))  # Randomly choose a tile ID
            terrain["tiles"].append({
                "id": tile_id,
                "pos": [x, y]
            })

    # Save terrain to a JSON file
    with open(output_file, 'w') as f:
        json.dump(terrain, f, indent=4)

    print(f"Terrain generated and saved to {output_file}")



# Generate terrain using Perlin Noise
def generate_terrain_with_noise(width, height, biome, output_file):
    # terrain = {
    #     "biome": biome,
    #     "tiles": []
    # }

    # # Parameters for Perlin noise
    # scale = 100.0
    # octaves = 6
    # persistence = 0.5
    # lacunarity = 2.0

    # for y in range(height):
    #     for x in range(width):
    #         # Generate a height value using Perlin noise
    #         block_value = noise.pnoise2(x / scale, y / scale, octaves=octaves, persistence=persistence, lacunarity=lacunarity, repeatx=width, repeaty=height, base=0)

    #         # Normalize the height value to be between 0 and 1
    #         height_value = (height_value + 1) / 2

    #         # Determine the tile based on the height value
    #         if height_value > 0.7:
    #             tile_id = "grass"
    #         elif height_value > 0.4:
    #             tile_id = "ground"
    #         else:
    #             tile_id = "stone"

    #         terrain["tiles"].append({
    #             "id": tile_id,
    #             "pos": [x, y]
    #         })

    
    # # Save terrain to a JSON file
    # with open(output_file, 'w') as f:
    #     json.dump(terrain, f, indent=4)
    pass



def generate_platforms(platform_height=2):
    # Parameters
    octaves = 4 # Higher octaves for smoother noise
    seed = 1
    scale = 100  # Smaller scale for larger, smoother features
    persistence = 0.5  # Lower persistence for smoother features
    lacunarity = 2.0  # Standard lacunarity for typical Perlin noise

    # Create Perlin noise generator
    caves = PerlinNoise(octaves=octaves, seed=seed)
    land_limiter = PerlinNoise(octaves=octaves+2, seed=seed+1)

    # Generate a heightmap with Perlin noise
    width, height = 100, 100
    heightmap = np.zeros(((height, width, 4)))
    heightline = np.zeros(width)

    for y in range(height):
        for x in range(width):
            nx = x / scale
            ny = y / scale
            heightline[x] = sum((land_limiter([nx, quality])) for quality in range(10))
            heightmap[y, x, :] = caves([nx, ny])


    # Normalize the heightmap to the range [0, 255] for image saving
    heightmap = ((heightmap - heightmap.min()) / (heightmap.max() - heightmap.min()) * 255).astype(np.uint8)
    heightline = ((heightline - heightline.min()) / (heightline.max() - heightline.min()) * height/10).astype(np.uint8)

    heightmap = ((np.array([heightmap,heightmap,heightmap,heightmap])))
    # heightmap = 255 - heightmap  # Invert to make higher values represent higher platforms
    
    # for x in range(width):
    #     for y in range(height):
    #         if heightline[x] > y or (heightmap[y, x] < 100 and abs(y - heightline[x]) > height/10):
    #             heightmap[y, x] = 0
    #         else: heightmap[y, x] = 255


    # for y in range(height):
    #     for x in range(width):
    #         heightmap[x, y] = ((heightmap[x, y] - 128) / 128.0) * platform_height if heightmap[x, y] > 127 else 0

    # platforms = np.zeros_like(heightmap)

    # for y in range(width):
    #     h = max(heightmap[y, :])
    #     for x in range(int(height/2 - h), height):
    #         platforms[x, y] = 255


    # Save the heightmap as an image
    image = Image.fromarray(heightmap, mode='RGBA')
    image.save('terrain.png')

# Generate platform terrain
platforms = generate_platforms(20)

def load_terrain(input_file):
    with open(input_file, 'r') as f:
        terrain = json.load(f)

    game_objects = []

    for tile in terrain['tiles']:
        tile_id = tile['id']
        pos = tile['pos']

        if tile_id in tile_registry:
            texture, width, height = load_texture(tile_registry[tile_id])
            game_object = GameObject(pos[0] * width, pos[1] * height, width, height, texture, 1, False)
            game_objects.append(game_object)

    return game_objects

