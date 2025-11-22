import pygame
import sys
import random
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.25
FLAP_STRENGTH = -7
PIPE_SPEED = 3
PIPE_GAP = 200
PIPE_FREQUENCY = 1500  # milliseconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 180, 0)
DARK_GREEN = (0, 120, 0)
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (222, 184, 135)
GOLD = (255, 215, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird - No Assets Needed")
clock = pygame.time.Clock()

# Fonts
font_large = pygame.font.SysFont('comicsansms', 50, bold=True)
font_medium = pygame.font.SysFont('comicsansms', 36)
font_small = pygame.font.SysFont('comicsansms', 24)


# Create images programmatically (no external assets needed)
def create_bird_frames():
    frames = []
    sizes = [(40, 30), (42, 28), (38, 32)]  # Slight size variations for animation
    for i, size in enumerate(sizes):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        # Body
        pygame.draw.ellipse(surf, YELLOW, (0, 0, size[0], size[1]))
        # Wing
        wing_color = (255, 200, 0) if i == 1 else (255, 220, 0)
        pygame.draw.ellipse(surf, wing_color, (5, 10, 20, 15))
        # Eye
        pygame.draw.circle(surf, BLACK, (size[0] - 10, 8), 4)
        pygame.draw.circle(surf, WHITE, (size[0] - 12, 6), 2)
        # Beak
        pygame.draw.polygon(surf, ORANGE, [
            (size[0], 12),
            (size[0] + 10, 12),
            (size[0], 18)
        ])
        frames.append(surf)
    return frames


def create_pipe_surface(height, is_top=False):
    surf = pygame.Surface((80, height), pygame.SRCALPHA)
    # Pipe body
    pygame.draw.rect(surf, GREEN, (0, 0, 80, height))
    pygame.draw.rect(surf, DARK_GREEN, (0, 0, 80, height), 4)
    # Pipe cap
    cap_height = 30
    if is_top:
        pygame.draw.rect(surf, DARK_GREEN, (0, height - cap_height, 80, cap_height))
        pygame.draw.rect(surf, GREEN, (5, height - cap_height + 5, 70, cap_height - 10))
    else:
        pygame.draw.rect(surf, DARK_GREEN, (0, 0, 80, cap_height))
        pygame.draw.rect(surf, GREEN, (5, 5, 70, cap_height - 10))
    return surf


def create_cloud():
    surf = pygame.Surface((120, 70), pygame.SRCALPHA)
    # Draw multiple circles to create a cloud shape
    pygame.draw.ellipse(surf, (255, 255, 255, 220), (0, 20, 60, 40))
    pygame.draw.ellipse(surf, (255, 255, 255, 220), (30, 10, 70, 50))
    pygame.draw.ellipse(surf, (255, 255, 255, 220), (60, 25, 60, 35))
    return surf


# Create all game assets
bird_frames = create_bird_frames()

# Create background with gradient
background_img = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    # Create a simple sky gradient
    color_factor = 1.0 - (y / HEIGHT) * 0.3
    color = (int(135 * color_factor), int(206 * color_factor), int(235 * color_factor))
    pygame.draw.line(background_img, color, (0, y), (WIDTH, y))

# Create pipe images
pipe_top_img = create_pipe_surface(400, is_top=True)
pipe_bottom_img = create_pipe_surface(400, is_top=False)

# Create ground
ground_img = pygame.Surface((WIDTH, 100))
ground_img.fill(GROUND_COLOR)
# Add some ground texture
for i in range(20):
    x = random.randint(0, WIDTH)
    y = random.randint(0, 100)
    pygame.draw.circle(ground_img, (200, 160, 120), (x, y), 2)

# Create cloud
cloud_img = create_cloud()


# Create simple sounds programmatically
def create_flap_sound():
    sound = pygame.mixer.Sound(buffer=bytes([128] * 44100))  # Silent sound
    return sound


def create_hit_sound():
    # Create a simple beep sound
    sample_rate = 44100
    duration = 0.1
    frames = int(duration * sample_rate)
    buffer = bytearray()
    for i in range(frames):
        # Simple square wave
        value = 128 + int(100 * (1 if (i // 100) % 2 else -1))
        buffer.append(min(max(value, 0), 255))
    return pygame.mixer.Sound(buffer=bytes(buffer))


def create_score_sound():
    # Create a higher pitched beep
    sample_rate = 44100
    duration = 0.1
    frames = int(duration * sample_rate)
    buffer = bytearray()
    for i in range(frames):
        # Higher frequency square wave
        value = 128 + int(80 * (1 if (i // 50) % 2 else -1))
        buffer.append(min(max(value, 0), 255))
    return pygame.mixer.Sound(buffer=bytes(buffer))


# Create sounds
flap_sound = create_flap_sound()
hit_sound = create_hit_sound()
score_sound = create_score_sound()


class Bird:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 3  # Start higher up
        self.velocity = 0
        self.width = 40
        self.height = 30
        self.frame_index = 0
        self.animation_speed = 0.2
        self.angle = 0
        self.flap_cooldown = 0

    def flap(self):
        if self.flap_cooldown == 0:
            self.velocity = FLAP_STRENGTH
            self.flap_cooldown = 5
            flap_sound.play()

    def update(self):
        # Apply gravity
        self.velocity += GRAVITY
        self.y += self.velocity

        # Update animation
        self.frame_index += self.animation_speed
        if self.frame_index >= len(bird_frames):
            self.frame_index = 0

        # Rotate bird based on velocity
        self.angle = -self.velocity * 3
        if self.angle < -30:
            self.angle = -30
        elif self.angle > 70:
            self.angle = 70

        # Update flap cooldown
        if self.flap_cooldown > 0:
            self.flap_cooldown -= 1

        # Keep bird on screen (top only)
        if self.y < 0:
            self.y = 0
            self.velocity = 0

    def draw(self):
        # Get current frame
        frame = bird_frames[int(self.frame_index)]

        # Rotate the bird
        rotated_bird = pygame.transform.rotate(frame, self.angle)

        # Draw the bird
        rect = rotated_bird.get_rect(center=(self.x + self.width / 2, self.y + self.height / 2))
        screen.blit(rotated_bird, rect.topleft)

    def get_mask(self):
        # Return the rectangle for collision detection with some padding
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)


class Pipe:
    def __init__(self):
        self.x = WIDTH
        self.height = random.randint(150, 400)
        self.top_pipe_rect = pygame.Rect(self.x, 0, 60, self.height - PIPE_GAP // 2)
        self.bottom_pipe_rect = pygame.Rect(self.x, self.height + PIPE_GAP // 2, 60, HEIGHT)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED
        self.top_pipe_rect.x = self.x
        self.bottom_pipe_rect.x = self.x

    def draw(self):
        # Draw top pipe (flipped)
        top_pipe_height = self.height - PIPE_GAP // 2
        top_pipe = create_pipe_surface(top_pipe_height, is_top=True)
        top_pipe = pygame.transform.flip(top_pipe, False, True)
        screen.blit(top_pipe, (self.x - 10, top_pipe_height - top_pipe.get_height()))

        # Draw bottom pipe
        bottom_pipe_height = HEIGHT - (self.height + PIPE_GAP // 2)
        bottom_pipe = create_pipe_surface(bottom_pipe_height, is_top=False)
        screen.blit(bottom_pipe, (self.x - 10, self.height + PIPE_GAP // 2))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        return bird_mask.colliderect(self.top_pipe_rect) or bird_mask.colliderect(self.bottom_pipe_rect)


class Cloud:
    def __init__(self):
        self.x = WIDTH + random.randint(0, 100)
        self.y = random.randint(50, 300)
        self.speed = random.uniform(0.5, 1.5)

    def update(self):
        self.x -= self.speed
        if self.x < -cloud_img.get_width():
            self.x = WIDTH + random.randint(0, 100)
            self.y = random.randint(50, 300)

    def draw(self):
        screen.blit(cloud_img, (self.x, self.y))


def draw_floor():
    screen.blit(ground_img, (0, HEIGHT - 100))


def show_start_screen():
    screen.blit(background_img, (0, 0))

    # Draw title
    title_font = pygame.font.SysFont('comicsansms', 60, bold=True)
    title_shadow = title_font.render("Flappy Bird", True, BLACK)
    title_text = title_font.render("Flappy Bird", True, WHITE)
    screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 103))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

    # Draw instructions
    instruction_font = pygame.font.SysFont('comicsansms', 30)
    instruction = instruction_font.render("Press SPACE to start", True, WHITE)
    screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2))

    # Draw floating bird
    bird_y = HEIGHT // 2 + 100 + pygame.time.get_ticks() // 50 % 40
    frame = bird_frames[int(pygame.time.get_ticks() // 200 % len(bird_frames))]
    screen.blit(frame, (WIDTH // 2 - 20, bird_y))

    pygame.display.update()


def main():
    bird = Bird()
    pipes = []
    clouds = [Cloud() for _ in range(3)]
    score = 0
    last_pipe = pygame.time.get_ticks()
    game_active = False  # Start with start screen
    game_started = False
    ground_scroll = 0
    scroll_speed = 1

    # No background music to avoid errors

    while True:
        current_time = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not game_started:
                        # Start the game
                        game_active = True
                        game_started = True
                        last_pipe = current_time
                    elif game_active:
                        # Flap during gameplay
                        bird.flap()
                    else:
                        # Restart game after game over
                        bird = Bird()
                        pipes = []
                        score = 0
                        last_pipe = current_time
                        game_active = True

        # Draw background
        screen.blit(background_img, (0, 0))

        # Update and draw clouds
        for cloud in clouds:
            cloud.update()
            cloud.draw()

        if not game_started:
            # Show start screen
            show_start_screen()
        elif game_active:
            # Update ground scroll
            ground_scroll = (ground_scroll - scroll_speed) % 35

            # Bird update
            bird.update()

            # Generate pipes
            if current_time - last_pipe > PIPE_FREQUENCY:
                pipes.append(Pipe())
                last_pipe = current_time

            # Update and draw pipes
            for pipe in pipes[:]:
                pipe.update()

                # Check if bird passed the pipe
                if pipe.x + 80 < bird.x and not pipe.passed:
                    pipe.passed = True
                    score += 1
                    score_sound.play()

                # Remove pipes that are off screen
                if pipe.x < -80:
                    pipes.remove(pipe)

                # Check for collisions
                if pipe.collide(bird):
                    game_active = False
                    hit_sound.play()

                pipe.draw()

            # Check if bird hit the ground or ceiling
            if bird.y >= HEIGHT - 100 - bird.height:
                game_active = False
                hit_sound.play()

            # Draw bird
            bird.draw()

            # Draw score with shadow effect
            score_shadow = font_large.render(str(score), True, BLACK)
            score_display = font_large.render(str(score), True, WHITE)
            screen.blit(score_shadow, (WIDTH // 2 - score_shadow.get_width() // 2 + 2, 52))
            screen.blit(score_display, (WIDTH // 2 - score_display.get_width() // 2, 50))
        else:
            # Game over screen with semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            # Draw all game elements behind the overlay
            for pipe in pipes:
                pipe.draw()
            bird.draw()

            game_over_text = font_large.render("Game Over", True, WHITE)
            score_text = font_medium.render(f"Score: {score}", True, GOLD)
            restart_text = font_small.render("Press SPACE to restart", True, WHITE)

            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT * 2 // 3))

        # Draw floor with scrolling (only when game is active)
        if game_started:
            screen.blit(ground_img, (ground_scroll, HEIGHT - 100))
            screen.blit(ground_img, (ground_scroll + WIDTH, HEIGHT - 100))

        # Update display
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()