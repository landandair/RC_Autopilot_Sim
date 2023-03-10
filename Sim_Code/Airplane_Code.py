"""Holds Code for dealing with the plane vector and converting between the reference and aircraft frame of reference"""
from pygame import sprite
import pygame as pg
import Pygame_Tools as Tools
import numpy as np
from Airplane_Control import PlaneController


class FakePlane(sprite.Sprite):
    """Simulate Flight Characteristics and control system for autopilot"""

    def __init__(self, start_pos, f_trans, Controller: PlaneController):
        """Inputs:
        - Start_Pos[Home Point in Meters(x,y)]
        - f_trans[Transfer Function f(x,y) Between meter cords and pixel Cords]
        - Controller Object which Gives Deflection Angles and throttle to be fed into the plane"""
        super().__init__()
        # Disp Params
        self.og_image = pg.image.load('Assets/Plane.png')
        self.image = self.og_image
        self.rect = self.image.get_rect()
        self.rect.center = f_trans(start_pos)
        self.f_transxy = f_trans  # Translate from meters from ref point to pixels (Broken)
        # Flight Characteristics(scuffed)
        self.cd = .2
        self.cl = 1.2
        self.mass = 5  # Kg
        self.fc_tail = lambda angle: .05 * angle  # theta/m/s (needs velocity vector * dt)
        self.fc_ail = lambda angle: .05 * angle  # theta/m/s (needs velocity vector * dt)
        self.f_throttle = lambda throttle: 10 * throttle  # Force(N) (0,1)
        # Physical Params-Plane Ref
        self.thrust = 0  # N
        self.roll = 0  # radians
        self.pitch = 0  # radians
        self.yaw = 0  # radians
        self.theta = self.yaw  # Yaw angle
        self.plane_velocity = np.array((1., 0., 0.))  # (X(Forward), Y(Left Wing), Z(UP From Wing))

        # Ref Params
        self.ref_velocity = np.array((1., 0., 0.))  # (X(Forward), Y(Left Wing), Z(UP From Wing))
        self.ref_pos = np.array((.1, 0, 0))
        self.to_ref()

        # Controller
        self.controller = Controller

        Tools.rot(self)

    def update(self):
        """Main Update Loop, Runs Every Frame
        - Get Controls
        - Do Physics Calculation
        - Update Position to Image"""
        self.get_controls()
        self.do_physics()
        self.update_pos()

    def get_controls(self):
        """Gets control inputs from controller
        - Get Control from player/controller
        - Apply Controls to Plane"""
        throttle, droll, dpitch, dyaw = self.controller.get_command(self.ref_pos, (self.roll, self.pitch, self.yaw))
        self.thrust = self.f_throttle(throttle)
        self.roll += self.fc_ail(droll)
        self.pitch += self.fc_tail(dpitch)
        self.yaw += self.fc_tail(dyaw)

    def do_physics(self):
        """Handles Physics increments
        - Calculate Force of: Thrust, Lift, Drag
        - Translate to Ref Axis
        - Add Gravity Velocity Vector  (Accel*dt)
        - Multiply Ref Vel Vector * dt and add it to the position vector"""
        dt = 1/60
        # Thrust - Drag
        self.plane_velocity += np.array((self.thrust/self.mass * dt - self.plane_velocity[0]**2 * self.cd/self.mass * dt,
                                         0, self.cl * self.plane_velocity[0]**2 / self.mass * dt))
        self.to_ref()
        grav = 9.81 # m/s**2
        self.ref_velocity[2] -= grav * dt
        self.ref_pos += self.ref_velocity * dt

    def update_pos(self):
        """Update Position on the screen based on the simulation data
        - Convert Xy between chosen sim units and pixel units using function
        - set that pos to the center if the image Rect
        - Adjust angle to match yaw angle and rotate"""
        pos = self.f_transxy(self.ref_pos[0:2])
        self.rect.center = pos
        self.theta = self.yaw
        Tools.rot(self)

    def to_ref(self):
        translation = np.array(((np.cos(self.yaw) * np.cos(self.pitch), -np.cos(self.yaw) * np.sin(self.pitch) *
                                 np.sin(self.roll) - np.sin(self.yaw) * np.cos(self.roll),
                                 -np.cos(self.yaw) * np.sin(self.pitch) * np.cos(self.roll) + np.sin(self.yaw) *
                                 np.sin(self.roll)),
                                (np.sin(self.yaw) * np.cos(self.pitch), -np.sin(self.yaw)*np.sin(self.pitch)*np.sin(
                                    self.roll)+np.cos(self.yaw)*np.cos(self.roll), -np.sin(self.yaw)*np.sin(self.pitch)*
                                 np.cos(self.roll)-np.cos(self.yaw)*np.sin(self.roll)),
                                (np.sin(self.pitch), np.cos(self.pitch)*np.sin(self.roll),
                                 np.cos(self.pitch)*np.sin(self.roll))))

        self.ref_velocity = np.matmul(translation, self.plane_velocity)
