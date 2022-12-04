==================
Curve bot
==================

Pure Python 3 package aiming to create sensor-based bot for the `Curve Crash <https://curvecrash.com/>`_ game.



Installation
==================

Just install the dependancies:

.. code-block:: bash

   pip install -r requirements.txt


Getting started
==================

Usage
-----------------

Define the board position on your screen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from curve_bot import Bot, Sensor, CircleSensor, LineSensor, LEFT, RIGHT


   board_position = {"top": 65, "left": 924, "width": 1285, "height": 1285}


| Ensure that the board contains at least a 1-pixel white border (the walls).
 | The smaller the board, the faster. Lower its size until you have at least 20 FPS in the program.
 | The board should always be visible and not covered by another window during run.
 | Example is the dimension for a 1440p monitor with the game fullscreen (I have another monitor to run the code).


Define the sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   # sensor = LineSensor(direction=0, distance=100, length=50, width=10)
   sensor = CircleSensor(direction=0, distance=100, radius=30)

The sensor is the zone near the curve head where collisions are checked.
There is currently 2 shapes available (Line and Circle).
``direction`` is a direction offset (in degrees) relative to the head direction.
``distance`` is the distance from the center of the sensor to the center of the head.


Define and run the bot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   bot = Bot(board_position, sensor, left_key='a', right_key='z')
   bot.run(framerate=60)



Implementing custom players
====================================

The move strategy being applied at each frame by the bot is define by its ``get_move`` method.

By default, it just holds left unless there is a collision detected, in which case it goes in the opposite side of the closest impact point:

.. code-block:: python

    def get_move(self):
        if self.sensor.sprite.impact_point is None:
            return LEFT
        head_to_impact_vec = self.sensor.sprite.impact_point - self.head_positions[-1]
        if np.cross(self.head_direction, head_to_impact_vec) > 0:
            return LEFT
        return RIGHT


It most case this will lead to a growing spiral.
But if the head has a wall on its left, it will "camp" the regular way.


You can easily change this strategy by directly editing this method, or just inherit from the ``Bot`` and redifinig this single method.

.. image:: https://user-images.githubusercontent.com/55620769/205485695-c331f902-48b5-4dba-8cf5-a2e990987fb8.png
  :align: center
  :width: 250


.. note:: If you prefer getting an uncolored (no ANSI characters) output (because of terminal incompatibility or for exporting purposes),
    you just need to set the ``COLOR_RENDERING = False`` at the top of ``game.py`` module.





Contribution
==================

Any contribution is welcome.

To do:
-----------------
* Doc, tests, packaging and all that stuff...
* General robustness
* Multi sensors