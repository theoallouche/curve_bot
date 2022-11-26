import sys

import cv2
import keyboard
import mss
import numpy as np
import pygame


# BOARD = {"top": 337, "left": 433, "width": 748, "height": 748}
# BOARD = {"top": 336, "left": 432, "width": 750, "height": 750}
BOARD = {"top": 65, "left": 924, "width": 1285, "height": 1285, "mon": 1}
LEFT_KEY = 'a'
RIGHT_KEY = 'z'
CURVATURE_RADIUS = 40
MAX_FPS = 60

LEFT, RIGHT = -1, 1

def get_rgb_board(board_position):
    with mss.mss() as sct:
        return np.transpose(np.flip(np.array(sct.grab(board_position))[:, :, :3], axis=-1), (1, 0, 2))

def get_head_position(current_board, previous_board):
    # RGB to gray + binarization
    new_im = cv2.cvtColor(current_board, cv2.COLOR_RGB2GRAY)
    old_im = cv2.cvtColor(previous_board, cv2.COLOR_RGB2GRAY)
    _, new_im = cv2.threshold(new_im, 10, 255, cv2.THRESH_BINARY)
    _, old_im = cv2.threshold(old_im, 10, 255, cv2.THRESH_BINARY)

    diff = new_im - old_im

    kernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
    diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, kernel)
    diff = cv2.erode(diff, kernel, iterations=1)
    # diff = cv2.dilate(diff, kernel, iterations=1)

    # num_labels, labels_im = cv2.connectedComponents(diff)
    # d = np.sort(np.bincount(labels_im.flatten()))[1] #2nd biggest label
    # head = (labels_im == d).astype(np.uint8)

    M = cv2.moments(diff)
    return np.array([int(M["m01"] / M["m00"]), int(M["m10"] / M["m00"])])

def get_direction(positions):
    # last_position_ind = 3
    # if len(positions) < last_position_ind:
    #     direction = positions[-1] - positions[-2]
    # else:
    #     direction = positions[-1] - positions[-last_position_ind]
    # return direction
    return positions[-1] - positions[-2]

def apply_move(move):
    if move == LEFT:
        keyboard.release(RIGHT_KEY)
        keyboard.press(LEFT_KEY)
    elif move == RIGHT:
        keyboard.release(LEFT_KEY)
        keyboard.press(RIGHT_KEY)
    else:
        keyboard.release(RIGHT_KEY)
        keyboard.release(LEFT_KEY)

def reset():
    positions = [[0, 0]]
    moves = []
    collions_vecs = []
    old_im = np.zeros((BOARD["width"], BOARD["height"], 3), dtype=np.uint8)
    same_frame_cpt = 0
    return positions, moves, collions_vecs, old_im, same_frame_cpt

class Sensor(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.radius = CURVATURE_RADIUS
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        pygame.draw.circle(self.image, 'green', (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()

    def update(self, position, direction, obstacle):
        # Sensor position should be in front of the head, at a distance of 'CURVATURE_RADIUS'
        self.rect.center = position + (CURVATURE_RADIUS + 10)*direction / np.linalg.norm(direction)
        # if pygame.mouse.get_pos():
        #     self.rect.center = pygame.mouse.get_pos()

    def get_collision_mask(self, obstacle):
        offset = obstacle.sprite.rect.x - self.rect.x, obstacle.sprite.rect.y - self.rect.y
        return self.mask.overlap_mask(obstacle.sprite.mask, offset)

    def _get_closest_impact_position(self, head_position, collision_mask):
        # impact_position = collision_mask.centroid()
        # Seems we can not access the mask coordinates, even by casting it to np.array
        width, height = collision_mask.get_size()
        collisions_points = [[x, y] for x in range(width) for y in range(height) if collision_mask.get_at((x, y))]

        # Passsage des coordonnees dans le réferentiel du rect englobant du sensor ((0, 0) en haut à gauche) vers les coordonnees dans l'ecran
        impact_absolute_positions = np.array(self.rect.topleft) + np.array(collisions_points)
        distances = np.linalg.norm(impact_absolute_positions - head_position, axis=1)
        closest_point_index = np.argmin(distances)
        impact_absolute_position = impact_absolute_positions[closest_point_index]
        impact_distance = distances[closest_point_index]
        return impact_absolute_position, impact_distance

    def get_move(self, head_position, direction, collision_mask):
        if collision_mask.count() == 0:
            return None, None

        impact_position, impact_distance = self._get_closest_impact_position(head_position, collision_mask)

        head_to_impact_vec = impact_position - head_position
        signed_angle = np.arctan2(head_to_impact_vec[1], head_to_impact_vec[0]) - np.arctan2(direction[1], direction[0])
        if signed_angle > 0: # ça tappe à droite dans le sens de la marche, donc on tourne à gauche
            return LEFT, head_to_impact_vec
        return RIGHT, head_to_impact_vec


class Obstacle(pygame.sprite.Sprite):

    def update(self, image):
        self.image = pygame.surfarray.make_surface(image)
        self.rect = self.image.get_rect(center=(BOARD["width"]//2, BOARD["height"]//2))
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()


# Intialization
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((BOARD["width"], BOARD["height"]))
sensor = pygame.sprite.GroupSingle(Sensor())
obstacle = pygame.sprite.GroupSingle(Obstacle())
positions, moves, collions_vecs, old_im, same_frame_cpt = reset()

# Main loop
while True:
    # Handling exit event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    board = get_rgb_board(BOARD)

    # Skip to next image if it has not changed
    if (board == old_im).all():
        same_frame_cpt += 1
        # If the screen has not changed for a long time, it's most likely game over
        if same_frame_cpt >= 1.5*MAX_FPS:
            positions, moves, collions_vecs, old_im, same_frame_cpt = reset()
        continue

    # Try to find the head position (based on successive images difference)
    # Skip to next image if unfound
    try:
        head_position = get_head_position(board, old_im)
    except (ValueError, ZeroDivisionError) as e:
        # print(f"Cant find the head ({e})")
        continue

    old_im = board.copy()

    positions.append(head_position)
    direction = get_direction(positions)

    obstacle.update(board)
    sensor.update(head_position, direction, obstacle)

    overlap_mask = sensor.sprite.get_collision_mask(obstacle)
    collision = overlap_mask.count() > 0

    move, collion_vec = sensor.sprite.get_move(head_position, direction, overlap_mask)
    moves.append(move)
    collions_vecs.append(collion_vec)
    apply_move(move)

    # Drawing
    obstacle.draw(screen)
    sensor.draw(screen)
    if collision:
        overlap_surf = overlap_mask.to_surface(setcolor='red')
        overlap_surf.set_colorkey((0, 0, 0))
        screen.blit(overlap_surf, sensor.sprite.rect)
    for position, move, collision_vec in zip(positions, moves, collions_vecs):
        pygame.draw.circle(screen, 'gray', position, 1)
        if move is None:
            continue
        if move == LEFT:
            color = 'red'
        elif move == RIGHT:
            color = 'blue'
        pygame.draw.line(screen, color, position, position+collision_vec, 1)
    pygame.display.update()
    pygame.display.set_caption(f"{int(clock.get_fps())} FPS")
    clock.tick(MAX_FPS)