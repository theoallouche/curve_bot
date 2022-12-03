import sys

import cv2
import keyboard
import mss
import numpy as np
import pygame

from sensors import Sensor, CircleSensor, LineSensor

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
        return np.transpose(np.flip(np.array(sct.grab(board_position))[:, :, :3], -1), (1, 0, 2))

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
    apply_move(None)
    positions = [[0, 0]]
    moves = []
    impact_points = []
    old_im = np.zeros((BOARD["width"], BOARD["height"], 3), dtype=np.uint8)
    same_frame_cpt = 0
    cpt = 0
    return positions, moves, impact_points, old_im, same_frame_cpt, cpt



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
# sensor = pygame.sprite.GroupSingle(Sensor(direction=-70, distance=100, height=50, width=10))
# sensor = pygame.sprite.GroupSingle(LineSensor(direction=-70, distance=100, length=50, width=10))
sensor = pygame.sprite.GroupSingle(CircleSensor(direction=-70, distance=100, radius=30))
obstacle = pygame.sprite.GroupSingle(Obstacle())
positions, moves, impact_points, old_im, same_frame_cpt, cpt = reset()
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
            positions, moves, impact_points, old_im, same_frame_cpt, cpt = reset()
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
    move = sensor.sprite.get_move()
    apply_move(move)

    obstacle.draw(screen)
    sensor.draw(screen)

    # Drawing collision surface in red
    if sensor.sprite.impact_point is not None:
        overlap_surf = sensor.sprite.overlap_mask.to_surface(setcolor='red')
        overlap_surf.set_colorkey((0, 0, 0))
        screen.blit(overlap_surf, sensor.sprite.rect)

    # Drawing head positions in gray + vectors from head to collision point in blue (left hand side) or red (right hand side)
    moves.append(move)
    impact_points.append(sensor.sprite.impact_point)
    for position, move, impact_point in zip(positions, moves, impact_points):
        pygame.draw.circle(screen, 'gray', position, 1)
        if impact_point is None:
            continue
        if move == LEFT:
            color = 'red'
        elif move == RIGHT:
            color = 'blue'
        pygame.draw.line(screen, color, position, impact_point, 1)

    pygame.display.update()
    pygame.display.set_caption(f"{int(clock.get_fps())} FPS")
    clock.tick(MAX_FPS)