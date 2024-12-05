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

#시작 세팅
joystick = Joystick()
game_image = Image.new("RGBA", (joystick.width, joystick.height))
game_draw = ImageDraw.Draw(game_image)

#배경 설정 후 그리기
background = Image.open("track1.png").convert("RGBA")
joystick.disp.image(background)

#색 지정 팔레트
udlr_fill = "#00FF00"
udlr_outline = "#00FFFF"
button_fill = "#FF00FF"
button_outline = "#FFFFFF"

fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)

#캐릭터 클래스 선언
class Character:
    def __init__(self, width, height, img):
        self.state = None
        self.position = np.array([width/2 - 60, height/2 - 30])
        self.image = Image.open(img)

    #움직임 함수
    def move(self, command = None):
        if command['move'] == False:
            self.state = None
            self.image = Image.open("kart.png")
        
        else:
            self.state = 'move'

            if command['up_pressed']:
                self.position[1] -= 5

            if command['down_pressed']:
                self.position[1] += 5

            if command['left_pressed']:
                self.image = Image.open("kart_l.png")
                self.position[0] -= 5
                
            if command['right_pressed']:
                self.image = Image.open("kart_r.png")
                self.position[0] += 5

    #캐릭터 그리는 함수
    def char_draw(self, canvas):
        canvas.paste(self.image, (int(self.position[0]), int(self.position[1])), mask=self.image)

#카트 객체 선언
kart = Character(joystick.width, joystick.height, "kart.png")

####실행 파트
while True:
    command = {'move': False,
               'up_pressed': False ,
               'down_pressed': False,
               'left_pressed': False,
               'right_pressed': False,
               'A_pressed': False,
               'B_pressed': False}
    
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
        command['A_pressed'] = True
    
    if not joystick.button_B.value: # B pressed
        command['B_pressed'] = True
    

    ##배경 그리기##
    game_image.paste(background, (0, 0), mask=background)
    # mask= : 투명도가 0인 부분은 제외시키는 역할

    kart.move(command)    
    kart.char_draw(game_image)

    ##game_image 화면에 송출##
    joystick.disp.image(game_image)

    ##화면 갱신 속도##
    time.sleep(0.01)