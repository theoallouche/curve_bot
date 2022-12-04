=========
Curve bot
=========


| Pure Python 3 package aiming to create sensor-based bot for the `Curve Crash <https://curvecrash.com/>`_ game.
| It is only meant for a 1-player game as it can not tell (yet) which curve it has the control on.
| It uses video flux to try to detect the head position and direction, and sensor around it to anticipate collisions and turn accordingly.

This is just a sandbox to figure out what could be a good local sensor-based strategy.


Installation
============

Just install the dependencies:

.. code-block:: bash

   pip install -r requirements.txt


Getting started
~~~~~~~~~~~~~~~

.. code-block:: python

   from curve_bot import Bot, CircleSensor, LineSensor


   board_position = {"top": 65, "left": 924, "width": 1285, "height": 1285}

   sensor = CircleSensor(direction=0, distance=75, radius=30)
   # sensor = LineSensor(direction=0, distance=105, length=80, width=20)

   bot = Bot(board_position, sensor, left_key='a', right_key='z')
   bot.run(framerate=60)


.. image:: https://user-images.githubusercontent.com/55620769/205488310-6ae7e76f-45c9-4ee6-9928-eebd7441beff.png
  :align: center
  :width: 900


.. note:: Once you launch the script, you should immediately click on the play window to give back the focus. Otherwise the program will start to type into whatever window is focused on !


Usage
=====


Define the board position on your screen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   board_position = {"top": 65, "left": 924, "width": 1285, "height": 1285}


| Ensure that the board contains at least a 1-pixel white border (the walls).
| The smaller the board, the faster. Lower its size until you have at least ~20 FPS in the program.
| The board should always be visible and not covered by another window during run.
| Example is the dimension for a 1440p monitor with the game fullscreen (another monitor is used to run the program).


Define the sensor
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from curve_bot import Sensor, CircleSensor, LineSensor

   sensor = CircleSensor(direction=0, distance=75, radius=30)

| The sensor is the zone near the curve head where collisions are checked.
| There is currently 2 shapes available (Line and Circle).
| ``direction`` is a direction offset (in degrees) relative to the head direction.
| ``distance`` is the distance from the center of the sensor to the center of the head.


Implementing custom strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The move strategy being applied at each frame by the bot is defined by its ``get_move`` method.

By default, it just holds left unless there is a collision detected, in which case it goes in the opposite side of the closest impact point:

.. code-block:: python

    from curve_bot import Bot, LEFT, RIGHT

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


Contribution
============

Any contribution is welcome.

To do:
~~~~~~
* Doc, tests, packaging and all that stuff...
* General robustness
* Multi sensors