import sys

import numpy as np
#import keyboard
import pygame

from .sprites import ObstacleMap
from .board_analyzer import BoardAnalyzer, AnalysisStatus


LEFT, RIGHT = -1, 1


class Bot:

    def __init__(self, sensor, left_key='a', right_key='z'):
        self.left_key = left_key
        self.right_key = right_key
        self.board_analyzer = BoardAnalyzer()
        self.sensor = pygame.sprite.GroupSingle(sensor)
        self.obstacle = pygame.sprite.GroupSingle(ObstacleMap(self.board_analyzer.board_dims))
        self.reset()

    def reset(self):
        self.obstacle.sprite.update(0)
        #self.apply_move(None)
        self.head_direction = [1, 0]
        self.head_positions = [[0, 0]]
        self.impact_points = []
        self.moves = []

    def get_move(self):
        if self.sensor.sprite.impact_point is None:
            return LEFT
        head_to_impact_vec = self.sensor.sprite.impact_point - self.head_positions[-1]
        # If the closest impact point is on the left hand side, turn right. And vice versa.
        if np.cross(self.head_direction, head_to_impact_vec) > 0:
            return LEFT
        return RIGHT

    def draw(self, screen, fps):
        self.obstacle.draw(screen)
        self.sensor.draw(screen)

        script = f"""document.ctx.clearRect(0, 0, {self.board_analyzer.board_dims["display_width"]}, {self.board_analyzer.board_dims["display_height"]});
        document.ctx.fillStyle = "rgb(200, 0, 0)";
        document.ctx.fillRect{*self.sensor.sprite.rect,};"""
        self.board_analyzer.driver.execute_script(script)

        # Collision surface in red
        if self.sensor.sprite.impact_point is not None:
            overlap_surf = self.sensor.sprite.overlap_mask.to_surface(setcolor='red')
            overlap_surf.set_colorkey((0, 0, 0))
            screen.blit(overlap_surf, self.sensor.sprite.rect)

        # Head positions in gray
        pygame.draw.circle(screen, 'gray', self.head_positions[-1], 1)

        # Vector from head to collision point in blue (left hand side) or red (right hand side)
        if not self.impact_points or self.impact_points[-1] is None:
            pass
        else:
            if self.moves[-1] == LEFT:
                color = 'red'
            elif self.moves[-1] == RIGHT:
                color = 'blue'
            pygame.draw.line(screen, color, self.head_positions[-1], self.impact_points[-1], 3)

        pygame.display.update()
        pygame.display.set_caption(f"{int(fps)} FPS")

    def run(self, framerate=60):
        clock = pygame.time.Clock()
        pygame.init()
        screen = pygame.display.set_mode((self.obstacle.sprite.obstacle.shape[:2]))
        while True:
            # Handling exit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            status = self.board_analyzer.update()
            if status == AnalysisStatus.GAME_OVER:
                self.reset()
                continue
            # if status == AnalysisStatus.FLYING:
            #     self.reset()
            #     continue
            if status == AnalysisStatus.UNCHANGED:
                continue
            # Update obstacle map and get head position and direction from board analyze
            rgb_board = self.board_analyzer.get_rgb_board()
            self.obstacle.update(rgb_board)
            head_position = self.board_analyzer.head_position
            self.head_direction = head_position - self.head_positions[-1]
            if status == AnalysisStatus.MOVING:
                self.head_positions.append(head_position)
                # Update sensor position and thus the collision mask
                self.sensor.update(head_position, self.head_direction, self.obstacle)
                self.impact_points.append(self.sensor.sprite.impact_point)

                # Apply move accordingly
                move = self.get_move()
                #self.apply_move(move)
                self.moves.append(move)

            # Draw
            fps = clock.get_fps()
            self.draw(screen, fps)

            clock.tick(framerate)
