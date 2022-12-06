from enum import IntEnum

import mss
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class AnalysisStatus(IntEnum):
    MOVING, UNCHANGED, GAME_OVER, FLYING = range(4)


class BoardAnalyzer:

    def __init__(self, board_position, wall_width):
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        if board_position is None:
            board_position = self._find_board()
        self.on_screen_board_position = board_position
        self.head_position = None
        self.rgb_board = None
        self.wall_width = wall_width
        self.on_game_board_position = self.driver.execute_script("const { fieldHeight, fieldWidth } = client.room.game.gameSettings; return {fieldHeight, fieldWidth}")

    def _find_board(self):
        element = self.driver.find_element(By.ID, 'game-map')
        # Assume there is equal amount of browser chrome on the left and right sides of the screen.
        canvas_x_offset = self.driver.execute_script("return window.screenX + (window.outerWidth - window.innerWidth) / 2 - window.scrollX;")
        # Assume all the browser chrome is on the top of the screen and none on the bottom.
        canvas_y_offset = self.driver.execute_script("return window.screenY + (window.outerHeight - window.innerHeight) - window.scrollY;")
        str_border_width = element.value_of_css_property('border-width')
        border_witdh = int(str_border_width.replace("px", ""))
        return {"top": element.rect["y"] + canvas_y_offset + border_witdh,
                "left": element.rect["x"] + canvas_x_offset + border_witdh,
                "width": element.size["width"] - 2*border_witdh,
                "height": element.size["height"] - 2*border_witdh}

    def update(self):
        infos = self.driver.execute_script("const { x, y, angle, isAlive, numParticles } = client.room.game.round.players.find(p => p.isMyPlayer).getCurves()[0].state; return {x, y, angle, isAlive, numParticles}")
        if not infos['isAlive']:
            return AnalysisStatus.GAME_OVER
        head_position = np.array([infos['x'] * self.on_screen_board_position['width'] / self.on_game_board_position['fieldWidth'] + self.wall_width,
                                  infos['y'] * self.on_screen_board_position['height'] / self.on_game_board_position['fieldWidth'] + self.wall_width])
        if (self.head_position == head_position).all():
            return AnalysisStatus.UNCHANGED
        self.head_position = head_position
        with mss.mss() as sct:
            self.rgb_board = np.transpose(np.flip(np.array(sct.grab(self.on_screen_board_position))[:, :, :3], -1), (1, 0, 2))
        if infos['numParticles']:
            return AnalysisStatus.MOVING
        return AnalysisStatus.FLYING