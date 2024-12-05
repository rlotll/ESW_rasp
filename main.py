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

fail_image = Image.open("fail.png")
success_image = Image.open("success.png")

backgrounds = [Image.open("track1.png"), Image.open("track2.png")]
bg_idx = 0


fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)

#캐릭터 클래스 선언
class Character:
    def __init__(self, width, height, img):
        self.state = None
        self.position = np.array([width/2 - 60, height/2 - 10])
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

#피할 대상 클래스 선언
class Enemy:
    def __init__(self, width, height, img_path):
        self.touched = 'no'
        self.image = Image.open(img_path).resize((40, 40))  # 적 이미지
        self.x = random.randint(30, width - 70)  # 화면 너비 내 랜덤 위치
        self.y = 90  # 에서 시작
        self.speed = random.randint(3, 4)  # 속도 (3~4)

    def move(self):
        if self.x < 100:
            self.y += self.speed
            self.x -= 2 #대각선 이동
        else:
            self.y += self.speed
            self.x += 2

    def draw(self, canvas):
        if self.touched == 'no':
            canvas.paste(self.image, (self.x, self.y), mask=self.image)

#충돌 검사
def check_collision(char, enemy):
    # 두 이미지를 겹치는 영역 계산
    overlap_left = max(char.position[0], enemy.x)
    overlap_top = max(char.position[1], enemy.y)
    overlap_right = min(char.position[0] + 120, enemy.x + 40)  # 캐릭터와 적 크기
    overlap_bottom = min(char.position[1] + 120, enemy.y + 40)

    # 겹치는 영역이 없다면 충돌 없음
    if overlap_left >= overlap_right or overlap_top >= overlap_bottom:
        return False

    # 겹치는 영역에서 픽셀 충돌 확인
    for x in range(int(overlap_left), int(overlap_right)):
        for y in range(int(overlap_top), int(overlap_bottom)):
            char_pixel = char.image.getpixel((x - char.position[0], y - char.position[1]))
            enemy_pixel = enemy.image.getpixel((x - enemy.x, y - enemy.y))
            if char_pixel[3] > 0 and enemy_pixel[3] > 0:  # 알파 값이 0보다 크면 픽셀이 존재
                return True
    return False

enemies = []
fail_flag = 0
timer = 0

#카트 객체 선언
kart = Character(joystick.width, joystick.height, "kart.png")
#바나나 객체 선언
#banana = Enemy(joystick.width, joystick.height, "banana.png")

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
    bg_idx = (bg_idx + 1) % 2
    current_background = backgrounds[bg_idx]
    game_image.paste(current_background, (0, 0), mask=current_background) # mask= : 투명도가 0인 부분은 제외시키는 역할

    # 적 생성 (8% 확률로 생성)
    if random.random() < 0.08:
        enemies.append(Enemy(joystick.width, joystick.height, "banana.png"))

    # 적 이동 및 그리기
    for enemy in enemies:
        enemy.move()
        enemy.draw(game_image)

    # 적 제거 (화면 아래로 나간 적)
    enemies = [enemy for enemy in enemies if enemy.y < joystick.height]

    kart.move(command)    
    kart.char_draw(game_image)

    # 충돌 처리
    for enemy in enemies:
        if check_collision(kart, enemy):
            # 게임 종료 처리 또는 캐릭터 체력 감소 등 추가
            fail_flag = 1
            break

    ##game_image 화면에 송출##
    joystick.disp.image(game_image)

    if fail_flag:
        joystick.disp.image(fail_image)
        break

    if timer > 1000:
        joystick.disp.image(success_image)
        break
    
    #시간 측정
    timer += 1
    ##화면 갱신 속도##
    time.sleep(0.01)