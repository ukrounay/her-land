import pygame
from pygame.locals import *
from OpenGL.GL import *
from enum import Enum
import numpy as np


from globals import *


class vec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, multiplier):
        if isinstance(multiplier, vec2):
            return vec2(self.x * multiplier.x, self.y * multiplier.y)
        return vec2(self.x * multiplier, self.y * multiplier)


    def length(self):
        return np.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        length = self.length()
        if length > 0:
            return vec2(self.x / length, self.y / length)
        return vec2()
    

    
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



# GameObject class
class GameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, texture, layer, gravity):
        super().__init__()

        self.position = vec2(x, y)
        self.velocity = vec2()
        self.view_offset = vec2()
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.gravity = gravity
        self.texture = texture
        self.layer = layer

    def draw(self, camera):
        start, end = self.get_display_bounds(camera)
        draw_quad(self.texture, matrices["normal"], start, end)

    def update_rect(self):
        self.rect.topleft = (self.position.x, self.position.y)
        self.rect.height = self.height
        self.rect.width = self.width
    
    def get_display_rect(self, camera):
        pos = self.position * camera.get_scale() + camera.offset
        return pygame.Rect(pos.x, pos.y, pos.x + self.width * camera.get_scale(), pos.y + self.height * camera.get_scale())
    
    def get_display_bounds(self, camera):
        pos = self.position * camera.get_scale() + camera.offset
        return pos, pos + vec2(self.width, self.height) * camera.get_scale()
    
    def get_display_center(self, camera):
        pos = self.position * camera.get_scale() + camera.offset
        return pos + vec2(self.width, self.height) * camera.get_scale() * 0.5


class PlayerObject(GameObject):
    def __init__(self, x, y, width, height, texture, layer, gravity):
        super().__init__(x, y, width, height, texture, layer, gravity)
        self.normal_height = height
        self.crouching_height = height * 0.65
        self.is_standing = False
        self.is_crouching = False
        self.is_jumping = False
        self.is_sprinting = False
        self.max_movement_speed = 5
        self.state = PlayerState.IDLE_RIGHT
        self.direction = PlayerDirection.RIGHT

    def move_left(self):
        self.velocity.x += -1 if self.velocity.x > -self.max_movement_speed else 0
        self.direction = PlayerDirection.LEFT
        self.update_state()

    def move_right(self):
        self.velocity.x += 1 if self.velocity.x < self.max_movement_speed else 0
        self.direction = PlayerDirection.RIGHT
        self.update_state()

    def update(self, interactable_objects):
        """ Move the player. """
        # Gravity
        self.apply_forces()
 
        # Move left/right
        self.position.x += self.velocity.x * self.get_speed_modifier()
        self.update_rect()

 
        # See if we hit anything
        hit_list = pygame.sprite.spritecollide(self, interactable_objects, False)
        for obj in hit_list:
            # If we are moving right,
            # set our right side to the left side of the item we hit
            if self.velocity.x > 0:
                self.position.x = obj.rect.left - self.width
            elif self.velocity.x < 0:
                # Otherwise if we are moving left, do the opposite.
                self.position.x = obj.rect.right
 
        # Move up/down
        self.position.y += self.velocity.y
        self.update_rect()

        # Check and see if we hit anything
        hit_list = pygame.sprite.spritecollide(self, interactable_objects, False)
        for obj in hit_list:
 
            # Reset our position based on the top/bottom of the object.
            if self.velocity.y > 0:
                self.position.y = obj.rect.top - self.height
            elif self.velocity.y < 0:
                self.position.y = obj.rect.bottom
 
            # Stop our vertical movement
            self.velocity.y = 0
        
        self.update_rect()
        self.update_state()
 
    def apply_forces(self):
        """ Calculate effect of gravity and friction. """

        self.velocity.x *= FRICTION_COEFFICIENT
        self.velocity.y += GRAVITY

        if abs(self.velocity.x) < 0.5: self.velocity.x = 0

 
    def jump(self, interactable_objects):
        """ Called when user hits 'jump' button. """

        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, interactable_objects, False)
        self.rect.y -= 2
 
        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0:
            self.velocity.y += -JUMP_STRENGTH
        self.update_state()


    def crouch(self, is_crouching):
        if self.is_crouching != is_crouching:
            if is_crouching:
                self.position.y += self.height - self.crouching_height
                self.height = self.crouching_height
                self.is_sprinting = False
            else:
                self.height = self.normal_height
                self.position.y -= self.height - self.crouching_height

            self.is_crouching = is_crouching
            self.update_rect()
            self.update_state()

    def sprint(self):
        self.is_sprinting = True



    def get_speed_modifier(self):
        if self.is_sprinting:
            return 0.5 if self.is_crouching else 1.5
        return 1


    def update_state(self):
        self.state = PlayerState.IDLE_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.IDLE_LEFT
        if(self.is_crouching):
            self.state = PlayerState.CROUCHING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.CROUCHING_LEFT
        if(self.is_jumping):
            self.state = PlayerState.JUMPING_RIGHT if self.direction == PlayerDirection.RIGHT else PlayerState.JUMPING_LEFT
            
    def draw(self, camera):
        start, end = self.get_display_bounds(camera)
        draw_quad(self.texture, matrices["reflected_vertical" if self.direction == PlayerDirection.LEFT else "normal"], start, end)

class TileObject(GameObject):

    def __init__(self, x, y, texture, layer, tile_type):
        super().__init__(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE, texture, layer, False)
        self.tile_pos = vec2(x, y)
        self.tile_type = tile_type


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

    def draw(self, screenWidth, screenHeight):
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

    def scroll(self, direction, screenWidth):
        self.offset += direction * self.speed / screenWidth
        if self.offset > 1.0 or self.offset < -1.0:
            self.offset = 0


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
    LEFT = vec2(0.8, 0.65)
    RIGHT = vec2(0.2, 0.65)


class Camera:
    def __init__(self):
        self.offset = vec2()
        self.scale = 1
        self.zoom = 1
        self.follow_point = FollowPoint.CENTER
        self.last_follow_point_change = 0
        self.renderBounds = pygame.Rect(0, 0, 0, 0)

    def updateBounds(self, screenWidth, screenHeight):
        self.renderBounds = pygame.Rect(TILE_SIZE * -2, TILE_SIZE * -2, screenWidth + TILE_SIZE * 2, screenHeight + TILE_SIZE * 2)

    def set_follow_point(self, fp):
        self.follow_point = fp
        self.last_follow_point_change = 0

    def follow(self, go: GameObject): 
        if self.follow_point != FollowPoint.CENTER:
            self.last_follow_point_change += 1
            if self.last_follow_point_change > FOLLOW_POINT_RETURN_INTERVAL:
                self.set_follow_point(FollowPoint.CENTER)
        object_center = go.get_display_center(self)
        screen_center = vec2(self.renderBounds.right, self.renderBounds.bottom) * self.follow_point.value
        if(object_center.x != screen_center.x):
            distance = abs(screen_center.x - object_center.x)
            direction = -1 if screen_center.x < object_center.x else 1
            offset = min(max(distance / FPS, 0.2), distance)
            self.offset.x += direction * offset

        if(object_center.y != screen_center.y):
            distance = abs(screen_center.y - object_center.y)
            direction = -1 if screen_center.y - object_center.y < 0 else 1
            offset = min(max(distance / FPS, 0.2), distance)
            self.offset.y += direction * offset

    def get_scale(self):
        return self.scale * self.zoom