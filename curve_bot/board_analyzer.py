from enum import IntEnum

import cv2
import mss
import numpy as np


class AnalysisStatus(IntEnum):
    SUCCESS, UNCHANGED_BOARD, UNFOUND_HEAD, GAME_OVER = range(4)


class BoardAnalyzer:

    def __init__(self, board_position):
        self.board_position = board_position
        self.head_position = None
        self.previous_rgb_board = np.zeros((board_position["width"], board_position["height"], 3), dtype=np.uint8)
        self.current_rgb_board = np.zeros((board_position["width"], board_position["height"], 3), dtype=np.uint8)
        self.same_frame_cpt = 0

    def get_rgb_board(self):
        with mss.mss() as sct:
            return np.transpose(np.flip(np.array(sct.grab(self.board_position))[:, :, :3], -1), (1, 0, 2))

    def get_head_position(self):
        # RGB to gray + binarization
        new_im = cv2.cvtColor(self.current_rgb_board, cv2.COLOR_RGB2GRAY)
        old_im = cv2.cvtColor(self.previous_rgb_board, cv2.COLOR_RGB2GRAY)
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

    def update(self, n_frames_before_reset=90):
        rgb_board = self.get_rgb_board()

        if (rgb_board == self.previous_rgb_board).all():
            self.same_frame_cpt += 1
            # If the screen has not changed for a long time, it's most likely game over
            if self.same_frame_cpt >= n_frames_before_reset:
                self.__init__(self.board_position)
                return AnalysisStatus.GAME_OVER
            return AnalysisStatus.UNCHANGED_BOARD

        self.previous_rgb_board = self.current_rgb_board
        self.current_rgb_board = rgb_board
        try:
            self.head_position = self.get_head_position()
        except (ValueError, ZeroDivisionError) as e:
            # print(f"Cant find the head ({e})")
            return AnalysisStatus.UNFOUND_HEAD
        return AnalysisStatus.SUCCESS