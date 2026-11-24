"""Main game class and game loop."""

import math
import random
from pathlib import Path

import pygame
import settings as cfg

from entities import (
    Ship,
    Asteroid,
    Missile,
    Explosion,
    collides,
)

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
    MISSILE_COOLDOWN,
    INITIAL_LIVES,
    INITIAL_SCORE,
    HUD_FONT_SIZE,
    HUD_COLOR,
    HUD_MARGIN,
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
        self.missiles = []
        self.shot_timer = 0.0

        self.score = INITIAL_SCORE
        self.lives = INITIAL_LIVES
        self.playing = False
        self.has_played = False

        self.splash_rect = pygame.Rect(
            0, 0,
            cfg.SPLASH_WIDTH,
            cfg.SPLASH_HEIGHT,
        )

        self.splash_rect.center = (
            cfg.WIDTH // 2,
            cfg.HEIGHT // 2,
        )

        self.title_font = pygame.font.Font(
            None, cfg.SPLASH_TITLE_SIZE
        )

        self.splash_font = pygame.font.Font(
            None, cfg.SPLASH_TEXT_SIZE
        )
        self.explosions = []

        assets = Path(__file__).resolve().parent / "assets"

        self.explosion_sheet = pygame.image.load(
            assets / "explosion.png"
        ).convert_alpha()

        self.font = pygame.font.Font(
            None, HUD_FONT_SIZE
        )

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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if (
                    event.button == 1
                    and not self.playing
                    and not getattr(self, "explosions", [])
                    and self.splash_rect.collidepoint(event.pos)
                ):
                    self.start_game()

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def start_game(self):
        """Start a new game session."""
        self.ship = Ship()
        self.asteroids.clear()
        self.missiles.clear()

        if hasattr(self, "explosions"):
            self.explosions.clear()

        self.score = cfg.INITIAL_SCORE
        self.lives = cfg.INITIAL_LIVES
        self.spawn_timer = 0.0
        self.shot_timer = 0.0
        self.playing = True
        self.has_played = True

    def draw_splash(self):
        """Draw the central game splash screen."""
        pygame.draw.rect(
            self.screen,
            cfg.SPLASH_BACKGROUND,
            self.splash_rect,
            border_radius=16,
        )

        pygame.draw.rect(
            self.screen,
            cfg.SPLASH_BORDER,
            self.splash_rect,
            width=2,
            border_radius=16,
        )

        if self.has_played:
            heading = "GAME OVER"
            subtitle = f"Final score: {self.score}"
            action = "Click here to play again"
        else:
            heading = "ASTEROIDS"
            subtitle = "Survive the asteroid field"
            action = "Click here to start"

        lines = [
            (heading, self.title_font, 58),
            (subtitle, self.splash_font, 120),
            ("LEFT / RIGHT - Rotate",
             self.splash_font, 169),
            ("UP - Thrust",
             self.splash_font, 200),
            ("SPACE - Fire",
             self.splash_font, 231),
            (action, self.splash_font, 278),
        ]

        for label, font, offset in lines:
            image = font.render(
                label, True, cfg.SPLASH_ACCENT
            )

            rect = image.get_rect(
                center=(
                    self.splash_rect.centerx,
                    self.splash_rect.top + offset,
                )
            )

            self.screen.blit(image, rect)

    def check_collisions(self):
        """Handle projectile and spaceship collisions."""
        for missile in self.missiles[:]:
            for asteroid in self.asteroids[:]:
                if collides(missile, asteroid):
                    self.explosions.append(
                        Explosion(
                            asteroid.position,
                            self.explosion_sheet,
                        )
                    )

                    self.missiles.remove(missile)
                    self.asteroids.remove(asteroid)
                    self.score += 1
                    break

        for asteroid in self.asteroids[:]:
            if collides(self.ship, asteroid):
                self.explosions.append(
                    Explosion(
                        asteroid.position,
                        self.explosion_sheet,
                    )
                )

                self.asteroids.remove(asteroid)

                if self.lives == 0:
                    self.playing = False
                    self.asteroids.clear()
                    self.missiles.clear()
                else:
                    self.lives -= 1
                    self.ship = Ship()

                break

    def draw_hud(self):
        """Display score and remaining lives."""
        score = self.font.render(
            f"SCORE: {self.score}",
            True,
            HUD_COLOR,
        )

        lives = self.font.render(
            f"LIVES: {self.lives}",
            True,
            HUD_COLOR,
        )

        self.screen.blit(
            score, (HUD_MARGIN, HUD_MARGIN)
        )

        self.screen.blit(
            lives,
            (
                WIDTH - lives.get_width() - HUD_MARGIN,
                HUD_MARGIN,
            ),
        )

    def update(self, dt):
        """Update background position."""
        self.background_offset += BACKGROUND_SPEED * dt
        self.background_offset %= WIDTH

        for explosion in self.explosions:
            explosion.update(dt)

        self.explosions = [
            explosion
            for explosion in self.explosions
            if explosion.alive
        ]

        if not self.playing:
            return

        keys = pygame.key.get_pressed()
        self.ship.control(keys, dt)

        self.shot_timer = max(0, self.shot_timer - dt)

        if keys[pygame.K_SPACE] and self.shot_timer == 0:
            self.missiles.append(Missile(self.ship))
            self.shot_timer = MISSILE_COOLDOWN

        self.spawn_timer += dt

        if self.spawn_timer >= ASTEROID_SPAWN_INTERVAL:
            self.spawn_timer -= ASTEROID_SPAWN_INTERVAL

            if len(self.asteroids) < MAX_ASTEROIDS:
                asteroid = Asteroid.spawn(self.ship.position)
                self.asteroids.append(asteroid)

        for asteroid in self.asteroids:
            asteroid.update(dt)

        for missile in self.missiles:
            missile.update(dt)

        self.missiles = [
            missile
            for missile in self.missiles
            if missile.alive
        ]

        self.check_collisions()

    def draw(self):
        """Draw the stationary and moving backgrounds."""
        self.screen.blit(self.background, (0, 0))

        offset = int(self.background_offset)

        # Two adjacent tiles provide continuous movement.
        self.screen.blit(self.asteroid_layer, (-offset, 0))
        self.screen.blit(
            self.asteroid_layer, (WIDTH - offset, 0)
        )

        if self.playing:
            for asteroid in self.asteroids:
                asteroid.draw(self.screen)

            for missile in self.missiles:
                missile.draw(self.screen)

            self.ship.draw(self.screen)

        for explosion in self.explosions:
            explosion.draw(self.screen)

        self.draw_hud()

        if (
            not self.playing
            and not getattr(self, "explosions", [])
        ):
            self.draw_splash()

        pygame.display.flip()

    def run(self):
        """Run the main game loop."""
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, 0.05)

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
