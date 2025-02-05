import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from enum import Enum
import numpy as np
import threading


from utilites import *
from globals import *


# class vec2:
#     def __init__(self, x=0.0, y=0.0):
#         self.x = x
#         self.y = y

#     def __add__(self, other):
#         return vec2(self.x + other.x, self.y + other.y)

#     def __sub__(self, other):
#         return vec2(self.x - other.x, self.y - other.y)

#     def __mul__(self, multiplier):
#         if isinstance(multiplier, vec2):
#             return vec2(self.x * multiplier.x, self.y * multiplier.y)
#         return vec2(self.x * multiplier, self.y * multiplier)


#     def length(self):
#         return np.sqrt(self.x ** 2 + self.y ** 2)

#     def normalized(self):
#         length = self.length()
#         if length > 0:
#             return vec2(self.x / length, self.y / length)
#         return vec2()
    

    
matrices = {
    "normal": [
        [0, 1],
        [1, 1],
        [1, 0],
        [0, 0]
    ],
    "reflected_vertical": [
        [1, 1],
        [0, 1],
        [0, 0],
        [1, 0]
    ],
    "reflected_horisontal": [
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1]
    ],
    "reflected_vertical_horisontal": [
        [1, 0],
        [0, 0],
        [0, 1],
        [1, 1]
    ]
}

def draw_quad(texture, matrix, start, end):
    glBindTexture(GL_TEXTURE_2D, texture)
    glBegin(GL_QUADS)
    glTexCoord2f(matrix[0][0], matrix[0][1]); glVertex2f(start.x, start.y)
    glTexCoord2f(matrix[1][0], matrix[1][1]); glVertex2f(end.x, start.y)
    glTexCoord2f(matrix[2][0], matrix[2][1]); glVertex2f(end.x, end.y)
    glTexCoord2f(matrix[3][0], matrix[3][1]); glVertex2f(start.x, end.y)
    glEnd()

def set_quad(matrix, start, end):
    glTexCoord2f(matrix[0][0], matrix[0][1]); glVertex2f(start.x, start.y)
    glTexCoord2f(matrix[1][0], matrix[1][1]); glVertex2f(end.x, start.y)
    glTexCoord2f(matrix[2][0], matrix[2][1]); glVertex2f(end.x, end.y)
    glTexCoord2f(matrix[3][0], matrix[3][1]); glVertex2f(start.x, end.y)


# -----------------------------
# Клас фізичного тіла
# -----------------------------
class RigidBody(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, texture, mass, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__()
        self.position = vec2(x, y)
        self.position_old = vec2(x, y)
        self.size = vec2(width, height)
        self.acceleration = vec2(0, 0)
        self.mass = mass
        self.gravity_enabled = gravity_enabled
        self.is_immovable = is_immovable
        self.is_physical = is_physical
        self.texture = texture
        self.rect = pygame.Rect(x, y, width, height)

    def apply_gravity(self, gravity=9.8*TILE_SIZE):
        if self.gravity_enabled: 
            self.accelerate(vec2(0, gravity))

    def accelerate(self, acc):
        self.acceleration += acc
        
    def get_velocity(self):
        return self.position - self.position_old

    def update_position(self, dt):
        if not self.is_immovable:
            velocity = self.get_velocity()
            self.position_old = self.position.copy()
            diff = velocity + (self.acceleration * dt * dt)
            # diff.x = diff.x % 10*TILE_SIZE 
            # diff.y = diff.y % 10*TILE_SIZE 
            if diff.x > 5*TILE_SIZE: diff.x = 5*TILE_SIZE
            if diff.y > 5*TILE_SIZE: diff.y = 5*TILE_SIZE
            if diff.x < -5*TILE_SIZE: diff.x = -5*TILE_SIZE
            if diff.y < -5*TILE_SIZE: diff.y = -5*TILE_SIZE
            
            self.position += diff
            self.acceleration = vec2(0, 0)    
            self.update_rect()

    def update_rect(self):
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        self.rect.height = self.size.y
        self.rect.width = self.size.x
    
    def get_current_velocity(self):
        return self.position - self.prev_position

    # def get_display_rect(self, camera):
    #     pos = self.position * camera.get_scale() + camera.offset
    #     size = pos + self.size * camera.get_scale()
    #     return pygame.Rect(pos.x, pos.y, pos.x + self.width * camera.get_scale(), pos.y + self.height * camera.get_scale())
    
    def get_display_bounds(self, camera):
        pos = self.position * camera.get_scale() + camera.offset
        return pos, pos + self.size * camera.get_scale()
    
    def get_display_center(self, camera):
        pos = self.position * camera.get_scale() + camera.offset
        return pos + self.size * camera.get_scale() * 0.5
    
    def get_uv(self):
        return matrices["normal"]
    

class Entity(RigidBody):
    def __init__(self, x, y, width, height, texture, mass, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, gravity_enabled, is_immovable, is_physical)
        self.age = 0
        self.max_age = max_age
        self.is_alive = True
        self.is_talking = False
        self.talk_bubble_text = ""
        self.text_bubble_remaining_time = 0

    def update(self, dt):
        self.tick(dt)
        if self.max_age > 0:
            self.age += dt
            self.tick(dt)
            if self.age >= self.max_age:
                self.is_alive = False

    def tick(self, dt):
        if self.text_bubble_remaining_time > 0: self.text_bubble_remaining_time -= dt
        pass

    def set_text_bubble(self, text, time=5):
        return self.talk_bubble_text
    

class LivingEntity(Entity):
    def __init__(self, x, y, width, height, texture, mass, health, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True, animation_frames=1):
        super().__init__(x, y, width/animation_frames, height, texture, mass, max_age, gravity_enabled, is_immovable, is_physical)
        self.health = health
        self.animation_frame = 0
        self.animation_frames = animation_frames
        self.texture_sheet_width = width
        self.texture_state = texture


    def damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.is_alive = False

    def heal(self, amount):
        self.health += amount

    def tick(self, dt):
        super().tick(dt)
        self.animation_frame += 1
        if self.animation_frame >= self.animation_frames:
            self.animation_frame = 0

    # def get_uv(self):
    #     return [
    #         self.animation_frame * self.size.x / self.texture_sheet_width, 0,
    #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 1, 
    #     ]
        
        

class Player(LivingEntity):
    def __init__(self, x, y, width, height, texture, mass, health=100, max_age=0, gravity_enabled=True, is_immovable=False, is_physical=True):
        super().__init__(x, y, width, height, texture, mass, health, max_age, gravity_enabled, is_immovable, is_physical)
        self.is_jumping = False
        self.jump_force = -1000*TILE_SIZE
        self.movement_speed = 3.5*TILE_SIZE
        self.state = PlayerState.IDLE_RIGHT

    def jump(self):
        if not self.is_jumping:
            self.accelerate(vec2(0, self.jump_force))
            self.is_jumping = True

    def move(self, d):
        self.accelerate(d)

    def move_left(self, dt):
        if self.get_velocity().x / dt > -self.movement_speed:
            self.move(vec2(-self.movement_speed / dt, 0))

    def move_right(self, dt):
        if self.get_velocity().x / dt < self.movement_speed:
            self.move(vec2(self.movement_speed / dt, 0))

    def update(self, dt):
        super().update(dt)

    def tick(self, dt):
        super().tick(dt)

    def get_uv(self):
        if self.get_velocity().x < 0:
            return matrices["reflected_vertical"]
        return matrices["normal"]
        #     return [
        #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 0,
        #         self.animation_frame * self.size.x / self.texture_sheet_width, 1, 
        #     ]
        # else:
        #     return [
        #         self.animation_frame * self.size.x / self.texture_sheet_width, 0,
        #         (self.animation_frame + 1) * self.size.x / self.texture_sheet_width, 1, 
        #     ]            

    def update_state(self):
        self.state = PlayerState.IDLE_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.IDLE_LEFT
        if(self.is_crouching):
            self.state = PlayerState.CROUCHING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.CROUCHING_LEFT
        if(self.is_jumping):
            self.state = PlayerState.JUMPING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.JUMPING_LEFT



class Environment(pygame.sprite.Group):
    def __init__(self, map_manager):
        self.bodies = []
        self.map_manager = map_manager

    def add_body(self, body):
        self.bodies.append(body)
        # self.add(body)


    def apply_gravity(self):
        for body in self.bodies:
            body.apply_gravity()
            
    def solve_collisions(self, dt):
        for i in range(len(self.bodies)):
            # for j in range(i + 1, len(self.bodies)):
            #     Environment.resolve_collision(self.bodies[i], self.bodies[j])
            body = self.bodies[i]

            start = body.position.copy()
            destination = body.position + body.size
            velocity = body.get_velocity()

            if velocity.x > 0: destination.x += velocity.x
            else: start.x += velocity.x
            if velocity.y > 0: destination.y += velocity.y
            else: start.y += velocity.y

            start_i = vec2i(math.floor(start.x / TILE_SIZE), math.floor(start.y / TILE_SIZE)) - vec2i(3, 3)
            # destination_i = vec2i.from_vec2(destination / vec2(TILE_SIZE, TILE_SIZE))
            destination_i = vec2i(math.floor(destination.x / TILE_SIZE), math.floor(destination.y / TILE_SIZE)) + vec2i(3, 3)

            # print(f"start: {start_i} destination: {destination_i}")
            for x in range(start_i.x, destination_i.x):
                for y in range(start_i.y, destination_i.y):
                    tile = self.map_manager.get_tile(x, y)
                    if tile is not None:
                        # print(f"Tile collision resolving! {x} ; {y}")
                        Environment.resolve_collision(self.bodies[i], tile, dt)
                        # draw_quad(textures['tiles'][tile.tile_type][0], tile.get_uv_matrix(), *tile.get_display_bounds(camera))


    def update_positions(self, dt):
        for body in self.bodies:
            body.update_position(dt)

    def update(self, dt, sub_steps=1):
        for body in self.bodies:
            if isinstance(body, Entity):
                body.update(dt)

        sub_dt = float(dt / sub_steps)
        for _ in range(sub_steps):
            self.apply_gravity()
            self.solve_collisions(sub_dt)
            self.update_positions(sub_dt)
    

    # -----------------------------
    # Функція для перевірки колізій
    # -----------------------------
    def check_collision(body1, body2):
        if not body1.is_physical and body2.is_physical: return False
        # print(body1.rect, body2.rect)
        return (body1.position.x < body2.position.x + body2.size.x and
                body1.position.x + body1.size.x > body2.position.x and
                body1.position.y < body2.position.y + body2.size.y and
                body1.position.y + body1.size.y > body2.position.y)

        # return body1.rect.colliderect(body2.rect)
    
        # x1, y1, w1, h1 = body1.get_hitbox()
        # x2, y2, w2, h2 = body2.get_hitbox()
        # print(x1, y1, w1, h1)
        # print(x2, y2, w2, h2)
        # return not (x1 + w1 < x2 or x1 > x2 + w2 or y1 + h1 < y2 or y1 > y2 + h2)

    # -----------------------------
    # Функція для обробки колізій
    # -----------------------------
    def resolve_collision(body1, body2, dt):
        if Environment.check_collision(body1, body2):
            # print("Collision detected!")

            # Розрахунок глибини проникнення по осях
            ox1, oy1 = body1.position_old.x, body1.position_old.y
            ox2, oy2 = body2.position_old.x, body2.position_old.y
            x1, y1 = body1.position.x, body1.position.y
            x2, y2 = body2.position.x, body2.position.y
            w1, h1 = body1.size.x, body1.size.y
            w2, h2 = body2.size.x, body2.size.y

            overlap_x = min(x1 + w1 - x2, x2 + w2 - x1)
            overlap_y = min(y1 + h1 - y2, y2 + h2 - y1)

            # # Розрахунок швидкості удару
            # hit_speed = ((body1.get_velocity().x - body2.get_velocity().x)**2 + (body1.get_velocity().y - body2.get_velocity().y)**2)**0.5
            # if hit_speed > 10:
            #     if isinstance(body1, LivingEntity): body1.damage(hit_speed/2)
            #     if isinstance(body2, LivingEntity): body2.damage(hit_speed/2)
            # print("Hit speed:", hit_speed)


            # Визначаємо напрямок нормалі зіткнення
            if abs(overlap_x) < abs(overlap_y):
                if x1 < x2: normal = [1, 0]  # Зіткнення зліва
                else: normal = [-1, 0]  # Зіткнення справа
                penetration = overlap_x
            else:
                if y1 < y2: 
                    normal = [0, 1]  # Зіткнення зверху
                else: 
                    normal = [0, -1]  # Зіткнення знизу
                if isinstance(body2, Player): body2.is_jumping = False
                if isinstance(body1, Player): body1.is_jumping = False
                if body1.get_velocity().x != 0: body1.accelerate(vec2(body1.get_velocity().x / dt*-2, 0))
                if body2.get_velocity().x != 0: body2.accelerate(vec2(body2.get_velocity().x / dt*-2, 0))
                penetration = overlap_y


            if body1.is_immovable and not body2.is_immovable: # Якщо body1 нерухомий
                body2.position.x += normal[0] * penetration
                body2.position.y += normal[1] * penetration
                # if normal[0] != 0: body2.position_old.x = body2.position.x
                # if normal[1] != 0: body2.position_old.y = body2.position.y
                return
            
            if body2.is_immovable and not body1.is_immovable: # Якщо body2 нерухомий
                body1.position.x -= normal[0] * penetration
                body1.position.y -= normal[1] * penetration
                # if normal[0] != 0: body1.position_old.x = body1.position.x
                # if normal[1] != 0: body1.position_old.y = body1.position.y
                # body1.acceleration *= vec2(*normal)
                return

            # Виштовхуємо тіла, щоб прибрати проникнення
            correction = penetration / (1 / body1.mass + 1 / body2.mass)
            body1.position.x -= normal[0] * correction / body1.mass
            body1.position.y -= normal[1] * correction / body1.mass
            body2.position.x += normal[0] * correction / body2.mass
            body2.position.y += normal[1] * correction / body2.mass

class Tile(RigidBody):

    def __init__(self, x, y, layer, tile_type):
        super().__init__(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE, None, 0, False, True, True)
        self.tile_pos = vec2(x, y)
        self.tile_type = tile_type
        self.state = [1,1]

    def get_uv(self):
        uv = [
            [self.state[0]/6,       1-self.state[1]/4],
            [(self.state[0] + 1)/6, 1-self.state[1]/4],
            [(self.state[0] + 1)/6, 1-(self.state[1]+1)/4],
            [self.state[0]/6,       1-(self.state[1]+1)/4],
            # [0/6, 1-1/4],
            # [1/6, 1-1/4],
            # [1/6, 0],
            # [0/6, 0]
        ]
        # print(self.state, uv)
        return uv
        
    
    def update_state(self, neighbours):
        """
        top, left, bottom, right
        """
        match neighbours:
            case [0,0,0,0]: self.state = [3,3] 

            case [0,0,1,1]: self.state = [0,0] 
            case [0,1,1,1]: self.state = [1,0] 
            case [0,1,1,0]: self.state = [2,0] 

            case [1,0,1,1]: self.state = [0,1] 
            # case [1,1,1,1]: self.state = [1,1] 
            case [1,1,1,0]: self.state = [2,1] 

            case [1,0,0,1]: self.state = [0,2] 
            case [1,1,0,1]: self.state = [1,2] 
            case [1,1,0,0]: self.state = [2,2] 

            case [0,0,1,0]: self.state = [3,0] 
            case [1,0,1,0]: self.state = [3,1] 
            case [1,0,0,0]: self.state = [3,2] 

            case [0,0,0,1]: self.state = [0,3] 
            case [0,1,0,1]: self.state = [1,3] 
            case [0,1,0,0]: self.state = [2,3] 

            case _: self.state = [1,1] 
        pass

class MapManager:
    def __init__(self, map_size, chunk_size, textures):
        self.map_size = map_size
        self.chunk_size = chunk_size
        self.textures = textures
        self.map = {}
        for cx in range(0, self.map_size):
            for cy in range(0, self.map_size):
                self.initialize_chunk(cx, cy, update_immediate=True)  
    
    def initialize_chunk(self, cx, cy, update_immediate=False):
        # Initialize map with chunks of tiles

        global_x, global_y = cx * self.chunk_size, cy * self.chunk_size

        self.map[f'c{cx}_{cy}'] = [[
            Tile(x, y, 1, "ground") if y > 0 else None
            for y in range(global_y, global_y + self.chunk_size)] 
            for x in range(global_x, global_x + self.chunk_size)]
        
        if update_immediate: self.update_chunk(cx, cy)

        
    def get_local_coords(self, global_x, global_y):
        """Correct chunk calculation for negative coordinates"""

        cx = math.floor(global_x / self.chunk_size)
        cy = math.floor(global_y / self.chunk_size)
        lx = global_x - cx * self.chunk_size
        ly = global_y - cy * self.chunk_size
        # lx = global_x % self.chunk_size
        # if lx < 0:  # Adjust when global_x is negative
        #     cx -= 1
        #     lx += self.chunk_size

        # ly = global_y % self.chunk_size
        # if ly < 0:  # Adjust when global_y is negative
        #     cy -= 1
        #     ly += self.chunk_size

        return cx, cy, lx, ly
    
    def get_tile(self, global_x, global_y):
        # Compute chunk and local tile coordinates
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        
        # Ensure chunk exists
        chunk_key = f'c{cx}_{cy}'
        
        if chunk_key not in self.map:
            self.initialize_chunk(cx, cy)  # Initialize the chunk if it doesn't exist

        return self.map[chunk_key][lx][ly] if chunk_key in self.map else None


    # def get_chunk(self, cx, cy):
    #     chunk = None
    #     try:
    #         chunk = self.map[cx][cy]
    #     except IndexError:
    #         print(f"Chunk out of bounds: ({cx}, {cy})")
    #     return chunk

    def update_tile(self, global_x, global_y, update_neighbours=False):
        tile = self.get_tile(global_x, global_y)
        if tile is not None:
            tile.update_state(self.get_neighbors(global_x, global_y))

        if update_neighbours:
            self.update_tile(global_x - 1, global_y, False)
            self.update_tile(global_x + 1, global_y, False)
            self.update_tile(global_x, global_y - 1, False)
            self.update_tile(global_x, global_y + 1, False)

    def delete_tile(self, global_x, global_y):
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        chunk_key = f'c{cx}_{cy}'
        if chunk_key in self.map:
            tile = self.map[chunk_key][lx][ly]
            if tile is not None:
                self.map[chunk_key][lx][ly] = None
                self.update_tile(global_x, global_y, True)

    def set_tile(self, global_x, global_y, tile_type):
        cx, cy, lx, ly = self.get_local_coords(global_x, global_y)
        chunk_key = f'c{cx}_{cy}'
        if chunk_key in self.map:
            tile = self.map[f'c{cx}_{cy}'][lx][ly]
            if tile is None:
                self.map[f'c{cx}_{cy}'][lx][ly] = Tile(global_x, global_y, 1, tile_type)
                self.update_tile(global_x, global_y, True)
            
    def get_neighbors(self, global_x, global_y):
        # Determine neighbor presence: [top, left, bottom, right]
        return [
            bool(self.get_tile(global_x, global_y - 1) is not None),
            bool(self.get_tile(global_x - 1, global_y) is not None),
            bool(self.get_tile(global_x, global_y + 1) is not None),
            bool(self.get_tile(global_x + 1, global_y) is not None),
        ]
    
    def update_chunk(self, chunk_x, chunk_y):
        print(f"Updating chunk: ({chunk_x}, {chunk_y})")
        # Update all tiles in the specified chunk
        for lx in range(self.chunk_size):
            for ly in range(self.chunk_size):
                self.update_tile(chunk_x * self.chunk_size + lx, chunk_y * self.chunk_size + ly)



def coord_round(value):
    return math.floor(value) if value >= 0 else math.floor(value) - 1

class PlayerState(Enum):
    IDLE_RIGHT = 0
    IDLE_LEFT = 1
    IDLE_CROUCHING_RIGHT = 2
    IDLE_CROUCHING_LEFT = 3
    CROUCHING_RIGHT = 4
    CROUCHING_LEFT = 5
    WALKING_RIGHT = 6
    WALKING_LEFT = 7
    RUNNING_RIGHT = 8
    RUNNING_LEFT = 9
    JUMPING_RIGHT = 10
    JUMPING_LEFT = 11

class PlayerDirection(Enum):
    RIGHT = 0
    LEFT = 1

# Background layer class
class BackgroundLayer:
    def __init__(self, texture, speed, layer):
        self.texture, self.width, self.height = texture
        self.speed = speed
        self.layer = layer
        self.offset = 0

    def draw(self, camera, screenWidth, screenHeight):
        ratio = screenWidth / screenHeight
        self_ratio = self.width / self.height
        height = screenWidth / self_ratio if ratio > self_ratio else screenHeight
        width = screenHeight * self_ratio if ratio < self_ratio else screenWidth
        top = (screenHeight - height) / 2
        left = (screenWidth - width) / 2
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0 + self.offset, 1); glVertex2f(left, top) 
        glTexCoord2f(1 + self.offset, 1); glVertex2f(left + width, top)
        glTexCoord2f(1 + self.offset, 0); glVertex2f(left + width, top + height)
        glTexCoord2f(0 + self.offset, 0); glVertex2f(left, top + height)
        glEnd()

    def scroll(self, offset, screenWidth):
        self.offset = -offset * self.speed / screenWidth


# # Ground class
# class GroundTile(GameObject):
#     def __init__(self, x, y, texture, layer):
#         width, height = 64, 64
#         super().__init__(x, y, width, height, texture, layer, False)

# Create game objects

# country, capital = random.choice(list(d.items()))
# capital = random.choice(list(d.values()))

class FollowPoint(Enum):
    CENTER = vec2(0.5, 0.65)
    LEFT = vec2(0.7, 0.65)
    RIGHT = vec2(0.3, 0.65)


class Camera:
    def __init__(self):
        self.offset = vec2()
        self.scale = 1
        self.zoom = 1
        self.follow_point = FollowPoint.CENTER
        self.last_follow_point_change = 0
        self.renderBounds = pygame.Rect(0, 0, 0, 0)
        self.render_distance = 10

    def updateBounds(self, screenWidth, screenHeight):
        self.renderBounds = pygame.Rect(TILE_SIZE * -2, TILE_SIZE * -2, screenWidth + TILE_SIZE * 2, screenHeight + TILE_SIZE * 2)
        self.render_distance = max(screenWidth, screenHeight) // TILE_SIZE + 1

    def set_follow_point(self, fp):
        self.follow_point = fp
        self.last_follow_point_change = 0

    def follow(self, body, dt): 
        if body is None: return
        velocity = body.get_velocity()
        if velocity.x > 0.1: self.set_follow_point(FollowPoint.RIGHT)
        elif velocity.x < -0.1: self.set_follow_point(FollowPoint.LEFT)
        elif self.follow_point != FollowPoint.CENTER:
            self.last_follow_point_change += dt
            if self.last_follow_point_change > 3:
                self.set_follow_point(FollowPoint.CENTER)
        object_center = body.get_display_center(self)
        screen_center = vec2(self.renderBounds.right, self.renderBounds.bottom) * self.follow_point.value
        if(object_center.x != screen_center.x):
            distance = abs(screen_center.x - object_center.x)
            direction = -1 if screen_center.x < object_center.x else 1
            offset = distance
            self.offset.x += direction * offset * dt * 2

        if(object_center.y != screen_center.y):
            distance = abs(screen_center.y - object_center.y)
            direction = -1 if screen_center.y - object_center.y < 0 else 1
            offset = distance
            self.offset.y += direction * offset * dt * 2

        # self.offset = screen_center - object_center

    def get_scale(self):
        return self.scale * self.zoom