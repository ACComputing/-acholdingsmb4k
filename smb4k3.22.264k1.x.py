import pygame
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
GRAVITY = 0.8
JUMP_POWER = -12
PLAYER_SPEED = 5
ENEMY_SPEED = 1
FPS = 60

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_BROWN = (139, 69, 19)
BRICK_RED = (180, 60, 50)
COIN_YELLOW = (255, 215, 0)
MARIO_RED = (255, 0, 0)
MARIO_BLUE = (0, 0, 255)
MARIO_SKIN = (255, 205, 148)
MARIO_MUSTACHE = (101, 67, 33)
GOOMBA_BROWN = (101, 67, 33)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros 1-1")
clock = pygame.time.Clock()

# ----------------------------------------------------------------------
# Sound generation
# ----------------------------------------------------------------------
def generate_tone(frequency, duration, volume=0.3):
    sample_rate = pygame.mixer.get_init()[0]
    n_samples = int(sample_rate * duration)
    buffer = bytearray()
    for i in range(n_samples):
        value = math.sin(2.0 * math.pi * frequency * i / sample_rate)
        sample = int(volume * 32767 * value)
        buffer.append(sample & 0xFF)
        buffer.append((sample >> 8) & 0xFF)
    return pygame.mixer.Sound(buffer=bytes(buffer))

jump_sound = generate_tone(523, 0.2)      # C5
coin_sound = generate_tone(659, 0.1)      # E5
stomp_sound = generate_tone(440, 0.1)     # A4

# ----------------------------------------------------------------------
# Level data (World 1-1)
# ----------------------------------------------------------------------
# Tile types
TILE_EMPTY = 0
TILE_GROUND = 1
TILE_BRICK = 2
TILE_QUESTION = 3
TILE_COIN = 4
TILE_GOOMBA = 5
TILE_FLAG = 6

# Level layout (list of strings)
level_map = [
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                                                                                                                                ",
    "                                                                       GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "                 BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    "     GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
]

# Convert to tile grid
tile_grid = []
for y, row in enumerate(level_map):
    tile_row = []
    for x, ch in enumerate(row):
        if ch == 'G':
            tile_row.append(TILE_GROUND)
        elif ch == 'B':
            tile_row.append(TILE_BRICK)
        elif ch == 'Q':
            tile_row.append(TILE_QUESTION)
        elif ch == 'C':
            tile_row.append(TILE_COIN)
        elif ch == 'M':
            tile_row.append(TILE_GOOMBA)
        elif ch == 'F':
            tile_row.append(TILE_FLAG)
        else:
            tile_row.append(TILE_EMPTY)
    tile_grid.append(tile_row)

LEVEL_WIDTH = len(tile_grid[0]) * TILE_SIZE
LEVEL_HEIGHT = len(tile_grid) * TILE_SIZE

# ----------------------------------------------------------------------
# Mario sprite (16x16 pixel art, scaled to 32x32)
# ----------------------------------------------------------------------
MARIO_SPRITE = [
    "  RRRRRR      ",
    "  RRRRRR      ",
    "  RRRRRR      ",
    "RRRRRRRRRR    ",
    "RRRRRRRRRR    ",
    "RRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRR",
    "  RRRRRRRRRR  ",
    "  RR  RR  RR  ",
    "  RRRRRRRRRR  ",
    "  RRBBBBBBRR  ",
    "  RBBBBBBBBR  ",
    "  RBBBBBBBBR  ",
    "   RBBBBBBR   ",
    "    BBBBBB    ",
    "    BBBBBB    "
]

# Color mapping
def get_mario_color(char):
    if char == 'R':
        return MARIO_RED      # red (hat, overalls)
    elif char == 'B':
        return MARIO_BLUE     # blue (shirt)
    elif char == 'S':
        return MARIO_SKIN     # skin (face)
    elif char == 'E':
        return BLACK          # eye
    elif char == 'M':
        return MARIO_MUSTACHE # mustache
    elif char == 'W':
        return WHITE          # white (glove, eye highlight)
    else:
        return None           # transparent

# Pre‑render Mario surface (facing right)
mario_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
pixel_size = TILE_SIZE // 16
for row_idx, row in enumerate(MARIO_SPRITE):
    for col_idx, ch in enumerate(row):
        color = get_mario_color(ch)
        if color:
            rect = pygame.Rect(col_idx * pixel_size, row_idx * pixel_size, pixel_size, pixel_size)
            pygame.draw.rect(mario_surface, color, rect)

# Mirror for left-facing
mario_left_surface = pygame.transform.flip(mario_surface, True, False)

# ----------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.score = 0
        self.coins = 0
        self.dead = False
        self.facing_right = True

    def update(self, tiles, enemies):
        # Horizontal movement
        self.vel_x = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        self.rect.x += self.vel_x
        self.collide_with_tiles(tiles, self.vel_x, 0)

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            jump_sound.play()

        # Gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide_with_tiles(tiles, 0, self.vel_y)

        # Enemy collision
        for enemy in enemies[:]:
            if self.rect.colliderect(enemy.rect):
                if self.vel_y > 0 and self.rect.bottom - self.vel_y <= enemy.rect.top:
                    # Stomp
                    stomp_sound.play()
                    self.score += 100
                    enemies.remove(enemy)
                    self.vel_y = -8
                else:
                    self.dead = True
                    return

        # Flag collision
        for tile in tiles:
            if tile.type == TILE_FLAG and self.rect.colliderect(tile.rect):
                self.score += 1000
                return 'win'
        return None

    def collide_with_tiles(self, tiles, dx, dy):
        for tile in tiles:
            if tile.type in (TILE_GROUND, TILE_BRICK, TILE_QUESTION):
                if self.rect.colliderect(tile.rect):
                    if dx > 0:
                        self.rect.right = tile.rect.left
                    elif dx < 0:
                        self.rect.left = tile.rect.right
                    if dy > 0:
                        self.rect.bottom = tile.rect.top
                        self.on_ground = True
                        self.vel_y = 0
                    elif dy < 0:
                        self.rect.top = tile.rect.bottom
                        self.vel_y = 0

    def draw(self, surface, camera_x):
        x = self.rect.x - camera_x
        y = self.rect.y
        if self.facing_right:
            surface.blit(mario_surface, (x, y))
        else:
            surface.blit(mario_left_surface, (x, y))

class Tile:
    def __init__(self, x, y, tile_type):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = tile_type
        self.hit = False  # for question blocks

    def draw(self, surface, camera_x):
        x = self.rect.x - camera_x
        y = self.rect.y
        if self.type == TILE_GROUND:
            pygame.draw.rect(surface, GROUND_BROWN, (x, y, TILE_SIZE, TILE_SIZE))
            # Grass top
            pygame.draw.rect(surface, (0, 128, 0), (x, y, TILE_SIZE, 4))
        elif self.type == TILE_BRICK:
            pygame.draw.rect(surface, BRICK_RED, (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, (100, 30, 20), (x+4, y+4, 6, 6))
        elif self.type == TILE_QUESTION:
            if not self.hit:
                pygame.draw.rect(surface, COIN_YELLOW, (x, y, TILE_SIZE, TILE_SIZE))
                font = pygame.font.SysFont(None, 24)
                mark = font.render("?", True, WHITE)
                surface.blit(mark, (x+10, y+5))
            else:
                pygame.draw.rect(surface, BRICK_RED, (x, y, TILE_SIZE, TILE_SIZE))
        elif self.type == TILE_FLAG:
            pygame.draw.rect(surface, (255, 0, 0), (x, y, TILE_SIZE, TILE_SIZE*2))
            pygame.draw.polygon(surface, WHITE, [(x+16, y), (x+16, y+40), (x+28, y+20)])

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.collected = False
        self.anim_offset = 0

    def update(self):
        if not self.collected:
            self.anim_offset += 0.2
            if self.anim_offset > math.pi * 2:
                self.anim_offset -= math.pi * 2

    def draw(self, surface, camera_x):
        if not self.collected:
            x = self.rect.x - camera_x
            y = self.rect.y + math.sin(self.anim_offset) * 2
            pygame.draw.circle(surface, COIN_YELLOW, (x+TILE_SIZE//2, y+TILE_SIZE//2), TILE_SIZE//3)
            # Star pattern
            pygame.draw.polygon(surface, WHITE, [
                (x+14, y+12), (x+16, y+8), (x+18, y+12),
                (x+22, y+12), (x+18, y+14), (x+20, y+18),
                (x+16, y+15), (x+12, y+18), (x+14, y+14), (x+10, y+12)
            ])

class Goomba:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.direction = -1
        self.alive = True
        self.walk_cycle = 0

    def update(self, tiles):
        if not self.alive:
            return
        self.walk_cycle += 0.2
        self.rect.x += self.direction * ENEMY_SPEED
        # Simple collision: turn around if hitting a wall or falling off edge
        on_ground = False
        for tile in tiles:
            if tile.type in (TILE_GROUND, TILE_BRICK, TILE_QUESTION):
                if self.rect.colliderect(tile.rect):
                    # Hit a wall from the side
                    if tile.rect.colliderect(self.rect.left + (1 if self.direction == -1 else -1), self.rect.top, 1, TILE_SIZE):
                        self.direction *= -1
                        break
                # Check ground below feet
                if self.rect.bottom + 1 >= tile.rect.top and self.rect.bottom < tile.rect.top + 5:
                    if tile.rect.left < self.rect.centerx < tile.rect.right:
                        on_ground = True
        if not on_ground:
            self.direction *= -1

    def draw(self, surface, camera_x):
        if self.alive:
            x = self.rect.x - camera_x
            y = self.rect.y + math.sin(self.walk_cycle) * 2
            pygame.draw.rect(surface, GOOMBA_BROWN, (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, (51, 33, 16), (x+4, y+4, 6, 6))
            pygame.draw.rect(surface, (51, 33, 16), (x+22, y+4, 6, 6))

# ----------------------------------------------------------------------
# Main game loop
# ----------------------------------------------------------------------
def main():
    # Build world
    tiles = []
    coins = []
    goombas = []
    for y, row in enumerate(tile_grid):
        for x, tile_type in enumerate(row):
            if tile_type != TILE_EMPTY:
                if tile_type == TILE_COIN:
                    coins.append(Coin(x*TILE_SIZE, y*TILE_SIZE))
                elif tile_type == TILE_GOOMBA:
                    goombas.append(Goomba(x*TILE_SIZE, y*TILE_SIZE))
                else:
                    tiles.append(Tile(x*TILE_SIZE, y*TILE_SIZE, tile_type))

    player = Player(100, 300)
    camera_x = 0
    game_over = False
    win = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_over and event.key == pygame.K_SPACE:
                    return True  # restart

        if game_over:
            screen.fill(BLACK)
            font = pygame.font.SysFont(None, 48)
            text = font.render("YOU WIN!" if win else "GAME OVER! Press SPACE to restart", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            pygame.display.update()
            clock.tick(10)
            continue

        # Update coins
        for coin in coins[:]:
            coin.update()
            if not coin.collected and player.rect.colliderect(coin.rect):
                coin.collected = True
                coin_sound.play()
                player.score += 100
                player.coins += 1

        # Update enemies
        for goomba in goombas:
            goomba.update(tiles)

        # Update player
        result = player.update(tiles, goombas)
        if result == 'win':
            win = True
            game_over = True
        elif player.dead:
            game_over = True

        # Camera scroll
        target_x = player.rect.centerx - SCREEN_WIDTH // 2
        camera_x = max(0, min(target_x, LEVEL_WIDTH - SCREEN_WIDTH))

        # Draw
        screen.fill(SKY_BLUE)
        for tile in tiles:
            tile.draw(screen, camera_x)
        for coin in coins:
            coin.draw(screen, camera_x)
        for goomba in goombas:
            goomba.draw(screen, camera_x)
        player.draw(screen, camera_x)

        # UI
        font = pygame.font.SysFont(None, 24)
        score_text = font.render(f"Score: {player.score}", True, WHITE)
        coin_text = font.render(f"Coins: {player.coins}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(coin_text, (10, 40))

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Restart loop
    while True:
        if not main():
            break
