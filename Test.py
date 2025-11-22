import pygame
import math
import random
import numpy as np

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎯 Basic COD-Style FPS - Bro Edition")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BROWN = (139, 69, 19)


# Player settings
class Player:
    def __init__(self):
        self.x = 1.5
        self.y = 1.5
        self.angle = 0
        self.height = 0.5
        self.speed = 0.05
        self.rotation_speed = 0.03
        self.health = 100
        self.ammo = 30
        self.kills = 0

    def move(self, keys, map_grid):
        dx, dy = 0, 0
        if keys[pygame.K_w]:  # Forward
            dx += math.cos(self.angle) * self.speed
            dy += math.sin(self.angle) * self.speed
        if keys[pygame.K_s]:  # Backward
            dx -= math.cos(self.angle) * self.speed
            dy -= math.sin(self.angle) * self.speed
        if keys[pygame.K_a]:  # Strafe left
            dx += math.cos(self.angle - math.pi / 2) * self.speed
            dy += math.sin(self.angle - math.pi / 2) * self.speed
        if keys[pygame.K_d]:  # Strafe right
            dx += math.cos(self.angle + math.pi / 2) * self.speed
            dy += math.sin(self.angle + math.pi / 2) * self.speed

        # Collision detection
        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_x < len(map_grid[0]) and 0 <= new_y < len(map_grid):
            if map_grid[int(new_y)][int(new_x)] == 0:
                self.x = new_x
                self.y = new_y

    def rotate(self, mouse_rel):
        self.angle += mouse_rel[0] * self.rotation_speed


# Enemy class
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.speed = 0.02
        self.active = True
        self.last_shot = 0
        self.shot_cooldown = 60  # frames

    def update(self, player, map_grid):
        if not self.active:
            return

        # Simple AI: move toward player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist > 0.5:  # Don't get too close
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

            # Basic collision
            if map_grid[int(self.y)][int(self.x)] != 0:
                self.x -= (dx / dist) * self.speed
                self.y -= (dy / dist) * self.speed

    def shoot(self, player, current_time):
        if current_time - self.last_shot > self.shot_cooldown:
            self.last_shot = current_time
            # Simple hit detection
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 5:  # Only shoot if player is close enough
                if random.random() < 0.3:  # 30% accuracy
                    return True
        return False


# Bullet class
class Bullet:
    def __init__(self, x, y, angle, is_player_bullet=True):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 0.2
        self.is_player_bullet = is_player_bullet
        self.distance = 0
        self.max_distance = 10

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.distance += self.speed

    def is_active(self):
        return self.distance < self.max_distance


# Map (1 = wall, 0 = empty space)
def create_map():
    return [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 1, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 1, 0, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 1, 0, 0, 0, 1, 0, 1],
        [1, 0, 0, 1, 1, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]


# Raycasting for 3D rendering
def cast_ray(map_grid, player_x, player_y, angle):
    # Ray direction
    ray_dir_x = math.cos(angle)
    ray_dir_y = math.sin(angle)

    # Player's current map position
    map_x = int(player_x)
    map_y = int(player_y)

    # Length of ray from current position to next x or y-side
    delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
    delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30

    # Direction to step in x or y direction (either +1 or -1)
    step_x = 1 if ray_dir_x >= 0 else -1
    step_y = 1 if ray_dir_y >= 0 else -1

    # Length of ray from one x or y-side to next x or y-side
    if ray_dir_x < 0:
        side_dist_x = (player_x - map_x) * delta_dist_x
    else:
        side_dist_x = (map_x + 1.0 - player_x) * delta_dist_x

    if ray_dir_y < 0:
        side_dist_y = (player_y - map_y) * delta_dist_y
    else:
        side_dist_y = (map_y + 1.0 - player_y) * delta_dist_y

    # Perform DDA (Digital Differential Analysis)
    hit = 0
    side = 0

    while hit == 0:
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1

        # Check if ray has hit a wall
        if map_x < 0 or map_x >= len(map_grid[0]) or map_y < 0 or map_y >= len(map_grid):
            break
        if map_grid[map_y][map_x] > 0:
            hit = 1

    # Calculate distance projected on camera direction
    if side == 0:
        perp_wall_dist = (map_x - player_x + (1 - step_x) / 2) / ray_dir_x
    else:
        perp_wall_dist = (map_y - player_y + (1 - step_y) / 2) / ray_dir_y

    return perp_wall_dist, side


# Draw minimap
def draw_minimap(screen, map_grid, player, enemies, bullets):
    map_size = 150
    cell_size = map_size // len(map_grid)

    # Draw minimap background
    pygame.draw.rect(screen, DARK_GRAY, (10, HEIGHT - map_size - 10, map_size, map_size))

    # Draw walls
    for y, row in enumerate(map_grid):
        for x, cell in enumerate(row):
            if cell == 1:
                pygame.draw.rect(screen, GRAY,
                                 (10 + x * cell_size,
                                  HEIGHT - map_size - 10 + y * cell_size,
                                  cell_size, cell_size))

    # Draw player
    player_x = 10 + int(player.x * cell_size)
    player_y = HEIGHT - map_size - 10 + int(player.y * cell_size)
    pygame.draw.circle(screen, GREEN, (player_x, player_y), 3)

    # Draw player direction
    end_x = player_x + math.cos(player.angle) * 10
    end_y = player_y + math.sin(player.angle) * 10
    pygame.draw.line(screen, GREEN, (player_x, player_y), (end_x, end_y), 2)

    # Draw enemies
    for enemy in enemies:
        if enemy.active:
            enemy_x = 10 + int(enemy.x * cell_size)
            enemy_y = HEIGHT - map_size - 10 + int(enemy.y * cell_size)
            pygame.draw.circle(screen, RED, (enemy_x, enemy_y), 3)

    # Draw bullets
    for bullet in bullets:
        bullet_x = 10 + int(bullet.x * cell_size)
        bullet_y = HEIGHT - map_size - 10 + int(bullet.y * cell_size)
        color = BLUE if bullet.is_player_bullet else RED
        pygame.draw.circle(screen, color, (bullet_x, bullet_y), 2)


# Draw HUD
def draw_hud(screen, player, font):
    # Health bar
    pygame.draw.rect(screen, RED, (20, 20, 200, 20))
    pygame.draw.rect(screen, GREEN, (20, 20, player.health * 2, 20))
    pygame.draw.rect(screen, WHITE, (20, 20, 200, 20), 2)

    # Ammo
    ammo_text = font.render(f"AMMO: {player.ammo}", True, WHITE)
    screen.blit(ammo_text, (20, 50))

    # Kills
    kills_text = font.render(f"KILLS: {player.kills}", True, WHITE)
    screen.blit(kills_text, (20, 80))

    # Crosshair
    pygame.draw.line(screen, WHITE, (HALF_WIDTH - 10, HALF_HEIGHT), (HALF_WIDTH + 10, HALF_HEIGHT), 2)
    pygame.draw.line(screen, WHITE, (HALF_WIDTH, HALF_HEIGHT - 10), (HALF_WIDTH, HALF_HEIGHT + 10), 2)


# Draw weapon (simple)
def draw_weapon(screen):
    # Draw a simple weapon at bottom of screen
    weapon_color = BROWN
    # Weapon body
    pygame.draw.rect(screen, weapon_color, (WIDTH // 2 - 20, HEIGHT - 100, 40, 80))
    # Weapon barrel
    pygame.draw.rect(screen, DARK_GRAY, (WIDTH // 2 - 5, HEIGHT - 120, 10, 20))


# Main game function
def main():
    # Initialize game objects
    player = Player()
    map_grid = create_map()
    enemies = [
        Enemy(2.5, 2.5),
        Enemy(7.5, 2.5),
        Enemy(5.5, 7.5),
        Enemy(2.5, 7.5)
    ]
    bullets = []
    font = pygame.font.Font(None, 36)

    # Mouse settings
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    running = True
    frame_count = 0

    while running:
        frame_count += 1

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and player.ammo > 0:
                    # Shoot bullet
                    bullets.append(Bullet(player.x, player.y, player.angle))
                    player.ammo -= 1
            elif event.type == pygame.MOUSEBUTTONDOWN and player.ammo > 0:
                # Shoot with mouse click
                bullets.append(Bullet(player.x, player.y, player.angle))
                player.ammo -= 1

        # Get mouse movement for rotation
        mouse_rel = pygame.mouse.get_rel()
        player.rotate(mouse_rel)

        # Get keys for movement
        keys = pygame.key.get_pressed()
        player.move(keys, map_grid)

        # Update enemies
        for enemy in enemies:
            if enemy.active:
                enemy.update(player, map_grid)
                if enemy.shoot(player, frame_count):
                    player.health -= 10
                    if player.health <= 0:
                        print("Game Over! You died!")
                        running = False

        # Update bullets
        for bullet in bullets[:]:
            bullet.update()

            # Check if bullet hit a wall
            if (bullet.x < 0 or bullet.x >= len(map_grid[0]) or
                    bullet.y < 0 or bullet.y >= len(map_grid) or
                    map_grid[int(bullet.y)][int(bullet.x)] == 1):
                bullets.remove(bullet)
                continue

            # Check if bullet hit an enemy (player bullet) or player (enemy bullet)
            if bullet.is_player_bullet:
                for enemy in enemies:
                    if (enemy.active and
                            math.sqrt((bullet.x - enemy.x) ** 2 + (bullet.y - enemy.y) ** 2) < 0.5):
                        enemy.health -= 50
                        if enemy.health <= 0:
                            enemy.active = False
                            player.kills += 1
                            player.ammo += 10  # Ammo pickup
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break
            else:
                # Enemy bullet hit player
                if math.sqrt((bullet.x - player.x) ** 2 + (bullet.y - player.y) ** 2) < 0.5:
                    player.health -= 20
                    if bullet in bullets:
                        bullets.remove(bullet)

            # Remove bullet if it traveled too far
            if not bullet.is_active() and bullet in bullets:
                bullets.remove(bullet)

        # RENDER 3D VIEW
        screen.fill(BLACK)

        # Draw ceiling and floor
        pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, HALF_HEIGHT))  # Ceiling
        pygame.draw.rect(screen, BROWN, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))  # Floor

        # Raycasting - draw walls
        for x in range(WIDTH):
            # Calculate ray position and direction
            camera_x = 2 * x / WIDTH - 1  # x-coordinate in camera space
            ray_dir_x = math.cos(player.angle) + math.sin(player.angle) * camera_x
            ray_dir_y = math.sin(player.angle) - math.cos(player.angle) * camera_x

            # Cast ray
            perp_wall_dist, side = cast_ray(map_grid, player.x, player.y,
                                            math.atan2(ray_dir_y, ray_dir_x))

            # Calculate height of line to draw on screen
            line_height = int(HEIGHT / perp_wall_dist) if perp_wall_dist > 0 else HEIGHT

            # Calculate lowest and highest pixel to fill in current stripe
            draw_start = max(-line_height // 2 + HALF_HEIGHT, 0)
            draw_end = min(line_height // 2 + HALF_HEIGHT, HEIGHT)

            # Choose wall color based on side
            if perp_wall_dist > 0:
                if side == 1:
                    color = (100, 100, 100)  # Darker for y-side
                else:
                    color = (150, 150, 150)  # Lighter for x-side

                # Darken color based on distance
                darken = min(1.0, perp_wall_dist / 8)
                color = tuple(int(c * (1 - darken)) for c in color)

                # Draw the wall slice
                pygame.draw.line(screen, color, (x, draw_start), (x, draw_end), 1)

        # Draw HUD elements
        draw_hud(screen, player, font)
        draw_weapon(screen)
        draw_minimap(screen, map_grid, player, enemies, bullets)

        # Check win condition
        if all(not enemy.active for enemy in enemies):
            win_text = font.render("MISSION COMPLETE! All enemies eliminated!", True, GREEN)
            screen.blit(win_text, (WIDTH // 2 - 250, HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()