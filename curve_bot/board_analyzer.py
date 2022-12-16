from enum import IntEnum

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
        print(self.driver.title)
        if board_position is None:
            board_position = self._find_board()
        self.on_screen_board_position = board_position
        self.head_position = None
        self.particle = [0, 0]
        self.wall_width = wall_width
        self.on_game_board_position = self.driver.execute_script("const { fieldHeight, fieldWidth } = client.room.game.gameSettings; return {fieldHeight, fieldWidth}")

    # def _reset(self):$


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

    def _to_screen_coordinates(self, x, y):
        x = x * self.on_screen_board_position['width'] / self.on_game_board_position['fieldWidth'] + self.wall_width
        y = y * self.on_screen_board_position['height'] / self.on_game_board_position['fieldWidth'] + self.wall_width
        return x, y

    def update(self):
        infos = self.driver.execute_script("const { x, y, angle, isAlive, numParticles } = client.room.game.round.players.find(p => p.isMyPlayer).getCurves()[0].state; return {x, y, angle, isAlive, numParticles}")
        # print(infos)
        if not infos['isAlive']:
            return AnalysisStatus.GAME_OVER
        head_position = np.array(self._to_screen_coordinates(infos['x'], infos['y']))
        if (self.head_position == head_position).all():
            return AnalysisStatus.UNCHANGED
        self.head_position = head_position

        # particles = self.driver.execute_script("return Array.from(client.room.game.round.players.find(p => p.isMyPlayer).getCurves()[0].particles).map(({x1, y1}) => [x1, y1]);")
        if infos['numParticles'] > 1:
            particle = self.driver.execute_script("const { x1, y1 } = client.room.game.round.players.find(p => p.isMyPlayer).getCurves()[0].state.lastParticle; return {x1, y1};")
            self.particle = np.array(self._to_screen_coordinates(particle['x1'], particle['y1']))
            return AnalysisStatus.MOVING
        return AnalysisStatus.FLYING