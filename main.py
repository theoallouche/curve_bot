import sys

import cv2
import keyboard
import mss
import numpy as np
import pygame


# BOARD = {"top": 337, "left": 433, "width": 748, "height": 748}
BOARD = {"top": 334, "left": 430, "width": 754, "height": 754}
LEFT_KEY = 'a'
RIGHT_KEY = 'z'
CURVATURE_RADIUS = 50
LINE_WIDTH = 10#4

LEFT, RIGHT = -1, 1

def get_head_position(current_board, previous_board):
    # RGB to gray + binarization
    new_im = cv2.cvtColor(current_board, cv2.COLOR_BGR2GRAY)
    old_im = cv2.cvtColor(previous_board, cv2.COLOR_BGR2GRAY)
    _, new_im = cv2.threshold(new_im, 10, 255, cv2.THRESH_BINARY)
    _, old_im = cv2.threshold(old_im, 10, 255, cv2.THRESH_BINARY)

    diff = new_im - old_im

    # kernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
    # diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, kernel)
    # diff = cv2.erode(diff, kernel, iterations=1)
    # diff = cv2.dilate(diff, kernel, iterations=1)

    # num_labels, labels_im = cv2.connectedComponents(diff)
    # d = np.sort(np.bincount(labels_im.flatten()))[1] #2nd biggest label
    # head = (labels_im == d).astype(np.uint8)

    M = cv2.moments(diff)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    return np.array([cX, cY])


class Sensor(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.radius = LINE_WIDTH
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, 'green', (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()

    def update(self, position, direction, obstacle):
        # Sensor position is in front of the head, at a distance of 'CURVATURE_RADIUS'
        self.rect.center = position + CURVATURE_RADIUS*direction / np.linalg.norm(direction)
        # if pygame.mouse.get_pos():
        #     self.rect.center = pygame.mouse.get_pos()

    def get_collision_mask(self, obstacle):
        offset = obstacle.sprite.rect.x - self.rect.x, obstacle.sprite.rect.y - self.rect.y
        return self.mask.overlap_mask(obstacle.sprite.mask, offset)

    def get_move(self, position, direction, collision_mask):
        if collision_mask.count() == 0:
            return 0
        centroid = collision_mask.centroid() # Coordonnees dans le réferentiel du rect du sensor ((0, 0) en bas à gauche).
        to_centroid_vec = centroid - np.array([self.radius//2, self.radius//2])
        signed_angle = np.arctan2(to_centroid_vec[1], to_centroid_vec[0]) - np.arctan2(direction[1], direction[0])
        if signed_angle > 0: # ça tappe à droite dans le sens de la marche, donc on tourne à gauche
            return LEFT
        return RIGHT


class Obstacle(pygame.sprite.Sprite):

    def update(self, image):
        self.image = pygame.surfarray.make_surface(image.transpose(1, 0, 2))
        self.rect = self.image.get_rect(center=(BOARD["width"]//2, BOARD["height"]//2))
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()


# Intialization
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((BOARD["width"], BOARD["height"]))
sensor = pygame.sprite.GroupSingle(Sensor())
obstacle = pygame.sprite.GroupSingle(Obstacle())
positions = [[0, 0]]
with mss.mss() as sct:
    old_im = np.array(sct.grab(BOARD))[:, :, :3]

# Main loop
while True:
    # Handling exit event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Fetch new image and convert to 3D (RGB) numpy array
    with mss.mss() as sct:
        new_im = np.array(sct.grab(BOARD))[:, :, :3]

    # Skip to next image if it has not changed
    if (new_im == old_im).all():
        continue

    # Try to find the head position (based on successive images difference). Skip to next image if unfound.
    try:
        position = get_head_position(new_im, old_im)
    except (ValueError, ZeroDivisionError) as e:
        print(f"Cant find the head ({e})")
        continue

    old_im = new_im.copy()

    # Store all succesive head positions
    positions.append(position)

    # Try to find an average direction from last positions
    if len(positions) < 10:
        direction = position - positions[-1]
    else:
        direction = position - positions[-10]

    # Update obstacle map and sensor position
    obstacle.update(new_im)
    sensor.update(position, direction, obstacle)

    # Detect collisions
    overlap_mask = sensor.sprite.get_collision_mask(obstacle)
    collision = overlap_mask.count() > 0

    # Choose and apply move
    move = sensor.sprite.get_move(position, direction, overlap_mask)
    if move == LEFT:
        keyboard.release(RIGHT_KEY)
        keyboard.press(LEFT_KEY)
    elif move == RIGHT:
        keyboard.release(LEFT_KEY)
        keyboard.press(RIGHT_KEY)
    else:
        keyboard.release(RIGHT_KEY)
        keyboard.release(LEFT_KEY)

    # Drawing
    obstacle.draw(screen)
    sensor.draw(screen)
    if collision:
        overlap_surf = overlap_mask.to_surface(setcolor='red')
        overlap_surf.set_colorkey((0, 0, 0))
        screen.blit(overlap_surf, sensor.sprite.rect)
    pygame.display.update()
    clock.tick()
    pygame.display.set_caption(f"{int(clock.get_fps())} FPS")
