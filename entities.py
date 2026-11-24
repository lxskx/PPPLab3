"""Classes and helper functions for game objects."""

import math
import random

import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SHIP_SIZE,
    SHIP_RADIUS,
    SHIP_ROTATION_SPEED,
    SHIP_ACCELERATION,
    SHIP_MAX_SPEED,
    SHIP_DRAG,
    SHIP_STOP_SPEED,
    SHIP_COLOR,
    ENGINE_COLOR,
    ASTEROID_MIN_RADIUS,
    ASTEROID_MAX_RADIUS,
    ASTEROID_MIN_SPEED,
    ASTEROID_MAX_SPEED,
    ASTEROID_ROTATION_SPEED,
    ASTEROID_SAFE_DISTANCE,
    ASTEROID_COLOR,
    ASTEROID_OUTLINE,
    MISSILE_SPEED,
    MISSILE_LIFETIME,
    MISSILE_RADIUS,
    MISSILE_COLOR,
)


def draw_wrapped(screen, image, position):
    """Draw an image on both sides of a screen boundary."""
    for dx in (-WIDTH, 0, WIDTH):
        for dy in (-HEIGHT, 0, HEIGHT):
            rect = image.get_rect(
                center=(
                    round(position.x + dx),
                    round(position.y + dy),
                )
            )

            if rect.colliderect(screen.get_rect()):
                screen.blit(image, rect)


class GameObject:
    """Base class for moving objects."""

    def __init__(self, position, velocity, angle, radius):
        """Initialize position, velocity, angle and radius."""
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.angle = angle
        self.radius = radius
        self.angular_velocity = 0.0
        self.image = None

    def wrap_position(self):
        """Move an object through opposite screen boundaries."""
        self.position.x %= WIDTH
        self.position.y %= HEIGHT

    def update(self, dt):
        """Update position and rotation."""
        self.position += self.velocity * dt
        self.angle += self.angular_velocity * dt
        self.angle %= 360

        self.wrap_position()

    def draw(self, screen):
        """Draw the rotated object."""
        image = pygame.transform.rotate(
            self.image, -self.angle
        )

        draw_wrapped(screen, image, self.position)


class Ship(GameObject):
    """Player-controlled spaceship."""

    def __init__(self):
        """Create a stationary ship at the screen center."""
        super().__init__(
            (WIDTH / 2, HEIGHT / 2),
            (0, 0),
            270,
            SHIP_RADIUS,
        )

        self.normal_image = self.create_image(False)
        self.engine_image = self.create_image(True)
        self.image = self.normal_image

    @staticmethod
    def create_image(engine):
        """Create a ship image with an optional engine flame."""
        size = SHIP_SIZE * 3
        center = size // 2

        surface = pygame.Surface(
            (size, size), pygame.SRCALPHA
        )

        points = [
            (center + SHIP_SIZE, center),
            (center - 15, center - 13),
            (center - 8, center),
            (center - 15, center + 13),
        ]

        if engine:
            flame = [
                (center - 10, center - 7),
                (center - 29, center),
                (center - 10, center + 7),
            ]

            pygame.draw.polygon(
                surface, ENGINE_COLOR, flame
            )

        pygame.draw.polygon(
            surface, (35, 55, 80), points
        )

        pygame.draw.polygon(
            surface, SHIP_COLOR, points, 2
        )

        return surface

    def direction(self):
        """Return the vector pointing towards the ship nose."""
        return pygame.Vector2(1, 0).rotate(self.angle)

    def control(self, keys, dt):
        """Process keyboard input and ship acceleration."""
        if keys[pygame.K_LEFT]:
            self.angle -= SHIP_ROTATION_SPEED * dt

        if keys[pygame.K_RIGHT]:
            self.angle += SHIP_ROTATION_SPEED * dt

        if keys[pygame.K_UP]:
            self.velocity += (
                self.direction() * SHIP_ACCELERATION * dt
            )

            self.image = self.engine_image
        else:
            self.velocity *= max(0, 1 - SHIP_DRAG * dt)
            self.image = self.normal_image

            if self.velocity.length() < SHIP_STOP_SPEED:
                self.velocity.update(0, 0)

        if self.velocity.length() > SHIP_MAX_SPEED:
            self.velocity.scale_to_length(SHIP_MAX_SPEED)

        self.update(dt)


def toroidal_distance(first, second):
    """Calculate the shortest distance on the wrapped field."""
    dx = abs(first.x - second.x)
    dy = abs(first.y - second.y)

    dx = min(dx, WIDTH - dx)
    dy = min(dy, HEIGHT - dy)

    return math.hypot(dx, dy)


class Asteroid(GameObject):
    """A randomly generated moving asteroid."""

    def __init__(self, position):
        """Initialize random size, movement and rotation."""
        radius = random.randint(
            ASTEROID_MIN_RADIUS,
            ASTEROID_MAX_RADIUS,
        )

        direction = random.uniform(0, 360)

        speed = random.uniform(
            ASTEROID_MIN_SPEED,
            ASTEROID_MAX_SPEED,
        )

        velocity = pygame.Vector2(speed, 0).rotate(
            direction
        )

        super().__init__(
            position,
            velocity,
            random.uniform(0, 360),
            radius,
        )

        self.angular_velocity = random.uniform(
            -ASTEROID_ROTATION_SPEED,
            ASTEROID_ROTATION_SPEED,
        )

        self.image = self.create_image()

    def create_image(self):
        """Create an irregular rocky asteroid image."""
        radius = self.radius
        size = radius * 2 + 8
        center = size // 2

        surface = pygame.Surface(
            (size, size), pygame.SRCALPHA
        )

        points = []

        for i in range(11):
            angle = 2 * math.pi * i / 11
            distance = radius * random.uniform(0.7, 1.0)

            x = center + math.cos(angle) * distance
            y = center + math.sin(angle) * distance

            points.append((round(x), round(y)))

        pygame.draw.polygon(
            surface, ASTEROID_COLOR, points
        )

        pygame.draw.polygon(
            surface, ASTEROID_OUTLINE, points, 2
        )

        return surface

    @classmethod
    def spawn(cls, ship_position):
        """Spawn an asteroid away from the player's ship."""
        while True:
            position = pygame.Vector2(
                random.randrange(WIDTH),
                random.randrange(HEIGHT),
            )

            if toroidal_distance(
                position, ship_position
            ) >= ASTEROID_SAFE_DISTANCE:
                return cls(position)


class Missile(GameObject):
    """A short-lived projectile fired by the ship."""

    def __init__(self, ship):
        """Create a missile at the nose of the ship."""
        direction = ship.direction()

        position = (
            ship.position + direction * (SHIP_SIZE + 5)
        )

        velocity = direction * MISSILE_SPEED

        super().__init__(
            position,
            velocity,
            ship.angle,
            MISSILE_RADIUS,
        )

        self.age = 0.0
        self.image = self.create_image()
        self.wrap_position()

    @staticmethod
    def create_image():
        """Create the projectile sprite."""
        surface = pygame.Surface(
            (14, 8), pygame.SRCALPHA
        )

        pygame.draw.ellipse(
            surface,
            MISSILE_COLOR,
            (0, 1, 14, 6),
        )

        return surface

    @property
    def alive(self):
        """Check whether the missile lifetime has expired."""
        return self.age < MISSILE_LIFETIME

    def update(self, dt):
        """Move the missile and increase its age."""
        super().update(dt)
        self.age += dt


def collides(first, second):
    """Check collision between two circular hitboxes."""
    distance = toroidal_distance(
        first.position,
        second.position,
    )

    return distance <= first.radius + second.radius
