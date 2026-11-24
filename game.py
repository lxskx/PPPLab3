"""Main game class and game loop."""

import math
import random

import pygame

from entities import Ship, Asteroid

from settings import (
    WIDTH,
    HEIGHT,
    FPS,
    TITLE,
    BACKGROUND_COLOR,
    STAR_COLORS,
    STAR_COUNT,
    BACKGROUND_ASTEROIDS,
    BACKGROUND_SPEED,
    BACKGROUND_ALPHA,
    BACKGROUND_SEED,
    ASTEROID_SPAWN_INTERVAL,
    MAX_ASTEROIDS,
)


class Game:
    """Manage the game window, events and background animation."""

    def __init__(self):
        """Initialize the game."""
        pygame.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.background = self.create_background()
        self.asteroid_layer = self.create_asteroid_layer()
        self.background_offset = 0.0
        self.ship = Ship()
        self.asteroids = []
        self.spawn_timer = 0.0

    def create_background(self):
        """Create a stationary background with stars."""
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill(BACKGROUND_COLOR)

        rng = random.Random(BACKGROUND_SEED)

        for _ in range(STAR_COUNT):
            x = rng.randrange(WIDTH)
            y = rng.randrange(HEIGHT)
            radius = rng.randint(1, 2)
            color = rng.choice(STAR_COLORS)

            pygame.draw.circle(
                surface, color, (x, y), radius
            )

        return surface

    def create_asteroid_layer(self):
        """Create a transparent background asteroid tile."""
        surface = pygame.Surface(
            (WIDTH, HEIGHT), pygame.SRCALPHA
        )

        rng = random.Random(BACKGROUND_SEED + 1)

        for _ in range(BACKGROUND_ASTEROIDS):
            x = rng.randint(60, WIDTH - 60)
            y = rng.randint(60, HEIGHT - 60)
            radius = rng.randint(15, 45)

            points = []

            for i in range(9):
                angle = 2 * math.pi * i / 9
                distance = radius * rng.uniform(0.7, 1.2)

                px = x + math.cos(angle) * distance
                py = y + math.sin(angle) * distance

                points.append((int(px), int(py)))

            pygame.draw.polygon(
                surface, (100, 110, 135), points
            )

            pygame.draw.polygon(
                surface, (150, 160, 185), points, 2
            )

        surface.set_alpha(BACKGROUND_ALPHA)

        return surface

    def handle_events(self):
        """Process window and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self, dt):
        """Update background position."""
        self.background_offset += BACKGROUND_SPEED * dt
        self.background_offset %= WIDTH

        keys = pygame.key.get_pressed()
        self.ship.control(keys, dt)

        self.spawn_timer += dt

        if self.spawn_timer >= ASTEROID_SPAWN_INTERVAL:
            self.spawn_timer -= ASTEROID_SPAWN_INTERVAL

            if len(self.asteroids) < MAX_ASTEROIDS:
                asteroid = Asteroid.spawn(self.ship.position)
                self.asteroids.append(asteroid)

        for asteroid in self.asteroids:
            asteroid.update(dt)

    def draw(self):
        """Draw the stationary and moving backgrounds."""
        self.screen.blit(self.background, (0, 0))

        offset = int(self.background_offset)

        # Two adjacent tiles provide continuous movement.
        self.screen.blit(self.asteroid_layer, (-offset, 0))
        self.screen.blit(
            self.asteroid_layer, (WIDTH - offset, 0)
        )

        for asteroid in self.asteroids:
            asteroid.draw(self.screen)

        self.ship.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """Run the main game loop."""
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
