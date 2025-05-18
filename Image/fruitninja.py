import pygame
import random
import math
import threading
import cv2
import mediapipe as mp

# Shared variables
clicked = False
prev_x, prev_y = None, None
movement_threshold = 0.02
curr_x, curr_y = 0, 0

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Function for hand tracking (runs in its own thread)
def hand_tracking():
    global clicked, prev_x, prev_y, curr_x, curr_y
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = hand_landmarks.landmark

                # Check if hand is a closed fist
                def is_finger_closed(tip_idx, pip_idx):
                    return landmarks[tip_idx].y > landmarks[pip_idx].y

                closed_fingers = [
                    is_finger_closed(8, 6),
                    is_finger_closed(12, 10),
                    is_finger_closed(16, 14),
                    is_finger_closed(20, 18)
                ]
                # thumb_closed = landmarks[4].x < landmarks[3].x if landmarks[17].x < landmarks[0].x else landmarks[4].x > landmarks[3].x

                clicked = all(closed_fingers)

                # Movement detection (optional, but we keep it for now)
                wrist = landmarks[0]
                curr_x, curr_y = wrist.x, wrist.y
                if prev_x is not None and prev_y is not None:
                    dx = curr_x - prev_x
                    dy = curr_y - prev_y
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance > movement_threshold:
                        pass  # You can do more with movement here
                prev_x, prev_y = curr_x, curr_y

        cv2.imshow("Hand Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start hand tracking in a separate thread
threading.Thread(target=hand_tracking, daemon=True).start()

## ^^^ code thanks to online source https://lotalutfunnahar.medium.com/hand-recognition-with-python-guide-with-code-samples-a0b17f4cd813


# ------------------------ Pygame Game ------------------------
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
FRUIT_COLORS = [(255, 0, 0), (0, 255, 0), (255, 165, 0), (128, 0, 128)]

fruit_types = [
    {'color': FRUIT_COLORS[0], 'radius': 30},
    {'color': FRUIT_COLORS[1], 'radius': 25},
    {'color': FRUIT_COLORS[2], 'radius': 35},
    {'color': FRUIT_COLORS[3], 'radius': 28},
]

gravity = 0.4
fruits = []
slice_trail = []

class Fruit:
    def __init__(self):
        props = random.choice(fruit_types)
        self.color = props['color']
        self.radius = props['radius']
        self.x = random.randint(100, WIDTH - 100)
        self.y = HEIGHT + self.radius
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-16, -12)
        self.alive = True

    def update(self):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        if self.y - self.radius > HEIGHT:
            self.alive = False

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, (self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 1.5))

    def check_slice(self, x1, y1, x2, y2):
        d1 = math.hypot(self.x - x1, self.y - y1)
        d2 = math.hypot(self.x - x2, self.y - y2)
        direct = math.hypot(x2 - x1, y2 - y1)
        if abs((d1 + d2) - direct) < self.radius * 1.5:
            self.alive = False

# Game loop
running = True
spawn_timer = 0
last_mouse_pos = None

while running:
    screen.fill(WHITE)
    dt = clock.tick(60)
    spawn_timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    print(curr_x, curr_y)
    # Spawn fruits
    if spawn_timer > 1000:
        fruits.append(Fruit())
        spawn_timer = 0

    if clicked:
        slice_trail.append(((prev_x*800, prev_y*600), (curr_x*800, curr_y*600)))
        for fruit in fruits:
            fruit.check_slice(*(prev_x*800, prev_y*600), *(curr_x*800, curr_y*600))
    prev_x, prev_y = curr_x, curr_y
    if clicked == False:
        pygame.draw.circle(screen, (0, 0, 0), (curr_x*800, curr_y*600), 10)
    else:
        pygame.draw.circle(screen, (0, 0, 255), (curr_x*800, curr_y*600), 10)
    
    fruits = [f for f in fruits if f.alive]
    for f in fruits:
        f.update()
        f.draw(screen)

    for line in slice_trail[-10:]:
        pygame.draw.line(screen, (0, 0, 255), line[0], line[1], 2)

    pygame.display.flip()

pygame.quit()
