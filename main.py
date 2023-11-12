from time import time as timer
from random import randint

from pygame import *

init()
mixer.init()
font.init()


class GameSprite(sprite.Sprite):
    def __init__(self, sprite_image, x, y, width, height, speed):
        super().__init__()
        self.speed = speed
        self.image = transform.scale(image.load(sprite_image), (width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def reset(self):
        virtual_surface.blit(self.image, (self.rect.x, self.rect.y))


class Player(GameSprite):
    def __init__(self):
        self.alive = True
        self.hp = 3
        self.dmg = 2
        self.wait = 0
        self.shoot_kd = 7
        self.clip = 10
        self.in_reload = False
        self.last_shoot = 0

        self.width = 100
        self.height = 150
        self.x = (WIDTH - self.width) // 2
        self.y = HEIGHT - 170
        super().__init__("images/rocket.png", (WIDTH - 100) // 2, HEIGHT - 170, 100, 150, 10)

        self.health_group = sprite.Group()

        x = WIDTH - 70
        for i in range(self.hp):
            heart = HealthIco(x, 20)
            self.health_group.add(heart)
            x -= 20

        self.interface_clip_group = []
        self.clip_group = []

        ammo_x = 20
        for _ in range(self.clip):
            cartridge = CartridgeIco(ammo_x, HEIGHT - 50)
            self.clip_group.append(cartridge)
            ammo_x += 20

        self.interface_clip_group = self.clip_group

    def update(self):
        keys = key.get_pressed()
        if keys[K_w] and self.rect.y > 0:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < HEIGHT - self.rect.height:
            self.rect.y += self.speed
        if keys[K_a] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[K_d] and self.rect.x < WIDTH - self.rect.width:
            self.rect.x += self.speed
        if keys[K_SPACE] and self.wait <= 0 and not self.in_reload:
            self.fire()
        else:
            self.wait -= 1

        if self.in_reload:
            current_time = timer()
            if current_time - self.last_shoot >= 1.5:
                self.clip = 10
                self.in_reload = False
                self.interface_clip_group = self.clip_group

    def fire(self):
        bullet = Bullet(self.rect.centerx - 10, self.rect.y)
        bullets_group.add(bullet)
        self.wait = self.shoot_kd
        shoot_sound.play()
        self.clip -= 1
        print(self.clip)
        self.interface_clip_group = self.interface_clip_group[:-1]
        if self.clip <= 0:
            self.reload()

    def reload(self):
        self.last_shoot = timer()
        self.in_reload = True

    def take_dmg(self, dmg):
        self.hp -= dmg
        for i in range(dmg):
            self.health_group.spritedict.popitem()
        print(self.hp)

        if self.hp <= 0:
            self.alive = False

    def regen(self, amount):
        x = WIDTH - 70
        for i in range(self.hp):
            x -= 20

        for j in range(amount):
            heart = HealthIco(x, 20)
            self.health_group.add(heart)
            x -= 20

        self.hp += amount


class Ufo(GameSprite):
    def __init__(self, hp, width, speed, is_boss=False):
        self.x = randint(0, WIDTH - width)
        self.y = randint(-HEIGHT - width // 2, 0)
        self.spawn_hp = hp
        self.current_hp = self.spawn_hp
        self.is_boss = is_boss

        if self.is_boss:
            self.bonus_increase_dmg_chance = 30
            self.bonus_increase_speed_chance = 30
            self.bonus_health_chance = 40
        else:
            self.bonus_increase_dmg_chance = 1
            self.bonus_increase_speed_chance = 1
            self.bonus_health_chance = 2

        super().__init__("images/ufo.png", self.x, self.y, width, width // 2, speed)

    def update(self, dmg):
        self.rect.y += self.speed
        if self.rect.y >= HEIGHT:
            update_lost(dmg)
            if self.is_boss:
                self.kill()
            else:
                self.respawn()

    def respawn(self):
        self.rect.x = randint(0, WIDTH - self.rect.width)
        self.rect.y = randint(-HEIGHT, - self.rect.height)
        self.current_hp = self.spawn_hp

    def take_dmg(self, dmg):
        self.current_hp -= dmg
        if self.current_hp <= 0:
            self.death()

    def death(self):
        global boss_is_present
        self.spawn_bonus()
        if self.is_boss:
            update_score(3)
            self.kill()
            boss_is_present = False
        else:
            update_score(1)
            self.respawn()

    def spawn_bonus(self):
        if randint(0, 100) < self.bonus_increase_speed_chance:
            bonus = IncreaseAttackSpeedBonus(self.rect.centerx, self.rect.centery)
            bonuses_group.add(bonus)
        elif randint(0, 100) < self.bonus_increase_dmg_chance:
            bonus = IncreaseDamageBonus(self.rect.centerx, self.rect.centery)
            bonuses_group.add(bonus)
        elif randint(0, 100) < self.bonus_health_chance:
            bonus = HealthBonus(self.rect.centerx, self.rect.centery)
            bonuses_group.add(bonus)


class Asteroid(GameSprite):
    def __init__(self):
        self.width = randint(30, 80)
        self.x = randint(0, WIDTH - self.width)
        self.y = randint(-HEIGHT, -self.width)
        self.speed = randint(1, 6)
        super().__init__("images/asteroid.png", self.x, self.y, self.width, self.width, self.speed)

    def update(self):
        self.rect.y += self.speed
        if self.rect.y >= HEIGHT:
            self.respawn()

    def respawn(self):
        self.speed = randint(1, 6)
        self.width = randint(30, 80)
        self.image = transform.scale(image.load("images/asteroid.png"), (self.width, self.width))
        self.rect = self.image.get_rect()
        self.rect.x = randint(0, WIDTH - self.rect.width)
        self.rect.y = randint(-HEIGHT, - self.rect.height)


class Bullet(GameSprite):
    def __init__(self, x, y):
        super().__init__("images/bullet.png", x, y, 20, 40, 15)

    def update(self):
        self.rect.y -= self.speed
        if self.rect.y < -self.rect.h:
            self.kill()


class Bonus(GameSprite):
    def __init__(self, sprite_image, x, y):
        super().__init__(sprite_image, x, y, 50, 50, 5)

    def catch(self, game_spite):
        if sprite.collide_rect(self, game_spite):
            self.do_effect(game_spite)
            self.kill()

    def do_effect(self, game_spite):
        pass

    def update(self, game_sprite):
        self.rect.y += self.speed
        self.catch(game_sprite)
        if self.rect.y > HEIGHT:
            self.kill()


class IncreaseDamageBonus(Bonus):
    def __init__(self, x, y):
        super().__init__("images/increase_damage.png", x, y)

    def do_effect(self, game_spite):
        game_spite.dmg += 1
        print(game_spite, "dmg = ", game_spite.dmg)


class IncreaseAttackSpeedBonus(Bonus):
    def __init__(self, x, y):
        super().__init__("images/increase_speed.png", x, y)

    def do_effect(self, game_sprite):
        game_sprite.shoot_kd -= 1
        print(game_sprite, "shoot_kd = ", game_sprite.shoot_kd)


class HealthBonus(Bonus):
    def __init__(self, x, y):
        super().__init__("images/heart.png", x, y)

    def do_effect(self, game_sprite):
        game_sprite.regen(1)


class HealthIco(GameSprite):
    def __init__(self, x, y):
        super().__init__("images/heart.png", x, y, 50, 50, 0)


class CartridgeIco(GameSprite):
    def __init__(self, x, y):
        super().__init__("images/bullet.png", x, y, 15, 30, 0)


def update_lost(amount):
    global lost, text_lost
    lost += amount
    text_lost = font_interface.render("Пропущено: " + str(lost), True, (255, 255, 255))


def update_score(amount):
    global score, text_score
    score += amount
    text_score = font_interface.render("Рахунок: " + str(score), True, (255, 255, 255))


WIDTH = 1280
HEIGHT = 720
ASPECT_RATIO = WIDTH / HEIGHT

FPS = 60

window = display.set_mode((WIDTH, HEIGHT), RESIZABLE)
display.set_caption("Shooter")
background = transform.scale(image.load("images/galaxy.jpg"), (WIDTH, HEIGHT))
clock = time.Clock()

virtual_surface = Surface((WIDTH, HEIGHT))
current_size = window.get_size()

mixer.music.load('sounds/space.ogg')
mixer.music.set_volume(0.1)
mixer.music.play(-1)

shoot_sound = mixer.Sound("sounds/fire.ogg")
shoot_sound.set_volume(0.1)

font_interface = font.Font(None, 30)
font_finish = font.Font(None, 300)

lost = 0
score = 0

text_lost = font_interface.render("Пропущено: " + str(lost), True, (255, 255, 255))
text_score = font_interface.render("Рахунок: " + str(score), True, (255, 255, 255))

text_win = font_finish.render("Ти переміг", True, (100, 200, 60))
text_lose = font_finish.render("Ти програв", True, (200, 100, 60))

ufo_group = sprite.Group()
boss_group = sprite.Group()
bonuses_group = sprite.Group()
bullets_group = sprite.Group()
health_group = sprite.Group()
asteroids_group = sprite.Group()

for i in range(10):
    ufo = Ufo(3, 150, 2)
    ufo_group.add(ufo)

player = Player()

for i in range(3):
    asteroid = Asteroid()
    asteroids_group.add(asteroid)

boss_is_present = False

game = True
finish = False
while game:

    for e in event.get():
        if e.type == QUIT:
            game = False
        if e.type == KEYDOWN:
            if e.key == K_ESCAPE:
                game = False
        if e.type == VIDEORESIZE:
            new_width = e.w
            new_height = int(new_width / ASPECT_RATIO)
            window = display.set_mode((new_width, new_height), RESIZABLE)
            current_size = window.get_size()

    if not finish:
        virtual_surface.blit(background, (0, 0))

        player.reset()
        player.update()

        ufo_group.draw(virtual_surface)
        ufo_group.update(1)

        if score != 0 and score % 10 == 0 and not boss_is_present:
            boss = Ufo(5, 300, 1, True)
            boss_group.add(boss)
            boss_is_present = True

        boss_group.draw(virtual_surface)
        boss_group.update(3)

        bonuses_group.draw(virtual_surface)
        bonuses_group.update(player)

        bullets_group.draw(virtual_surface)
        bullets_group.update()

        asteroids_group.draw(virtual_surface)
        asteroids_group.update()

        player.health_group.draw(virtual_surface)
        for ammo in player.interface_clip_group:
            virtual_surface.blit(ammo.image, (ammo.rect.x, ammo.rect.y))

        crash_list = sprite.spritecollide(player, ufo_group, False)
        for enemy in crash_list:
            enemy.death()
            player.take_dmg(1)

        crash_boss_list = sprite.spritecollide(player, boss_group, False)
        for enemy in crash_boss_list:
            enemy.death()
            player.take_dmg(3)

        crash_list_asteroids = sprite.spritecollide(player, asteroids_group, False)
        for asteroid in crash_list_asteroids:
            asteroid.respawn()
            player.take_dmg(1)

        enemy_hit_dict = sprite.groupcollide(ufo_group, bullets_group, False, True)
        for enemy in enemy_hit_dict:
            enemy.take_dmg(player.dmg)

        boss_hit_dict = sprite.groupcollide(boss_group, bullets_group, False, True)
        for enemy in boss_hit_dict:
            enemy.take_dmg(player.dmg)

        sprite.groupcollide(asteroids_group, bullets_group, False, True)

        virtual_surface.blit(text_lost, (30, 30))
        virtual_surface.blit(text_score, (30, 60))

        if not player.alive or lost >= 20:
            virtual_surface.blit(text_lose, (100, 300))
            finish = True

        if score > 200:
            virtual_surface.blit(text_win, (100, 300))
            finish = True

    scaled_surface = transform.scale(virtual_surface, current_size)
    window.blit(scaled_surface, (0, 0))
    clock.tick(FPS)
    display.update()
