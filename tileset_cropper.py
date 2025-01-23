from PIL import Image
import os

def divide_tilemap(tilemap_path, tile_size=(16, 16)):
    # Open the tilemap image
    tilemap = Image.open(tilemap_path)
    
    # Get the base filename and create the output directory
    base_filename = os.path.splitext(os.path.basename(tilemap_path))[0]
    output_dir = os.path.join(os.path.dirname(tilemap_path), base_filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the dimensions of the tilemap
    tilemap_width, tilemap_height = tilemap.size
    tile_width, tile_height = tile_size
    
    # Loop through the tilemap and crop the individual tiles
    for row in range(0, tilemap_height, tile_height):
        for col in range(0, tilemap_width, tile_width):
            # Define the bounding box for each tile
            bbox = (col, row, col + tile_width, row + tile_height)
            tile = tilemap.crop(bbox)
            
            # Create the filename for the tile (row_column.png)
            tile_filename = f"{row // tile_height}_{col // tile_width}.png"
            tile_path = os.path.join(output_dir, tile_filename)
            
            # Save the tile
            tile.save(tile_path)

    print(f"Tiles saved to: {output_dir}")

# Input: Path to the tilemap PNG
tilemap_path = input("Enter the path to the PNG tilemap: ")
divide_tilemap(tilemap_path)
