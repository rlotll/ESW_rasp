import time
import random
from colorsys import hsv_to_rgb
import board
from digitalio import DigitalInOut, Direction
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
import numpy as np

class Joystick:
    def __init__(self):
        self.cs_pin = DigitalInOut(board.CE0)
        self.dc_pin = DigitalInOut(board.D25)
        self.reset_pin = DigitalInOut(board.D24)
        self.BAUDRATE = 24000000

        self.spi = board.SPI()
        self.disp = st7789.ST7789(
                    self.spi,
                    height=240,
                    y_offset=80,
                    rotation=180,
                    cs=self.cs_pin,
                    dc=self.dc_pin,
                    rst=self.reset_pin,
                    baudrate=self.BAUDRATE,
                    )

        # Input pins:
        self.button_A = DigitalInOut(board.D5)
        self.button_A.direction = Direction.INPUT

        self.button_B = DigitalInOut(board.D6)
        self.button_B.direction = Direction.INPUT

        self.button_L = DigitalInOut(board.D27)
        self.button_L.direction = Direction.INPUT

        self.button_R = DigitalInOut(board.D23)
        self.button_R.direction = Direction.INPUT

        self.button_U = DigitalInOut(board.D17)
        self.button_U.direction = Direction.INPUT

        self.button_D = DigitalInOut(board.D22)
        self.button_D.direction = Direction.INPUT

        self.button_C = DigitalInOut(board.D4)
        self.button_C.direction = Direction.INPUT

        # Turn on the Backlight
        self.backlight = DigitalInOut(board.D26)
        self.backlight.switch_to_output()
        self.backlight.value = True

        # Create blank image for drawing.
        # Make sure to create image with mode 'RGB' for color.
        self.width = self.disp.width
        self.height = self.disp.height

class Character:
    def __init__(self, width, height):
        self.appearance = 'circle'
        self.state = None
        self.position = np.array([width/2 - 20, height/2 - 20, width/2 + 20, height/2 + 20])
        self.outline = "#FFFFFF"
        # 총알 발사를 위한 캐릭터 중앙 점 추가
        self.center = np.array([(self.position[0] + self.position[2]) / 2, (self.position[1] + self.position[3]) / 2])

    def move(self, command = None):
        if command['move'] == False:
            self.state = None
            self.outline = "#FFFFFF" #검정색상 코드!
        
        else:
            self.state = 'move'
            self.outline = "#FF0000" #빨강색상 코드!

            if command['up_pressed']:
                self.position[1] -= 5
                self.position[3] -= 5

            if command['down_pressed']:
                self.position[1] += 5
                self.position[3] += 5

            if command['left_pressed']:
                self.position[0] -= 5
                self.position[2] -= 5
                
            if command['right_pressed']:
                self.position[0] += 5
                self.position[2] += 5

        #center update
        self.center = np.array([(self.position[0] + self.position[2]) / 2, (self.position[1] + self.position[3]) / 2])

class Enemy:
    def __init__(self, spawn_position):
        self.appearance = 'circle'
        self.state = 'alive'
        self.position = np.array([spawn_position[0] - 25, spawn_position[1] - 25, spawn_position[0] + 25, spawn_position[1] + 25])
        self.center = np.array([(self.position[0] + self.position[2]) / 2, (self.position[1] + self.position[3]) / 2])
        self.outline = "#00FF44"

class Bullet:
    def __init__(self, position, command):
        self.appearance = 'rectangle'
        self.speed = 10
        self.damage = 10
        self.position = np.array([position[0]-3, position[1]-3, position[0]+3, position[1]+3])
        self.direction = {'up' : False, 'down' : False, 'left' : False, 'right' : False}
        self.state = None
        self.outline = "#0000FF"
        if command['up_pressed']:
            self.direction['up'] = True
        if command['down_pressed']:
            self.direction['down'] = True
        if command['right_pressed']:
            self.direction['right'] = True
        if command['left_pressed']:
            self.direction['left'] = True

        

    def move(self):
        if self.direction['up']:
            self.position[1] -= self.speed
            self.position[3] -= self.speed

        if self.direction['down']:
            self.position[1] += self.speed
            self.position[3] += self.speed

        if self.direction['left']:
            self.position[0] -= self.speed
            self.position[2] -= self.speed
            
        if self.direction['right']:
            self.position[0] += self.speed
            self.position[2] += self.speed
            
    def collision_check(self, enemys):
        for enemy in enemys:
            collision = self.overlap(self.position, enemy.position)
            
            if collision:
                enemy.state = 'die'
                self.state = 'hit'

    def overlap(self, ego_position, other_position):
        '''
        두개의 사각형(bullet position, enemy position)이 겹치는지 확인하는 함수
        좌표 표현 : [x1, y1, x2, y2]
        
        return :
            True : if overlap
            False : if not overlap
        '''
        return ego_position[0] > other_position[0] and ego_position[1] > other_position[1] \
                 and ego_position[2] < other_position[2] and ego_position[3] < other_position[3]

joystick = Joystick()
my_image = Image.new("RGB", (joystick.width, joystick.height)) #도화지!
my_draw = ImageDraw.Draw(my_image) #그리는 도구!


# 잔상이 남지 않는 코드 & 대각선 이동 가능
my_circle = Character(joystick.width, joystick.height)
my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
enemy_1 = Enemy((50, 50))
enemy_2 = Enemy((200, 200))
enemy_3 = Enemy((150, 50))

enemys_list = [enemy_1, enemy_2, enemy_3]

bullets = []
while True:
    command = {'move': False, 'up_pressed': False , 'down_pressed': False, 'left_pressed': False, 'right_pressed': False}
    
    if not joystick.button_U.value:  # up pressed
        command['up_pressed'] = True
        command['move'] = True

    if not joystick.button_D.value:  # down pressed
        command['down_pressed'] = True
        command['move'] = True

    if not joystick.button_L.value:  # left pressed
        command['left_pressed'] = True
        command['move'] = True

    if not joystick.button_R.value:  # right pressed
        command['right_pressed'] = True
        command['move'] = True

    if not joystick.button_A.value: # A pressed
        bullet = Bullet(my_circle.center, command)
        bullets.append(bullet)

    my_circle.move(command)
    for bullet in bullets:
        bullet.collision_check(enemys_list)
        bullet.move()
        
    #그리는 순서가 중요합니다. 배경을 먼저 깔고 위에 그림을 그리고 싶었는데 그림을 그려놓고 배경으로 덮는 결과로 될 수 있습니다.
    my_draw.rectangle((0, 0, joystick.width, joystick.height), fill = (255, 255, 255, 100))
    my_draw.ellipse(tuple(my_circle.position), outline = my_circle.outline, fill = (0, 0, 0))
    
    for enemy in enemys_list:
        if enemy.state != 'die':
            my_draw.ellipse(tuple(enemy.position), outline = enemy.outline, fill = (255, 0, 0))

    for bullet in bullets:
        if bullet.state != 'hit':
            my_draw.rectangle(tuple(bullet.position), outline = bullet.outline, fill = (0, 0, 255))

    #좌표는 동그라미의 왼쪽 위, 오른쪽 아래 점 (x1, y1, x2, y2)
    joystick.disp.image(my_image)


'''
<발전 방향 제안>

실행시켜보면 문제점이 무엇인가요?
- 가만히 있는 상태에서 발사버튼(A)를 누르면 bullet이 그려진 후, 움직이지 않음
- bullet을 담는 bullets 리스트에 bullet이 쌓이기만 할 뿐, 사라지지 않음 -> 메모리가 부족해지고 점점 동작 속도가 느려지는 것도 체감 가능  

어떻게 하면 고칠 수 있을지 생각해보고 고쳐보세요😀

움직이지 않고, 아무런 행동이 없기 때문에 spawn 된 후, 가만히 있게 만들었습니다.  
만약 총알에 맞았을 때 적의 색이 바뀐다거나, 도망가기위해 움직인다거나 하는 것도 구현해보세요!

총알을 맞추면 적들이 잘 사라지나요?  
아직 미흡한 점이 무엇인지 생각해보고 수정해봅시다!😀
- Enemy 역시 그냥 눈으로만 안보이는 척 하는 것일 뿐, list 내에 살아 있음. -> 메모리 관리 필요
- Enemy가 총알에 맞았을 시, 한 방에 죽는 것이 아닌 체력이 있다면?
'''

