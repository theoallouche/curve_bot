import numpy as np
import pygame


class ObstacleMap(pygame.sprite.Sprite):

    def __init__(self, board_position):
        super().__init__()
        self.board_position = board_position

    def update(self, image):
        self.image = pygame.surfarray.make_surface(image)
        self.rect = self.image.get_rect(center=(self.board_position["width"]//2, self.board_position["height"]//2))
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()


class Sensor(pygame.sprite.Sprite):

    def __init__(self, direction=0, distance=60, height=50, width=10):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.original_image = self.image
        self.rect = self.image.get_rect()

        pivot = (width//2, distance)
        self.offset = pygame.math.Vector2(self.original_image.get_rect(topleft = (-pivot[0], -pivot[1])).center)

        self.head_position = None
        self.direction = None
        self.direction_offset = direction
        self.overlap_mask = None
        self.impact_point = None

    def update(self, head_position, direction, obstacle):
        self.head_position = head_position
        self.direction = direction
        angle = np.rad2deg(np.arctan2(-direction[1], direction[0])) + 90 - self.direction_offset
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.head_position - self.offset.rotate(-angle))
        self.mask = pygame.mask.from_threshold(self.image, color=(0, 0, 0), threshold=(1,1,1,1))
        self.mask.invert()
        self.overlap_mask = self.mask.overlap_mask(obstacle.sprite.mask, (-self.rect.x, -self.rect.y))
        self.impact_point = self._get_closest_impact_position() if self.overlap_mask.count() else None

    def _get_closest_impact_position(self):
        # Seems we can not access the mask coordinates, even by casting it to np.array
        width, height = self.overlap_mask.get_size()
        collisions_points = [[x, y] for x in range(width) for y in range(height) if self.overlap_mask.get_at((x, y))]
        impact_absolute_positions = np.array(self.rect.topleft) + np.array(collisions_points)
        distances = np.linalg.norm(impact_absolute_positions - self.head_position, axis=1)
        closest_point_index = np.argmin(distances)
        return impact_absolute_positions[closest_point_index]


class LineSensor(Sensor):

    def __init__(self, direction=0, distance=60, length=50, width=10):
        super().__init__(direction=direction, distance=distance, height=length, width=width)
        pygame.draw.line(self.image, 'green', (width//2, 0), (width//2, length), width)


class CircleSensor(Sensor):

    def __init__(self, direction=0, distance=60, radius=50):
        super().__init__(direction=direction, distance=distance, height=2*radius, width=2*radius)
        pygame.draw.circle(self.image, 'green', (radius, radius), radius)
