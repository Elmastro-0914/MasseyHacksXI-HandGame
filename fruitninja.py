import pygame
import random
import math
import threading
import cv2
import mediapipe as mp
import time

from collections import deque

pygame.init()

WIDTH, HEIGHT = 1980, 1080

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

smooth_buffer_size = 5
x_buffer = deque(maxlen=smooth_buffer_size)
y_buffer = deque(maxlen=smooth_buffer_size)

mainFont = pygame.font.Font("flappy.ttf", 30)

background = pygame.image.load("Image/backgroundFruitNinja.png").convert()
handopen = pygame.image.load("Image/handOpen.png").convert_alpha()
handclose = pygame.image.load("Image/handClose.png").convert_alpha()
score = pygame.transform.scale(pygame.image.load("Image/scoreFruitNinja.png").convert_alpha(), (1000*0.3, 280*0.3))
logo = pygame.image.load("Image/VegetableSamuraiLOGO.png").convert_alpha()

cauliflower = pygame.image.load("Image/cauliflower.png").convert_alpha()
beetroot = pygame.image.load("Image/beetroot.png").convert_alpha()
carrot = pygame.image.load("Image/carrot.png").convert_alpha()
lettuce = pygame.image.load("Image/lettuce.png").convert_alpha()
tomato = pygame.image.load("Image/tomato.png").convert_alpha()

WHITE = (255, 255, 255)
FRUIT_SPRITES = [cauliflower, beetroot, carrot, lettuce, tomato]
FRUIT_TYPES = [
    {'sprite': FRUIT_SPRITES[0], 'dimen': (100, 100)},
    {'sprite': FRUIT_SPRITES[1], 'dimen': (100, 100)},
    {'sprite': FRUIT_SPRITES[2], 'dimen': (100, 100)},
    {'sprite': FRUIT_SPRITES[3], 'dimen': (100, 100)},
    {'sprite': FRUIT_SPRITES[4], 'dimen': (100, 100)},
]

gravity = 0.4
fruits = []
slice_trail = []

clicked = False
prev_x, prev_y = 0, 0
movement_threshold = 0.001
curr_x, curr_y = 0, 0

start = False
high_score = 0

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.2)
mp_drawing = mp.solutions.drawing_utils

def hand_tracking():
    global clicked, prev_x, prev_y, curr_x, curr_y
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.convertScaleAbs(frame, beta=-50)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                def is_finger_closed(tip_idx, pip_idx):
                    return landmarks[tip_idx].y > landmarks[pip_idx].y

                closed_fingers = [
                    is_finger_closed(8, 6),
                    is_finger_closed(12, 10),
                    is_finger_closed(16, 14),
                    is_finger_closed(20, 18),
                ]
                clicked = all(closed_fingers)

                wrist = landmarks[0]
                curr_x, curr_y = wrist.x, wrist.y
                
                x_buffer.append(wrist.x)
                y_buffer.append(wrist.y)
                curr_x = sum(x_buffer) / len(x_buffer)
                curr_y = sum(y_buffer) / len(y_buffer)

        cv2.imshow("Hand Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

threading.Thread(target=hand_tracking, daemon=True).start()

class Fruit:
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        fruit_type = random.choice(FRUIT_TYPES)
        self.sprite = fruit_type["sprite"]
        self.width, self.height = fruit_type["dimen"]
        self.y = HEIGHT + self.height
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-25, -30)
        self.alive = True
        self.hitTime = 100

    def update(self):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        if self.y - self.height > HEIGHT:
            self.alive = False

    def draw(self, screen):
        screen.blit(self.sprite, (self.x - self.width, self.y - self.height))

    def check_collision(self, cx, cy, cr):
        dx = self.x - cx
        dy = self.y - cy
        distance = math.hypot(dx, dy)
        return distance < self.width + cr


running = True
spawn_timer = 0
scoreCount = 0
game_timer = 60  # seconds
timer_font = pygame.font.Font("flappy.ttf", 28)
game_start_time = None

while running:
    dt = clock.tick(90)
    screen.blit(background, (30, 0))

    screen.blit(logo, (1400, 100))
    screen.blit(score, (300, 100))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and not start:
            if event.key == pygame.K_SPACE:
                start = True
                scoreCount = 0
                game_start_time = time.time()
                fruits.clear()

    if not start:
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200), border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200), 5, border_radius=10)
        start_text = mainFont.render("Make a fist", True, (255, 255, 255))
        start_text2 = mainFont.render("to Start", True, (255, 255, 255))
        high_score_text = mainFont.render(f"High Score: {high_score}", True, (255, 255, 0))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, HEIGHT//2 - start_text.get_height()//2-55))
        screen.blit(start_text2, (WIDTH//2 - start_text.get_width()//2+25, HEIGHT//2 - start_text.get_height()//2))

        screen.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT//2 + 30))
        pygame.display.flip()
        if clicked:
            time.sleep(3)
            start = True
            scoreCount = 0
            game_start_time = time.time()
            fruits.clear()
        continue

    elapsed = int(time.time() - game_start_time)
    remaining = max(0, game_timer - elapsed)
    timer_text = timer_font.render(f"Time Left: {remaining} sec", True, (255, 255, 255))
    screen.blit(timer_text, (1000, 100))

    if remaining == 0:
        if scoreCount > high_score:
            high_score = scoreCount
        start = False
        continue

    scoretext = mainFont.render(f"{scoreCount}", True, (255, 255, 255))
    screen.blit(scoretext, (460, 120))
    spawn_timer += dt

    if spawn_timer > 1000:
        fruits.append(Fruit())
        spawn_timer = 0

    mouse_x, mouse_y = curr_x * WIDTH, curr_y * HEIGHT
    cursor_radius = 20

    if clicked:
        for fruit in fruits:
            if fruit.check_collision(mouse_x, mouse_y, cursor_radius):
                fruit.alive = False
                scoreCount += 1

    if clicked:
        screen.blit(handclose, (int(mouse_x)-45, int(mouse_y)-45))
    else:
        screen.blit(handopen, (int(mouse_x)-45, int(mouse_y)-45))

    fruits = [f for f in fruits if f.alive]
    for fruit in fruits:
        fruit.update()
        fruit.draw(screen)

    prev_x, prev_y = curr_x, curr_y
    pygame.display.flip()

pygame.quit()