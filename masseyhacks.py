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


menuBG = pygame.image.load("Image/menuBG.png")
logo = pygame.image.load("Image/logo.png")


game = ""

# MediaPipe initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils


def show_menu():
    menu_running = True
    selected_game = None

    BUTTON_WIDTH = 400
    BUTTON_HEIGHT = 150
    BUTTON_SPACING = 80

    button_font = pygame.font.SysFont("arial", 60)
    title_font = pygame.font.SysFont("arial", 100, bold=True)

    play_ninja_rect = pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 - BUTTON_HEIGHT - BUTTON_SPACING // 2, BUTTON_WIDTH, BUTTON_HEIGHT)
    play_flappy_rect = pygame.Rect(WIDTH // 2 - BUTTON_WIDTH // 2, HEIGHT // 2 + BUTTON_SPACING // 2, BUTTON_WIDTH, BUTTON_HEIGHT)

    while menu_running:
        screen.blit(menuBG, (30, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        mouse_x, mouse_y = curr_x * WIDTH, curr_y * HEIGHT

        # Draw buttons
        def draw_button(rect, text, hover):
            color = (200, 0, 0) if hover else (100, 0, 0)
            pygame.draw.rect(screen, color, rect, border_radius=20)
            pygame.draw.rect(screen, (255, 255, 255), rect, 4, border_radius=20)
            text_surf = button_font.render(text, True, WHITE)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

        ninja_hover = play_ninja_rect.collidepoint(mouse_x, mouse_y)
        flappy_hover = play_flappy_rect.collidepoint(mouse_x, mouse_y)

        draw_button(play_ninja_rect, "Play Fruit Ninja", ninja_hover)
        draw_button(play_flappy_rect, "Play Flappy Bird", flappy_hover)

        title = title_font.render("Gesture Game Menu", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        # Draw hand image
        if clicked:
            screen.blit(handclose, (mouse_x, mouse_y))
        else:
            screen.blit(handclose, (mouse_x, mouse_y))

        pygame.display.flip()

        # Check gesture-based selection
        if clicked:
            if ninja_hover:
                selected_game = "ninja"
                menu_running = False
            elif flappy_hover:
                selected_game = "flappy"
                menu_running = False

        clock.tick(60)

    return selected_game

# Launch gesture menu
game = show_menu()
    

if game == "ninja":
    while running and game == "ninja":
        dt = clock.tick(90)
        screen.blit(background, (30, 0))

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


elif game == "flappy":

    RED = (255, 0, 0)
    GREY = (127, 127, 127)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)
    WHITE = (255, 255, 255)
    myClock = pygame.time.Clock()
    running = True

    currX, currY = 1, 1

    

    prevX, prevY = 0, 0
    threading.Thread(target=hand_tracking, daemon=True).start()

    score = 0
    highest = 0
    backgroundx = 0
    goosenum = 0
    bird_y = 540
    gravity = 0.2
    velocity = 0
    jump_strength = -10

    background_img = pygame.image.load("Image/background.png").convert_alpha()
    backgroundtop_img = pygame.image.load("Image/backgroundtop.png").convert_alpha()
    end_img = pygame.image.load("Image/end.png")
    box_img = pygame.image.load("Image/box.png")

    positionx = [1000, 2000, 3000]
    positiony = [random.randint(500, 980), random.randint(500, 980), random.randint(500, 980)]
    spacing = [(125, 55), (115, 25), (145, 75)]
    adding = [False, False, False]
    died = False
    start = True
    firstdied = True
    goose_img = pygame.image.load("Image/goose.png").convert()
    goose_rect = pygame.Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())

    # Main loop
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
                        
        if not died:              
            if not start:
                # Apply gravity
                velocity += gravity
                bird_y += velocity
                            
            #Setting the background
            screen.blit(background_img,(backgroundx+30,51))
            screen.blit(background_img,(backgroundx+30+1735,51))
            screen.blit(background_img,(backgroundx+30+1735*2,51))
            screen.blit(backgroundtop_img,(215,0))
            if not start:
                backgroundx-=8     #4 or 8
                if backgroundx<-1735:
                    backgroundx = 0
                for i in range(3):
                    if positionx[i] == -184:
                        positionx[i] = 3000
                        positiony[i] = random.randint(400,980)
                        adding[i] = False  
                    else:
                        positionx[i]= positionx[i]-8      #4 or 8

            for i in range(3):
                pipe_down_img = pygame.image.load("Image/buildingdown.png").convert() #.convert_alpha()
                pipe_up_img = pygame.image.load("Image/buildingup.png").convert() #.convert_alpha()

                pipe_down_pos = (positionx[i], positiony[i])
                pipe_up_pos = (positionx[i], positiony[i] - 500 - 875)

                screen.blit(pipe_down_img, pipe_down_pos)
                screen.blit(pipe_up_img, pipe_up_pos)

                #Pixel-perfect collision detection with pipe_down
                pipe_down_rect = pygame.Rect(*pipe_down_pos, pipe_down_img.get_width(), pipe_down_img.get_height())
                if goose_rect.colliderect(pipe_down_rect):
                    for x in range(goose_rect.w):
                        for y in range(goose_rect.h):
                            gx = x
                            gy = y
                            if goose_img.get_at((gx, gy))[3] > 0:
                                px = goose_rect.x + x - pipe_down_pos[0]
                                py = goose_rect.y + y - pipe_down_pos[1]
                                if 0 <= px < pipe_down_img.get_width() and 0 <= py < pipe_down_img.get_height():
                                    if pipe_down_img.get_at((px, py))[3] > 0:
                                        died = True
                                        break

                #Pixel-perfect collision detection with pipe_up
                pipe_up_rect = pygame.Rect(*pipe_up_pos, pipe_up_img.get_width(), pipe_up_img.get_height())
                if goose_rect.colliderect(pipe_up_rect):
                    for x in range(goose_rect.w):
                        for y in range(goose_rect.h):
                            gx = x
                            gy = y
                            if goose_img.get_at((gx, gy))[3] > 0:
                                px = goose_rect.x + x - pipe_up_pos[0]
                                py = goose_rect.y + y - pipe_up_pos[1]  
                                if 0 <= px < pipe_up_img.get_width() and 0 <= py < pipe_up_img.get_height():
                                    if pipe_up_img.get_at((px, py))[3] > 0:
                                        died = True
                                        break
            #Score system
            screen.blit(pygame.image.load("Image/score.png"),(30,0))
            flappyfont = pygame.font.Font("flappy.ttf",30)
            scoretext = flappyfont.render(f"{score}",True,WHITE)
            scoretext2 = flappyfont.render(f"{score}",True,BLACK)
            screen.blit(scoretext2,(182,7))
            screen.blit(scoretext,(180,5))
        
            if abs(currY - prevY) < 0.3 and abs(currY - prevY) > 0.03:
                if currY - prevY < 0:
                    velocity = jump_strength
                    pygame.mixer.Sound.play(pygame.mixer.Sound("Sound/flying.mp3"))
            

            if start:
                goose_img = pygame.image.load("Image/goose.png").convert_alpha()
                goose_rect = pygame.Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                screen.blit(goose_img, goose_rect)
                
                screen.blit(pygame.image.load("Image/start.png"),(300,200))
                flappyfont = pygame.font.Font("flappy.ttf",30)
                beginning = flappyfont.render(f"Close fist to start",True,WHITE)
                screen.blit(beginning,(300,300))
                pygame.display.flip()
            else:
                '''Goose'''
                #Apply gravity
                goosenum+=1
                goosenum= goosenum%15
                velocity += gravity
                bird_y += velocity    
                if bird_y > 1005:
                    bird_y = 1005
                    velocity = 0
                elif bird_y <= 0:
                    bird_y = 0
                    velocity = 0

                #Bliting the bird
                if goosenum <= 5:
                    goose_img = pygame.image.load("Image/goose.png").convert_alpha()
                    goose_rect = pygame.Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                    screen.blit(goose_img, goose_rect)     
                elif goosenum<=10:
                    goose_img = pygame.image.load("Image/gooseup.png").convert_alpha()
                    goose_rect = pygame.Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                    screen.blit(goose_img, goose_rect)  
                else:
                    goose_img = pygame.image.load("Image/goosedown.png").convert_alpha()
                    goose_rect = pygame.Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                    screen.blit(goose_img, goose_rect)
                pygame.display.flip()

            for i in range(3):
                if positionx[i]+179 <= 400:
                    if not adding[i]:
                        score +=1
                        adding[i] = True
                        pygame.mixer.Sound.play(pygame.mixer.Sound("Sound/point.mp3"))
        #Death screen
        else:
            if firstdied:
                pygame.mixer.Sound.play(pygame.mixer.Sound("Sound/die.mp3"))
                firstdied = False
                screen.blit(end_img,(300,200))
                screen.blit(box_img,(300,300))
                if highest <= score:
                    highest = score
                flappyfont = pygame.font.Font("flappy.ttf",30)
                scoring = flappyfont.render(f"{score}",True,WHITE)
                screen.blit(scoring,(350,360))
                highesting = flappyfont.render(f"{highest}",True,WHITE)
                screen.blit(highesting,(560,360))
                restart = flappyfont.render(f"Close fist",True,WHITE)
                restart2 = flappyfont.render(f"to restart",True,WHITE)
                screen.blit(restart,(350,410))
                screen.blit(restart2,(350,455))

        prevX, prevY = currX, currY
        myClock.tick(60)

        pygame.display.flip()
        

    pygame.quit()






















































# from pygame import *
# from random import *

# init()
# font.init()

# #Screen
# screen = display.set_mode((1920, 1080)) 

# RED=(255,0,0)
# GREY=(127,127,127)
# BLACK=(0,0,0)
# BLUE=(0,0,255)
# GREEN=(0,255,0)
# YELLOW=(255,255,0)
# WHITE=(255,255,255)
# myClock=time.Clock()
# running=True


# '''Setting the variables'''
# gravity = 0
# score = 0
# highest = 0
# backgroundx = 0
# background_img = image.load("Image/background.png").convert()
# backgroundtop_img = image.load("Image/backgroundtop.png").convert()
# died = False
# start = True
# firstdied = True

# #For the goose
# bird_y = 540
# gravity = 0.5
# velocity = 0
# jump_strength = -10

# goosenum = 0
# positionx = [1000,1840,2680]
# positiony = [randint(400,980),randint(400,980),randint(400,980)]

# spacing = [(125,55),(115,25),(145,75)]
# adding = [False,False,False]


# goose_img = image.load("Image/goose.png").convert()
# goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())

# while running:
#     for evt in event.get():
#         if evt.type==QUIT:
#             running=False
#         if evt.type == KEYDOWN:
#             if evt.key == K_SPACE:
#                 if died:
#                     score = 0
#                     bird_y = 540
#                     velocity = 0
#                     positionx = [1000,1840,2680]
#                     positiony = [randint(400,980),randint(400,980),randint(400,980)]
#                     adding = [False,False,False]
#                     start = True
#                     died = False
#                     firstdied = True
#                 elif start:
#                     start = False
#                     mixer.Sound.play(mixer.Sound("Sound/start.mp3"))
#                 else:
#                     velocity = jump_strength
#                     mixer.Sound.play(mixer.Sound("Sound/flying.mp3"))
#     if not died:              
#         if not start:
#             # Apply gravity
#             velocity += gravity
#             bird_y += velocity
                        
#         #Setting the background
#         screen.blit(background_img,(backgroundx,51))
#         screen.blit(background_img,(backgroundx+1735,51))
#         screen.blit(background_img,(backgroundx+1735*2,51))
#         screen.blit(backgroundtop_img,(185,0))
#         if not start:
#             backgroundx-=8     #4 or 8
#             if backgroundx<-1735:
#                 backgroundx = 0
#             for i in range(3):
#                 if positionx[i] == -184:
#                     positionx[i] = 2680
#                     positiony[i] = randint(400,980)
#                     adding[i] = False  
#                 else:
#                     positionx[i]= positionx[i]-8      #4 or 8

#         for i in range(3):
#             pipe_down_img = image.load("Image/buildingdown.png").convert() #.convert_alpha()
#             pipe_up_img = image.load("Image/buildingup.png").convert() #.convert_alpha()

#             pipe_down_pos = (positionx[i], positiony[i])
#             pipe_up_pos = (positionx[i], positiony[i] - 400 - 875)

#             screen.blit(pipe_down_img, pipe_down_pos)
#             screen.blit(pipe_up_img, pipe_up_pos)

#             #Pixel-perfect collision detection with pipe_down
#             pipe_down_rect = Rect(*pipe_down_pos, pipe_down_img.get_width(), pipe_down_img.get_height())
#             if goose_rect.colliderect(pipe_down_rect):
#                 for x in range(goose_rect.w):
#                     for y in range(goose_rect.h):
#                         gx = x
#                         gy = y
#                         if goose_img.get_at((gx, gy))[3] > 0:
#                             px = goose_rect.x + x - pipe_down_pos[0]
#                             py = goose_rect.y + y - pipe_down_pos[1]
#                             if 0 <= px < pipe_down_img.get_width() and 0 <= py < pipe_down_img.get_height():
#                                 if pipe_down_img.get_at((px, py))[3] > 0:
#                                     died = True
#                                     break

#             #Pixel-perfect collision detection with pipe_up
#             pipe_up_rect = Rect(*pipe_up_pos, pipe_up_img.get_width(), pipe_up_img.get_height())
#             if goose_rect.colliderect(pipe_up_rect):
#                 for x in range(goose_rect.w):
#                     for y in range(goose_rect.h):
#                         gx = x
#                         gy = y
#                         if goose_img.get_at((gx, gy))[3] > 0:
#                             px = goose_rect.x + x - pipe_up_pos[0]
#                             py = goose_rect.y + y - pipe_up_pos[1]
#                             if 0 <= px < pipe_up_img.get_width() and 0 <= py < pipe_up_img.get_height():
#                                 if pipe_up_img.get_at((px, py))[3] > 0:
#                                     died = True
#                                     break
#         #Score system
#         screen.blit(image.load("Image/score.png"),(0,0))
#         flappyfont = font.Font("flappy.ttf",30)
#         scoretext = flappyfont.render(f"{score}",True,WHITE)
#         scoretext2 = flappyfont.render(f"{score}",True,BLACK)
#         screen.blit(scoretext2,(152,7))
#         screen.blit(scoretext,(150,5))
        

#         if start:
#             goose_img = image.load("Image/goose.png").convert_alpha()
#             goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
#             screen.blit(goose_img, goose_rect)
            
#             screen.blit(image.load("Image/start.png"),(300,200))
#             flappyfont = font.Font("flappy.ttf",30)
#             beginning = flappyfont.render(f"Close fist to start",True,WHITE)
#             screen.blit(beginning,(300,300))
#             display.flip()
            
#         else:
#             '''Goose'''
#             #Apply gravity
#             goosenum+=1
#             goosenum= goosenum%15
#             velocity += gravity
#             bird_y += velocity    
#             if bird_y > 1005:
#                 bird_y = 1005
#                 velocity = 0
#             elif bird_y <= 0:
#                 bird_y = 0
#                 velocity = 0

#             #Bliting the bird
#             if goosenum <= 5:
#                 goose_img = image.load("Image/goose.png").convert_alpha()
#                 goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
#                 screen.blit(goose_img, goose_rect)     
#             elif goosenum<=10:
#                 goose_img = image.load("Image/gooseup.png").convert_alpha()
#                 goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
#                 screen.blit(goose_img, goose_rect)  
#             else:
#                 goose_img = image.load("Image/goosedown.png").convert_alpha()
#                 goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
#                 screen.blit(goose_img, goose_rect)
#             display.flip()

        
#         for i in range(3):
#             if positionx[i]+179 <= 400:
#                 if not adding[i]:
#                     score +=1
#                     adding[i] = True
#                     mixer.Sound.play(mixer.Sound("Sound/point.mp3"))
#     #Death screen
#     else:
#         if firstdied:
#             mixer.Sound.play(mixer.Sound("Sound/die.mp3"))
#             firstdied = False
#             screen.blit(image.load("Image/end.png"),(300,200))
#             screen.blit(image.load("Image/box.png"),(300,300))
#             if highest <= score:
#                 highest = score
#             flappyfont = font.Font("flappy.ttf",30)
#             scoring = flappyfont.render(f"{score}",True,WHITE)
#             screen.blit(scoring,(350,360))
#             highesting = flappyfont.render(f"{highest}",True,WHITE)
#             screen.blit(highesting,(560,360))
#             restart = flappyfont.render(f"Close fist",True,WHITE)
#             restart2 = flappyfont.render(f"to restart",True,WHITE)
#             screen.blit(restart,(350,410))
#             screen.blit(restart2,(350,455))

#     display.flip()


#     myClock.tick(60)
            
# quit()


