import pgzrun
import random
import math
from pygame import Rect

WIDTH = 768
HEIGHT = 768
TITLE = "Why did the chicken cross the road?"
game_state = "menu"

# Música e sons
music.set_volume(0.3)
sound_on = True
music_on = True

# Sprites da galinha
chicken_idle = "chicken_idle1"
chicken_walk = ["chicken_walk1", "chicken_walk2"]

class Chicken:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.speed = 4
        self.image = chicken_idle
        self.frame = 0
        self.frame_timer = 0
        self.hitbox = Rect(self.x - 16, self.y - 16, 32, 32)

    def move(self):
        keys = keyboard
        moved = False
        if keys.up: self.y -= self.speed; moved = True
        elif keys.down: self.y += self.speed; moved = True
        if keys.left: self.x -= self.speed; moved = True
        elif keys.right: self.x += self.speed; moved = True

        self.x = max(20, min(WIDTH - 20, self.x))
        self.y = max(20, min(HEIGHT - 20, self.y))
        self.hitbox = Rect(self.x - 16, self.y - 16, 32, 32)

        if moved:
            self.animate()
        else:
            self.image = chicken_idle

    def animate(self):
        self.frame_timer += 1
        if self.frame_timer >= 10:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % len(chicken_walk)
            self.image = chicken_walk[self.frame]

    def draw(self):
        screen.blit(self.image, (self.x - 32, self.y - 32))

class Car:
    def __init__(self, y):
        self.x = WIDTH + random.randint(0, 400)
        self.y = y
        self.speed = random.randint(2, 5)
        self.image = "car1"
        self.hitbox = Rect(self.x + 20, self.y + 40, 160, 120)

    def move(self):
        self.x -= self.speed
        if self.x < -80:
            self.x = WIDTH + random.randint(100, 300)
            self.speed = random.randint(2, 5)
        self.hitbox = Rect(self.x + 20, self.y + 40, 160, 120)

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

# Inicialização
chicken = Chicken()
car_rows = [200, 300, 400, 500]
cars = [Car(y) for y in car_rows]

def reset_game():
    global chicken, cars, game_state
    chicken = Chicken()
    cars = [Car(y) for y in car_rows]
    game_state = "playing"

def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        music.play("chicken_theme")
    else:
        music.stop()

def toggle_sound():
    global sound_on
    sound_on = not sound_on

def draw_menu():
    screen.clear()
    screen.blit("road_bg", (0, 0))
    screen.draw.text("Why did the chicken cross the road?", center=(WIDTH // 2, 150), fontsize=60, color="white")
    screen.draw.text("Start Game", center=(WIDTH // 2, 250), fontsize=40, color="yellow")
    screen.draw.text(f"Music: {'On' if music_on else 'Off'}", center=(WIDTH // 2, 310), fontsize=35, color="lightblue")
    screen.draw.text(f"Sound: {'On' if sound_on else 'Off'}", center=(WIDTH // 2, 360), fontsize=35, color="lightblue")
    screen.draw.text("Exit", center=(WIDTH // 2, 410), fontsize=35, color="red")

def draw():
    screen.clear()
    screen.blit("road_bg", (0, 0))

    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        chicken.draw()
        for car in cars:
            car.draw()
    elif game_state == "gameover":
        screen.draw.text(" Game Over! Press R to Restart ", center=(WIDTH//2, HEIGHT//2), fontsize=50, color="red")
    elif game_state == "win":
        screen.draw.text("You made it to the other side!\nPress R to Restart", center=(WIDTH // 2, HEIGHT // 2), fontsize=50, color="green")

def update():
    global game_state
    if game_state == "playing":
        chicken.move()
        for car in cars:
            car.move()
            if chicken.hitbox.colliderect(car.hitbox):
                if sound_on:
                    sounds.honk.play()
                game_state = "gameover"
        if chicken.y < 60:
            game_state = "win"

def on_key_down(key):
    global game_state
    if game_state in ["gameover", "win"]:
        if key == keys.R:
            reset_game()
    elif key == keys.ESCAPE:
        game_state = "menu"
        music.stop()

def on_mouse_down(pos):
    global game_state
    if game_state == "menu":
        x, y = pos
        if 230 < y < 270:  # Start Game
            game_state = "playing"
            reset_game()
            if music_on:
                music.play("chicken_theme")
        elif 290 < y < 330:  # Toggle Music
            toggle_music()
        elif 340 < y < 380:  # Toggle Sound
            toggle_sound()
        elif 390 < y < 430:  # Exit
            exit()

pgzrun.go()
