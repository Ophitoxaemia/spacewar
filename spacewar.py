# Space war game for two players
# Python 3.8.10
import pygame
import math
from copy import deepcopy
import random

pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((1280, 720))
font = pygame.freetype.SysFont('Comic Sans MS', 30)

clock = pygame.time.Clock()
running = True
dt = 0
waiting_for_restart = False
waiting_for_start = True
max_damage = 10

# ship 1
angle = 90
ship1dx = 0
ship1dy = 0
ship1damage = 0
ship1_pos = pygame.Vector2(screen.get_width()/5, screen.get_height() / 2)
torpedos1 = []
firedtime1 = 0
ship1speed=0.0
lastIncreasedSpeedTick1 = 0
drawThrust1 = False
maxspeed1 = 6

# ship 2
angle2 = 90
ship2dx = 0
ship2dy = 0
ship2damage = 0
ship2_pos = pygame.Vector2(screen.get_width()*4/5, screen.get_height() / 2)
torpedos2 = []
firedtime2 = 0
ship2speed=0.0
lastIncreasedSpeedTick2 = 0
drawThrust2 = False
maxspeed2 = 6

s = "*"
caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
pygame.display.set_caption(caption) 

# nebulas, ships can hide in these
nebulas = []
for i in range(0,6):
    nebula = pygame.Rect(random.randrange(0,screen.get_width()), random.randrange(0,screen.get_height()), random.randrange(30,screen.get_height()/4), random.randrange(30,screen.get_height()/4))
    nebulas.append(nebula) 

# rocks harm ships
# there is only one shape rock, but have different sizes
rocks = []
for i in range(0,7):
    rocksize = random.randrange(2,7)
    while True: # Don't spawn rock inside a ship
        rockpos = [random.randrange(0,screen.get_width()), random.randrange(0,screen.get_height())]
        rockrect = pygame.Rect(rockpos[0]-3*rocksize/2, rockpos[1]-3*rocksize/2, rocksize, rocksize)
        if not (rockrect.colliderect(ship1_pos.x-12,ship1_pos.y-6, 24, 12) or rockrect.colliderect(ship2_pos.x-12,ship2_pos.y-6, 24, 12)):
            break 
    rockpoints = [[rockpos[0]-3*rocksize, rockpos[1]+0*rocksize],[rockpos[0]-1*rocksize, rockpos[1]-3*rocksize], [rockpos[0]+1*rocksize, rockpos[1]-2*rocksize], [rockpos[0]+2*rocksize, rockpos[1]-2*rocksize], [rockpos[0]+2*rocksize, rockpos[1]+0*rocksize], [rockpos[0]+3*rocksize, rockpos[1]+1*rocksize], [rockpos[0]+1*rocksize, rockpos[1]+3*rocksize], [rockpos[0]+0*rocksize, rockpos[1]+3*rocksize], [rockpos[0]-3*rocksize, rockpos[1]+0*rocksize]]
    rockdxy = (random.randrange(-5, 5)/2, random.randrange(-5, 5)/2) # /2 allows generating non-integer values
    rockangle = random.randrange(0, 359)
    rockspinrate = random.randrange(-4,4)/2+.3 # makes sure spin rate is never 0
    rock = [rockpos, rockrect, rockdxy, rockpoints, rocksize, rockangle, rockspinrate] # tuples don't allow assignments so everything is an array
    rocks.append(rock)

def rectRotated2( surface, color, pos, rotation_angle, rotation_offset_center = (0,0), nAntialiasingRatio = 1 ):
    """
    - rotation_angle: in degree
    - rotation_offset_center: moving the center of the rotation: (-100,0) will turn the rectangle around a point 100 above center of the rectangle,
                                            if (0,0) the rotation is at the center of the rectangle
    - nAntialiasingRatio: set 1 for no antialising, 2/4/8 for better aliasing
    """
    nRenderRatio = nAntialiasingRatio
    
    sw = pos[2]+abs(rotation_offset_center[0])*2
    sh = pos[3]+abs(rotation_offset_center[1])*2

    surfcenterx = sw//2
    surfcentery = sh//2
    s = pygame.Surface( (sw*nRenderRatio,sh*nRenderRatio) )
    s = s.convert_alpha()
    s.fill((0,0,0,0))
    
    rw2=pos[2]//2 # halfwidth of rectangle
    rh2=pos[3]//2

    pygame.draw.rect( s, color, ((surfcenterx-rw2-rotation_offset_center[0])*nRenderRatio,(surfcentery-rh2-rotation_offset_center[1])*nRenderRatio,pos[2]*nRenderRatio,pos[3]*nRenderRatio) )
    s = pygame.transform.rotate( s, rotation_angle )        
    if nRenderRatio != 1: s = pygame.transform.smoothscale(s,(s.get_width()//nRenderRatio,s.get_height()//nRenderRatio))
    incfromrotw = (s.get_width()-sw)//2
    incfromroth = (s.get_height()-sh)//2
    surface.blit( s, (pos[0]-surfcenterx+rotation_offset_center[0]+rw2-incfromrotw,pos[1]-surfcentery+rotation_offset_center[1]+rh2-incfromroth) )  

def rotate_points(points, pivot, angle):
    pp = pygame.math.Vector2(pivot)
    rotated_points = [
        (pygame.math.Vector2(x, y) - pp).rotate(angle) + pp for x, y in points]
    return rotated_points    
    
while running:                                                              
    # pygame.QUIT event means the user clicked X to close window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # erase last screen
    screen.fill((0,0,0)) 

    # play area is a torus- no edges
    if ship1_pos.x <= 0:
        ship1_pos.x = screen.get_width()-10
    if ship1_pos.y <= 0:
        ship1_pos.y = screen.get_height()-10
    if ship1_pos.x > screen.get_width():
        ship1_pos.x = 10
    if ship1_pos.y > screen.get_height():
        ship1_pos.y = 10                 

    if ship2_pos.x <= 0:
        ship2_pos.x = screen.get_width()-10
    if ship2_pos.y <= 0:
        ship2_pos.y = screen.get_height()-10
    if ship2_pos.x > screen.get_width():
        ship2_pos.x = 10
    if ship2_pos.y > screen.get_height():
        ship2_pos.y = 10

    s1rect = pygame.Rect(ship1_pos.x-18,ship1_pos.y-18, 36, 36)                            
    s2rect = pygame.Rect(ship2_pos.x-18,ship2_pos.y-18, 36, 36)                            
    if (s1rect.colliderect(s2rect)): # ships have an inelastic collision with each other 
        ship1dx=ship2dx/2+ship1dx/2  # could also explode or have elastic collision
        ship1dy=ship2dy/2+ship1dy/2
        ship2dx=ship1dx/2+ship2dx/2
        ship2dy=ship1dy/2+ship2dy/2

    # draw ships
    if drawThrust1:
        rectRotated2(screen, "red", (ship1_pos.x-12+math.cos(math.radians(angle))*5,ship1_pos.y-6+6-2-math.sin(math.radians(angle))*5, 24, 4), angle)
    rectRotated2(screen, "gray", (ship1_pos.x-12-math.cos(math.radians(angle))*5,ship1_pos.y-6+6-2+math.sin(math.radians(angle))*5, 24, 4), angle)
    pygame.draw.circle(screen, "gray", (ship1_pos.x,ship1_pos.y),5)
    width1 = int((max_damage-ship1damage)/3)
    if width1 > 0:
        pygame.draw.circle(screen, "gray", (ship1_pos.x,ship1_pos.y),25,width1) # draw ship's shield
    if drawThrust2:
        rectRotated2(screen, "green", (ship2_pos.x-12+math.cos(math.radians(angle2))*5,ship2_pos.y-6+6-2-math.sin(math.radians(angle2))*5, 24, 4), angle2)    
    rectRotated2(screen, "gray", (ship2_pos.x-12-math.cos(math.radians(angle2))*5,ship2_pos.y-6+6-2+math.sin(math.radians(angle2))*5, 24, 4), angle2)    
    pygame.draw.circle(screen, "gray", (ship2_pos.x,ship2_pos.y),5)
    width2 = int((max_damage-ship2damage)/3)
    if width2 > 0:
        pygame.draw.circle(screen, "gray", (ship2_pos.x,ship2_pos.y),25,width2)

    if len(torpedos1) > 0:
        for torpedo in torpedos1: 
            pygame.draw.rect(screen,"red",(torpedo[0].x, torpedo[0].y, 4, 4))        
            torpedo[0].x += torpedo[1].x # [1] are the dx and dy values
            torpedo[0].y += torpedo[1].y
            if ((torpedo[0].x > ship2_pos.x-12 and torpedo[0].x < ship2_pos.x+12) and (torpedo[0].y > ship2_pos.y-12 and torpedo[0].y < ship2_pos.y+12)):
                torpedos1.remove(torpedo) 
                ship2damage += 1
                caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
                pygame.display.set_caption(caption) 
                if (ship2damage >= max_damage):
                    winmessage = "Ship1 wins!"
                    waiting_for_restart = True

            if (torpedo[0].x < 0 or torpedo[0].y < 0 or torpedo[0].x > screen.get_width() or torpedo[0].y > screen.get_height()):
                torpedos1.remove(torpedo) # torpedoes disappear at edges

    if len(torpedos2) > 0:
        for torpedo in torpedos2: 
            pygame.draw.rect(screen,"green",(torpedo[0].x, torpedo[0].y, 4, 4))        
            torpedo[0].x += torpedo[1].x
            torpedo[0].y += torpedo[1].y
            if ((torpedo[0].x > ship1_pos.x-12 and torpedo[0].x < ship1_pos.x+12) and (torpedo[0].y > ship1_pos.y-12 and torpedo[0].y < ship1_pos.y+12)):
                torpedos2.remove(torpedo) 
                ship1damage += 1
                caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
                pygame.display.set_caption(caption)                  
                if (ship1damage >= max_damage):
                    winmessage = "Ship2 wins!"
                    waiting_for_restart = True                 

            if (torpedo[0].x < 0 or torpedo[0].y < 0 or torpedo[0].x > screen.get_width() or torpedo[0].y > screen.get_height()):
                torpedos2.remove(torpedo)    

    # rock = [rockpos, rockrect, rockdxy, rockpoints, rocksize, rockangle, rockspinrate]
    #            0         1        2          3          4         5           6
    # polygon(surface, color, points, width=0)
    for rock in rocks:
        pygame.draw.polygon(screen, "white", rotate_points(rock[3], rock[0], rock[5]), 1)
        pygame.display.set_caption(caption)   
        rock[0][0]+=rock[2][0]
        rock[0][1]+=rock[2][1]

        rock[5]+=rock[6]

        if rock[0][0] <= 0:
            rock[0][0] = screen.get_width()-10
        if rock[0][1] <= 0:
            rock[0][1] = screen.get_height()-10
        if rock[0][0] > screen.get_width():
            rock[0][0] = 10
        if rock[0][1] > screen.get_height():
            rock[0][1] = 10    

        rocksize = rock[4]

        rock[1] = pygame.Rect(rock[0][0]-3*rocksize, rock[0][1]-3*rocksize, rocksize*6, rocksize*6)        
        if rock[1].colliderect(s1rect): # s1rect is set above
            ship1damage += 5 # below makes a hitbar for each ship
            caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
            pygame.display.set_caption(caption) 
            if (ship1damage >= max_damage):
                winmessage = "Ship2 wins!"
                waiting_for_restart = True
            if rock in rocks:
                rocks.remove(rock)                   

        # pygame.draw.rect(screen,"cadetblue1",s2rect, 1)   # visualize the hitboxes     
        # pygame.draw.rect(screen,"cadetblue1",rock[1], 1)        

        if rock[1].colliderect(s2rect):
            ship2damage += 5
            caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
            pygame.display.set_caption(caption)             
            if (ship2damage >= max_damage):
                winmessage = "Ship1 wins!"
                waiting_for_restart = True
            if rock in rocks:
                rocks.remove(rock)                   

        # reset the points in the rect because we may have changed the position
        rock[3] = [[rock[0][0]-3*rocksize, rock[0][1]+0*rocksize],[rock[0][0]-1*rocksize, rock[0][1]-3*rocksize], [rock[0][0]+1*rocksize, rock[0][1]-2*rocksize], [rock[0][0]+2*rocksize, rock[0][1]-2*rocksize], [rock[0][0]+2*rocksize, rock[0][1]+0*rocksize], [rock[0][0]+3*rocksize, rock[0][1]+1*rocksize], [rock[0][0]+1*rocksize, rock[0][1]+3*rocksize], [rock[0][0]+0*rocksize, rock[0][1]+3*rocksize], [rock[0][0]-3*rocksize, rock[0][1]+0*rocksize]]

        # a little clumsy
        for index in range(len(rock[3])): # Move rock
            rock[3][index][0]+=rock[2][0]
            rock[3][index][1]+=rock[2][1]

    for nebula in nebulas:
        pygame.draw.ellipse(screen,(114,58,229),nebula)  # draw after ships so it hides them

    if (waiting_for_start):
        font.render_to(screen, (screen.get_width()/4-100, 150), "WAD to move", (190,190,190))  
        font.render_to(screen, (screen.get_width()/4-100, 250), "V to fire", (190,190,190))                 
        font.render_to(screen, (screen.get_width()*3/4-100, 150), "Arrows to move", (190,190,190))          
        font.render_to(screen, (screen.get_width()*3/4-100, 250), "F11 to fire", (190,190,190))          

    if (waiting_for_restart):
        font.render_to(screen, (screen.get_width()/2-75, 250), winmessage, (190, 190, 190))                   
        font.render_to(screen, (screen.get_width()/2-150, 350), "Press spacebar to restart", (190, 190, 190))                   

    keys = pygame.key.get_pressed()

    if waiting_for_restart and keys[pygame.K_SPACE]: # Restart the game
        waiting_for_restart = False
        waiting_for_start = True

        # ship 1
        angle = 90
        ship1dx = 0
        ship1dy = 0
        ship1damage = 0
        ship1_pos = pygame.Vector2(screen.get_width()/5, screen.get_height() / 2)
        torpedos1.clear()
        firedtime1 = 0
        lastIncreasedSpeedTick1 = 0

        # ship 2
        angle2 = 90
        ship2dx = 0
        ship2dy = 0
        ship2damage = 0
        ship2_pos = pygame.Vector2(screen.get_width()*4/5, screen.get_height() / 2)
        torpedos2.clear()
        firedtime2 = 0
        lastIncreasedSpeedTick2 = 0

        rocks.clear()
        for i in range(0,7):
            rocksize = random.randrange(2,7)
            while True: # Don't spawn rock inside a ship, can still be unfair if a rock is headed toward ship
                rockpos = [random.randrange(0,screen.get_width()), random.randrange(0,screen.get_height())]
                rockrect = pygame.Rect(rockpos[0]-3*rocksize/2, rockpos[1]-3*rocksize/2, rocksize, rocksize)
                if not (rockrect.colliderect(ship1_pos.x-12,ship1_pos.y-6, 24, 12) or rockrect.colliderect(ship2_pos.x-12,ship2_pos.y-6, 24, 12)):
                    break 
            rockpoints = [[rockpos[0]-3*rocksize, rockpos[1]+0*rocksize],[rockpos[0]-1*rocksize, rockpos[1]-3*rocksize], [rockpos[0]+1*rocksize, rockpos[1]-2*rocksize], [rockpos[0]+2*rocksize, rockpos[1]-2*rocksize], [rockpos[0]+2*rocksize, rockpos[1]+0*rocksize], [rockpos[0]+3*rocksize, rockpos[1]+1*rocksize], [rockpos[0]+1*rocksize, rockpos[1]+3*rocksize], [rockpos[0]+0*rocksize, rockpos[1]+3*rocksize], [rockpos[0]-3*rocksize, rockpos[1]+0*rocksize]]
            rockdxy = (random.randrange(-5, 5)/2, random.randrange(-5, 5)/2) # 2 allows generating non-integer values
            rockangle = random.randrange(0, 359)
            rockspinrate = random.randrange(-4,4)/2+.3 # makes sure spin rate is never 0
            rock = [rockpos, rockrect, rockdxy, rockpoints, rocksize, rockangle, rockspinrate]
            rocks.append(rock)

        caption = "Ship1 health: "+''.join([char*(max_damage-ship1damage) for char in s])+"                                         Ship2 health: "+''.join([char*(max_damage+1-ship2damage) for char in s])
        pygame.display.set_caption(caption)           

    if (not waiting_for_restart): # Stop controls when game is over
        ship1_pos.x += ship1dx
        ship1_pos.y += ship1dy
        # ship 1 controls
        if keys[pygame.K_a]:
            angle = angle + 3
        if keys[pygame.K_d]:
            angle = angle - 3        
        if keys[pygame.K_w]:
            if (pygame.time.get_ticks() > lastIncreasedSpeedTick1+100): # throttle acceleration to 10 times/second
                speed = abs(ship1dx)+abs(ship1dy)
                new_speed = abs(ship1dx - math.cos(math.radians(angle))/4)+abs(ship1dy + math.sin(math.radians(angle))/4)
                if speed <= maxspeed1 or new_speed < speed: # Allow engine to fire if slowing from max speed
                    ship1dx += -math.cos(math.radians(angle))/4
                    ship1dy += math.sin(math.radians(angle))/4
                lastIncreasedSpeedTick1 = pygame.time.get_ticks()
            drawThrust1=True
            waiting_for_start = False
            # caption = "speed: "+str(speed)+"                    newspeed: "+str(new_speed)
            # pygame.display.set_caption(caption)           
        else:
            drawThrust1=False
        if keys[pygame.K_v]:
            if (pygame.time.get_ticks() > firedtime1+200):
                torpedod = pygame.Vector2(-math.cos(math.radians(angle))*4+ship1dx, math.sin(math.radians(angle))*4+ship1dy)
                torpedo = [deepcopy(ship1_pos), torpedod]
                torpedos1.append(torpedo)
                firedtime1= pygame.time.get_ticks()    

        # ship 2 controls
        ship2_pos.x += ship2dx
        ship2_pos.y += ship2dy
        if keys[pygame.K_LEFT]:
            angle2 = angle2 + 3
        if keys[pygame.K_RIGHT]:
            angle2 = angle2 - 3
        if keys[pygame.K_UP]:
            if (pygame.time.get_ticks() > lastIncreasedSpeedTick2+100):
                speed = abs(ship2dx)+abs(ship2dy)
                new_speed = abs(ship2dx - math.cos(math.radians(angle2))/4)+abs(ship2dy + math.sin(math.radians(angle2))/4)
                if speed <= maxspeed2 or new_speed < speed:
                    ship2dx += -math.cos(math.radians(angle2))/4
                    ship2dy += math.sin(math.radians(angle2))/4
                lastIncreasedSpeedTick2 = pygame.time.get_ticks()
            drawThrust2 = True
            waiting_for_start = False
        else:
            drawThrust2 = False
        if keys[pygame.K_F11] or keys[pygame.K_c]: # c/z/x are for when using 2 keyboards
            if (pygame.time.get_ticks() > firedtime2+200): # fire only once per second
                torpedod = pygame.Vector2(-math.cos(math.radians(angle2))*4+ship2dx, math.sin(math.radians(angle2))*4+ship2dy)
                torpedo = [deepcopy(ship2_pos), torpedod]
                torpedos2.append(torpedo)
                firedtime2= pygame.time.get_ticks() 

    # flip() blit drawing to screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()