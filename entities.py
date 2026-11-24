"""Classes and helper functions for game objects."""

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
