import sys

import numpy as np
import keyboard
import pygame

from .sprites import ObstacleMap
from .board_analyzer import BoardAnalyzer, AnalysisStatus


LEFT, RIGHT = -1, 1


class Bot:

    def __init__(self, board_position, sensor, left_key='a', right_key='z'):
        self.board_position = board_position
        self.left_key = left_key
        self.right_key = right_key
        self.board_analyzer = BoardAnalyzer(board_position)
        self.sensor = pygame.sprite.GroupSingle(sensor)
        self.obstacle = pygame.sprite.GroupSingle(ObstacleMap(board_position))
        self.reset()

    def reset(self):
        self.apply_move(None)
        self.head_direction = [1, 0]
        self.head_positions = [[0, 0]]
        self.impact_points = []
        self.moves = []

    def get_move(self):
        if self.sensor.sprite.impact_point is None:
            return None
        head_to_impact_vec = self.sensor.sprite.impact_point - self.head_positions[-1]
        # If the closest impact point is on the left hand side, turn right. And vice versa.
        if np.cross(self.head_direction, head_to_impact_vec) > 0:
            return LEFT
        return RIGHT

    def apply_move(self, move):
        if move == LEFT:
            keyboard.release(self.right_key)
            keyboard.press(self.left_key)
        elif move == RIGHT:
            keyboard.release(self.left_key)
            keyboard.press(self.right_key)
        else:
            keyboard.release(self.right_key)
            keyboard.release(self.left_key)

    def draw(self, screen, fps):
        self.obstacle.draw(screen)
        self.sensor.draw(screen)

        # Collision surface in red
        if self.sensor.sprite.impact_point is not None:
            overlap_surf = self.sensor.sprite.overlap_mask.to_surface(setcolor='red')
            overlap_surf.set_colorkey((0, 0, 0))
            screen.blit(overlap_surf, self.sensor.sprite.rect)

        # Head positions in gray + vectors from head to collision point in blue (left hand side) or red (right hand side)
        for position, move, impact_point in zip(self.head_positions, self.moves, self.impact_points):
            pygame.draw.circle(screen, 'gray', position, 1)
            if impact_point is None:
                continue
            if move == LEFT:
                color = 'red'
            elif move == RIGHT:
                color = 'blue'
            pygame.draw.line(screen, color, position, impact_point, 1)

        pygame.display.update()
        pygame.display.set_caption(f"{int(fps)} FPS")

    def run(self, framerate=60):
        clock = pygame.time.Clock()
        pygame.init()
        screen = pygame.display.set_mode((self.board_position["width"], self.board_position["height"]))

        while True:
            # Handling exit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Do nothing if head has not been found
            status = self.board_analyzer.update()
            if status != AnalysisStatus.SUCCESS:
                if status == AnalysisStatus.GAME_OVER:
                    self.reset()
                continue

            # Update obstacle map and get head position and direction from board analyze
            self.obstacle.update(self.board_analyzer.current_rgb_board)
            head_position = self.board_analyzer.head_position
            self.head_direction = head_position - self.head_positions[-1]
            self.head_positions.append(head_position)

            # Update sensor position and thus the collision mask
            self.sensor.update(head_position, self.head_direction, self.obstacle)
            self.impact_points.append(self.sensor.sprite.impact_point)

            # Apply move accordingly
            move = self.get_move()
            self.apply_move(move)
            self.moves.append(move)

            # Draw
            fps = clock.get_fps()
            self.draw(screen, fps)

            clock.tick(framerate)

