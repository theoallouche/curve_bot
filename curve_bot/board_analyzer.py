from enum import IntEnum
from base64 import b64decode
from io import BytesIO

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class AnalysisStatus(IntEnum):
    MOVING, UNCHANGED, GAME_OVER, FLYING = range(4)


class BoardAnalyzer:

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        print(f"Connected to '{self.driver.title}' tab")

        canvas = self.driver.find_element(By.ID, 'game-map')
        dims = self.driver.execute_script("const { width, height } = document.getElementById('game-map'); return {width, height}")

        border_width = int(canvas.value_of_css_property('border-width').replace("px", ""))
        native_board_dims = self.driver.execute_script("const { fieldHeight, fieldWidth } = client.room.game.gameSettings; return {fieldHeight, fieldWidth}")
        self.board_dims = {"native_width": native_board_dims["fieldWidth"],
                           "native_height": native_board_dims["fieldHeight"],
                           "native_wall_width": border_width,
                           "display_width": dims["width"] ,
                           "display_height": dims["height"] }

        self.head_position = None

        self.driver.execute_script("""

            const tmp = document.getElementById("clone-game-map");
            if (tmp) tmp.parentNode.removeChild(tmp);

            const canvas = document.getElementById("game-map");
            const newCanvas = canvas.cloneNode();
            newCanvas.setAttribute("id", "clone-game-map")
            canvas.after(newCanvas);

            document.canvas = canvas;
            document.ctx = newCanvas.getContext("2d");

            setInterval(() => {
                document.canvas.toBlob(b => {
                    b.arrayBuffer().then(arr => {
                        document.canvasBuffer = arr;
                    })
                });
            }, 100)
            document.setBlob = () => {
                document.canvas.toBlob(b => {
                    document.blob = b;
                });
                return document.blob;
            };
        """)
        # # ou getContext("webgl", {preserveDrawingBuffer: true});
        # self.driver.execute_script('document.canvas = document.getElementById("game-map");')

    def _to_screen_coordinates(self, x, y):
        x = x * self.board_dims['display_width'] / self.board_dims['native_width'] + 1 # 1pixel offset for the wall
        y = y * self.board_dims['display_height'] / self.board_dims['native_height'] + 1
        return x, y

    def get_rgb_board(self):
        blob = self.driver.execute_script("""
            return document.canvasBuffer;
            //return new Uint8Array(document.canvasBuffer);
        """)
        #data_url = self.driver.execute_script("return document.canvas.toDataURL();")
        #data_str = data_url.split(",")[1]
        #im = Image.open(BytesIO(b64decode(data_str)))
        Image.open(BytesIO(blob))
        im = Image.open(blob)
        return np.transpose(np.array(im)[:, :, :3], (1, 0, 2))

    def update(self):
        infos = self.driver.execute_script("const { x, y, angle, isAlive, numParticles } = client.room.game.round.players.find(p => p.isMyPlayer).getCurves()[0].state; return {x, y, angle, isAlive, numParticles}")
        if not infos['isAlive']:
            return AnalysisStatus.GAME_OVER
        head_position = np.array(self._to_screen_coordinates(infos['x'], infos['y']))
        if (self.head_position == head_position).all():
            return AnalysisStatus.UNCHANGED
        self.head_position = head_position
        if infos['numParticles'] > 1:
            return AnalysisStatus.MOVING
        return AnalysisStatus.FLYING
