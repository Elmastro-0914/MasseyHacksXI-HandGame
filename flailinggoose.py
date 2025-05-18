from pygame import *
from random import *
import math
import threading
import cv2
import mediapipe as mp

init()
font.init()

# Screen
screen = display.set_mode((1920, 1080)) 

RED = (255, 0, 0)
GREY = (127, 127, 127)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
myClock = time.Clock()
running = True

currX, currY = 1, 1

# MediaPipe initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

prevX, prevY = 0, 0

cap = cv2.VideoCapture(0)

# Thread to process webcam input separately
def process_hand():
    global currX, currY, prevX, prevY, start, died
    global score, bird_y, velocity, positionx, positiony
    global adding, firstdied
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

                def is_finger_closed(tip_idx, pip_idx):
                    return landmarks[tip_idx].y > landmarks[pip_idx].y

                closed_fingers = [
                    is_finger_closed(8, 6),
                    is_finger_closed(12, 10),
                    is_finger_closed(16, 14),
                    is_finger_closed(20, 18)
                ]

                thumb_closed = landmarks[4].x < landmarks[3].x if landmarks[17].x < landmarks[0].x else landmarks[4].x > landmarks[3].x

                wrist = landmarks[0]
                currX, currY = wrist.x, wrist.y

                if all(closed_fingers) and thumb_closed:
                    if died:
                        score = 0
                        bird_y = 540
                        velocity = 0
                        positionx = [1000, 2000, 3000]
                        positiony = [randint(500, 980), randint(500, 980), randint(500, 980)]
                        adding = [False, False, False]
                        start = True
                        died = False
                        firstdied = True
                    elif start:
                        start = False
                        mixer.Sound.play(mixer.Sound("Sound/start.mp3"))
                    # else:
                    #     velocity = jump_strength
                    #     mixer.Sound.play(mixer.Sound("Sound/flying.mp3"))
                        

        cv2.imshow('Hand Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        

threading.Thread(target=process_hand, daemon=True).start()

# Game Variables
score = 0
highest = 0
backgroundx = 0
goosenum = 0
bird_y = 540
gravity = 0.2
velocity = 0
jump_strength = -10

background_img = image.load("Image/background.png").convert_alpha()
backgroundtop_img = image.load("Image/backgroundtop.png").convert_alpha()
end_img = image.load("Image/end.png")
box_img = image.load("Image/box.png")

positionx = [1000, 2000, 3000]
positiony = [randint(500, 980), randint(500, 980), randint(500, 980)]
spacing = [(125, 55), (115, 25), (145, 75)]
adding = [False, False, False]
died = False
start = True
firstdied = True
goose_img = image.load("Image/goose.png").convert()
goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())

# Main loop
while running:
    for evt in event.get():
        if evt.type == QUIT:
            running = False
                    
    if not died:              
        if not start:
            # Apply gravity
            velocity += gravity
            bird_y += velocity
                        
        #Setting the background
        screen.blit(background_img,(backgroundx,51))
        screen.blit(background_img,(backgroundx+1735,51))
        screen.blit(background_img,(backgroundx+1735*2,51))
        screen.blit(backgroundtop_img,(185,0))
        if not start:
            backgroundx-=8     #4 or 8
            if backgroundx<-1735:
                backgroundx = 0
            for i in range(3):
                if positionx[i] == -184:
                    positionx[i] = 3000
                    positiony[i] = randint(400,980)
                    adding[i] = False  
                else:
                    positionx[i]= positionx[i]-8      #4 or 8

        for i in range(3):
            pipe_down_img = image.load("Image/buildingdown.png").convert() #.convert_alpha()
            pipe_up_img = image.load("Image/buildingup.png").convert() #.convert_alpha()

            pipe_down_pos = (positionx[i], positiony[i])
            pipe_up_pos = (positionx[i], positiony[i] - 500 - 875)

            screen.blit(pipe_down_img, pipe_down_pos)
            screen.blit(pipe_up_img, pipe_up_pos)

            #Pixel-perfect collision detection with pipe_down
            pipe_down_rect = Rect(*pipe_down_pos, pipe_down_img.get_width(), pipe_down_img.get_height())
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
            pipe_up_rect = Rect(*pipe_up_pos, pipe_up_img.get_width(), pipe_up_img.get_height())
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
        screen.blit(image.load("Image/score.png"),(0,0))
        flappyfont = font.Font("flappy.ttf",30)
        scoretext = flappyfont.render(f"{score}",True,WHITE)
        scoretext2 = flappyfont.render(f"{score}",True,BLACK)
        screen.blit(scoretext2,(152,7))
        screen.blit(scoretext,(150,5))

        print(abs(currY - prevY))         
        if abs(currY - prevY) < 0.3 and abs(currY - prevY) > 0.03:
            print(currY - prevY)
            if currY - prevY < 0:
                velocity = jump_strength
                mixer.Sound.play(mixer.Sound("Sound/flying.mp3"))
        

        if start:
            goose_img = image.load("Image/goose.png").convert_alpha()
            goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
            screen.blit(goose_img, goose_rect)
            
            screen.blit(image.load("Image/start.png"),(300,200))
            flappyfont = font.Font("flappy.ttf",30)
            beginning = flappyfont.render(f"Close fist to start",True,WHITE)
            screen.blit(beginning,(300,300))
            display.flip()
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
                goose_img = image.load("Image/goose.png").convert_alpha()
                goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                screen.blit(goose_img, goose_rect)     
            elif goosenum<=10:
                goose_img = image.load("Image/gooseup.png").convert_alpha()
                goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                screen.blit(goose_img, goose_rect)  
            else:
                goose_img = image.load("Image/goosedown.png").convert_alpha()
                goose_rect = Rect(400, int(bird_y), goose_img.get_width(), goose_img.get_height())
                screen.blit(goose_img, goose_rect)
            display.flip()

        for i in range(3):
            if positionx[i]+179 <= 400:
                if not adding[i]:
                    score +=1
                    adding[i] = True
                    mixer.Sound.play(mixer.Sound("Sound/point.mp3"))
    #Death screen
    else:
        if firstdied:
            mixer.Sound.play(mixer.Sound("Sound/die.mp3"))
            firstdied = False
            screen.blit(end_img,(300,200))
            screen.blit(box_img,(300,300))
            if highest <= score:
                highest = score
            flappyfont = font.Font("flappy.ttf",30)
            scoring = flappyfont.render(f"{score}",True,WHITE)
            screen.blit(scoring,(350,360))
            highesting = flappyfont.render(f"{highest}",True,WHITE)
            screen.blit(highesting,(560,360))
            restart = flappyfont.render(f"Close fist",True,WHITE)
            restart2 = flappyfont.render(f"to restart",True,WHITE)
            screen.blit(restart,(350,410))
            screen.blit(restart2,(350,455))

    prevX, prevY = currX, currY
    display.flip()
    myClock.tick(60)

quit()