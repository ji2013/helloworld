import pygame
import math
import random
import time

# 初始化pygame
pygame.init()

# 游戏窗口设置
WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("方盒枪战游戏")

# 帧率设置
clock = pygame.time.Clock()
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
BG_COLOR = (30, 30, 30)

# 工具函数
def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y - y2)

def normalize(dx, dy):
    length = math.hypot(dx, dy)
    if length == 0:
        return 0, 0
    return dx / length, dy / length

def clamp(value, low, high):
    return max(low, min(high, value))

# 武器系统定义
WEAPONS = {
    "手枪": {
        "damage": 25,
        "cooldown": 0.28,
        "bullet_speed": 12,
        "bullet_count": 1,
        "spread": 0,
        "color": (255, 255, 102),  # 黄色
        "ammo": float('inf')  # 手枪无限弹药
    },
    "机枪": {
        "damage": 10,
        "cooldown": 0.05,
        "bullet_speed": 10,
        "bullet_count": 1,
        "spread": 4,
        "color": (102, 255, 102),  # 绿色
        "ammo": 200
    },
    "步枪": {
        "damage": 20,
        "cooldown": 0.11,
        "bullet_speed": 14,
        "bullet_count": 1,
        "spread": 2,
        "color": (102, 204, 255),  # 蓝色
        "ammo": 100
    },
    "狙击枪": {
        "damage": 100,
        "cooldown": 1.2,
        "bullet_speed": 25,
        "bullet_count": 1,
        "spread": 0,
        "color": (255, 102, 255),  # 紫色
        "ammo": 30
    }
}

WEAPON_ORDER = ["手枪", "机枪", "步枪", "狙击枪", "手榴弹"]

# 玩家类
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.size = 36
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        
        # 武器系统
        self.weapons = WEAPON_ORDER[:4]  # 初始拥有所有枪械
        self.weapon_index = 0
        self.weapon_ammo = {
            "手枪": float('inf'),
            "机枪": 200,
            "步枪": 100,
            "狙击枪": 30
        }
        self.grenades = 5  # 手榴弹数量
        
        self.last_shot_time = 0
        self.last_grenade_time = 0
        
    @property
    def current_weapon_name(self):
        return self.weapons[self.weapon_index]
    
    @property
    def current_weapon(self):
        if self.current_weapon_name == "手榴弹":
            return None
        return WEAPONS[self.current_weapon_name]
    
    def switch_weapon(self, index):
        if 0 <= index < len(WEAPON_ORDER):
            # 检查是否有这个武器
            if index == 4:  # 手榴弹
                self.weapon_index = 4
            else:
                if WEAPON_ORDER[index] in self.weapons:
                    self.weapon_index = index
    
    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_d]:
            dx += self.speed
        
        # 斜向移动归一化
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
        
        # 更新位置，限制在屏幕内
        self.x = clamp(self.x + dx, self.size, WIDTH - self.size)
        self.y = clamp(self.y + dy, self.size, HEIGHT - self.size)
    
    def can_shoot(self):
        if self.current_weapon_name == "手榴弹":
            return self.grenades > 0 and time.time() - self.last_grenade_time > 0.5
        weapon = self.current_weapon
        if not weapon:
            return False
        if self.weapon_ammo[self.current_weapon_name] <= 0:
            return False
        return time.time() - self.last_shot_time >= weapon["cooldown"]
    
    def shoot(self, target_x, target_y):
        if not self.can_shoot():
            return []
        
        if self.current_weapon_name == "手榴弹":
            # 扔手榴弹
            self.last_grenade_time = time.time()
            self.grenades -= 1
            dx, dy = normalize(target_x - self.x, target_y - self.y)
            speed = 8
            grenade = Grenade(self.x, self.y, dx * speed, dy * speed)
            return [], [grenade]
        
        # 枪械射击
        weapon = self.current_weapon
        self.last_shot_time = time.time()
        self.weapon_ammo[self.current_weapon_name] -= 1
        
        bullets = []
        base_angle = math.atan2(target_y - self.y, target_x - self.x)
        bullet_count = weapon["bullet_count"]
        
        if bullet_count == 1:
            angles = [base_angle]
        else:
            spread_rad = math.radians(weapon["spread"])
            start = base_angle - spread_rad / 2
            step = spread_rad / max(1, bullet_count - 1)
            angles = [start + i * step for i in range(bullet_count)]
        
        for angle in angles:
            # 加入随机散布
            if weapon["spread"] > 0:
                angle += math.radians(random.uniform(-weapon["spread"], weapon["spread"]))
            
            vx = math.cos(angle) * weapon["bullet_speed"]
            vy = math.sin(angle) * weapon["bullet_speed"]
            bullets.append(Bullet(self.x, self.y, vx, vy, weapon["damage"], weapon["color"], is_player=True))
        
        return bullets, []
    
    def draw(self, screen, mouse_x, mouse_y):
        # 绘制玩家方块
        pygame.draw.rect(screen, BLUE, 
                        (self.x - self.size//2, self.y - self.size//2, 
                         self.size, self.size))
        # 绘制枪口指向线
        if self.current_weapon:
            color = self.current_weapon["color"]
        else:
            color = GRAY
        dx, dy = normalize(mouse_x - self.x, mouse_y - self.y)
        gun_x = self.x + dx * 40
        gun_y = self.y + dy * 40
        pygame.draw.line(screen, color, (self.x, self.y), (gun_x, gun_y), 3)

# 子弹类
class Bullet:
    def __init__(self, x, y, vx, vy, damage, color, is_player):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.color = color
        self.is_player = is_player
        self.radius = 5
        self.alive = True
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        # 超出屏幕则消失
        if self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20:
            self.alive = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# 敌人类
class Enemy:
    def __init__(self, wave):
        # 从屏幕边缘生成
        side = random.randint(0, 3)
        if side == 0:
            self.x = random.randint(0, WIDTH)
            self.y = -30
        elif side == 1:
            self.x = WIDTH + 30
            self.y = random.randint(0, HEIGHT)
        elif side == 2:
            self.x = random.randint(0, WIDTH)
            self.y = HEIGHT + 30
        else:
            self.x = -30
            self.y = random.randint(0, HEIGHT)
        
        self.size = 32
        self.speed = 1.5 + wave * 0.1
        self.hp = 50 + wave * 10
        self.max_hp = self.hp
        self.damage = 10
        self.last_shot_time = 0
        self.shoot_cooldown = 1.0
        self.alive = True
    
    def update(self, player, enemy_bullets):
        if not self.alive:
            return
        
        # 追踪玩家
        dx, dy = normalize(player.x - self.x, player.y - self.y)
        dist = math.hypot(player.x - self.x, player.y - self.y)
        
        # 如果距离太远，靠近玩家
        if dist > 300:
            self.x += dx * self.speed
            self.y += dy * self.speed
        # 如果距离够了，射击玩家
        elif dist < 500:
            # 射击
            if time.time() - self.last_shot_time > self.shoot_cooldown:
                self.last_shot_time = time.time()
                # 生成敌人子弹
                angle = math.atan2(player.y - self.y, player.x - self.x)
                vx = math.cos(angle) * 6
                vy = math.sin(angle) * 6
                enemy_bullets.append(Bullet(self.x, self.y, vx, vy, self.damage, RED, is_player=False))
        
        # 限制位置
        self.x = clamp(self.x, self.size, WIDTH - self.size)
        self.y = clamp(self.y, self.size, HEIGHT - self.size)
    
    def draw(self, screen):
        # 绘制敌人方块
        pygame.draw.rect(screen, RED, 
                        (self.x - self.size//2, self.y - self.size//2, 
                         self.size, self.size))
        # 绘制血条
        bar_width = self.size
        bar_height = 4
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (50, 50, 50), 
                        (self.x - bar_width//2, self.y - self.size//2 - 8, 
                         bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, 
                        (self.x - bar_width//2, self.y - self.size//2 - 8, 
                         bar_width * hp_ratio, bar_height))

# 手榴弹类
class Grenade:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.timer = 2.0  # 2秒后爆炸
        self.radius = 8
        self.alive = True
        self.gravity = 0.2
    
    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        
        # 碰到边界反弹
        if self.x < self.radius or self.x > WIDTH - self.radius:
            self.vx *= -0.8
            self.x = clamp(self.x, self.radius, WIDTH - self.radius)
        if self.y < self.radius or self.y > HEIGHT - self.radius:
            self.vy *= -0.8
            self.y = clamp(self.y, self.radius, HEIGHT - self.radius)
        
        # 倒计时
        self.timer -= 1/60
        if self.timer <= 0:
            self.alive = False
            return True  # 要爆炸了
        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, 
                        (self.x - self.radius, self.y - self.radius, 
                         self.radius*2, self.radius*2))
        # 显示倒计时
        if self.timer < 1:
            # 闪烁
            if int(self.timer * 10) % 2 == 0:
                pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius + 3)

# 爆炸效果类
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_radius = 100
        self.radius = 10
        self.speed = 5
        self.alive = True
    
    def update(self):
        self.radius += self.speed
        if self.radius >= self.max_radius:
            self.alive = False
    
    def draw(self, screen):
        # 绘制爆炸，透明度渐变
        alpha = int(255 * (1 - self.radius / self.max_radius))
        color = (255, 165, 0, alpha)
        # 创建临时surface来绘制带透明度的圆
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (self.radius, self.radius), self.radius)
        screen.blit(s, (self.x - self.radius, self.y - self.radius))

# 游戏主类
class Game:
    def __init__(self):
        self.player = Player()
        self.enemies = []
        self.bullets = []
        self.grenades = []
        self.explosions = []
        
        self.wave = 1
        self.score = 0
        self.enemies_per_wave = 5
        self.enemies_spawned = 0
        self.wave_delay = 0
        
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 48)
    
    def spawn_wave(self):
        if self.enemies_spawned < self.enemies_per_wave and random.random() < 0.02:
            self.enemies.append(Enemy(self.wave))
            self.enemies_spawned += 1
    
    def check_collisions(self):
        # 子弹和单位的碰撞
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            if bullet.is_player:
                # 玩家子弹打敌人
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                    if dist < enemy.size//2 + bullet.radius:
                        enemy.hp -= bullet.damage
                        bullet.alive = False
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.score += 100
                            # 掉落弹药
                            if random.random() < 0.3:
                                # 随机给当前武器补弹药
                                weapon = self.player.current_weapon_name
                                if weapon != "手榴弹" and self.player.weapon_ammo[weapon] != float('inf'):
                                    self.player.weapon_ammo[weapon] += 10
                            if random.random() < 0.1:
                                self.player.grenades += 1
                        break
            else:
                # 敌人子弹打玩家
                dist = math.hypot(bullet.x - self.player.x, bullet.y - self.player.y)
                if dist < self.player.size//2 + bullet.radius:
                    self.player.hp -= bullet.damage
                    bullet.alive = False
                    if self.player.hp <= 0:
                        self.player.hp = 0
        
        # 手榴弹爆炸伤害
        for grenade in self.grenades:
            if not grenade.alive:
                # 爆炸了，处理伤害
                explosion_x, explosion_y = grenade.x, grenade.y
                # 玩家伤害
                dist = math.hypot(explosion_x - self.player.x, explosion_y - self.player.y)
                if dist < 100:
                    damage = 50 * (1 - dist / 100)
                    self.player.hp -= damage
                # 敌人伤害
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    dist = math.hypot(explosion_x - enemy.x, explosion_y - enemy.y)
                    if dist < 100:
                        damage = 100 * (1 - dist / 100)
                        enemy.hp -= damage
                        if enemy.hp <= 0:
                            enemy.alive = False
                            self.score += 100
                # 添加爆炸效果
                self.explosions.append(Explosion(explosion_x, explosion_y))
    
    def update(self, mouse_x, mouse_y):
        keys = pygame.key.get_pressed()
        self.player.move(keys)
        
        # 生成敌人
        if len(self.enemies) == 0 and self.enemies_spawned >= self.enemies_per_wave:
            # 波次完成
            self.wave_delay += 1
            if self.wave_delay > 60:  # 1秒后下一波
                self.wave += 1
                self.enemies_per_wave = 5 + self.wave * 2
                self.enemies_spawned = 0
                self.wave_delay = 0
        else:
            self.spawn_wave()
        
        # 更新敌人
        enemy_bullets = []
        for enemy in self.enemies:
            enemy.update(self.player, enemy_bullets)
        self.bullets.extend(enemy_bullets)
        
        # 更新子弹
        for bullet in self.bullets:
            bullet.update()
        # 移除死亡的子弹
        self.bullets = [b for b in self.bullets if b.alive]
        
        # 更新手榴弹
        new_grenades = []
        for grenade in self.grenades:
            exploded = grenade.update()
            if not exploded:
                if grenade.alive:
                    new_grenades.append(grenade)
        self.grenades = new_grenades
        
        # 更新爆炸
        for explosion in self.explosions:
            explosion.update()
        self.explosions = [e for e in self.explosions if e.alive]
        
        # 移除死亡的敌人
        self.enemies = [e for e in self.enemies if e.alive]
        
        # 碰撞检测
        self.check_collisions()
    
    def draw(self, mouse_x, mouse_y):
        screen.fill(BG_COLOR)
        
        # 绘制网格背景
        for x in range(0, WIDTH, 50):
            pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))
        
        # 绘制爆炸
        for explosion in self.explosions:
            explosion.draw(screen)
        
        # 绘制手榴弹
        for grenade in self.grenades:
            grenade.draw(screen)
        
        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen)
        
        # 绘制敌人
        for enemy in self.enemies:
            enemy.draw(screen)
        
        # 绘制玩家
        self.player.draw(screen, mouse_x, mouse_y)
        
        # 绘制HUD
        # 血量
        hp_text = self.font.render(f"血量: {int(self.player.hp)}/{self.player.max_hp}", True, WHITE)
        screen.blit(hp_text, (10, 10))
        
        # 血条
        bar_width = 200
        bar_height = 20
        pygame.draw.rect(screen, (50, 50, 50), (10, 40, bar_width, bar_height))
        hp_ratio = self.player.hp / self.player.max_hp
        pygame.draw.rect(screen, GREEN, (10, 40, bar_width * hp_ratio, bar_height))
        
        # 当前武器
        weapon_name = self.player.current_weapon_name
        weapon_text = self.font.render(f"武器: {weapon_name}", True, WHITE)
        screen.blit(weapon_text, (10, 70))
        
        # 弹药
        if weapon_name != "手榴弹":
            ammo = self.player.weapon_ammo[weapon_name]
            if ammo == float('inf'):
                ammo_text = self.font.render("弹药: 无限", True, WHITE)
            else:
                ammo_text = self.font.render(f"弹药: {int(ammo)}", True, WHITE)
            screen.blit(ammo_text, (10, 95))
        
        # 手榴弹数量
        grenade_text = self.font.render(f"手榴弹: {self.player.grenades}", True, WHITE)
        screen.blit(grenade_text, (10, 120))
        
        # 波次和分数
        wave_text = self.font.render(f"波次: {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH - 100, 10))
        score_text = self.font.render(f"分数: {self.score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 100, 35))
        
        # 操作提示
        help_text = self.font.render("WASD移动 | 鼠标瞄准 | 左键射击/扔雷 | 1-5切换武器", True, GRAY)
        screen.blit(help_text, (10, HEIGHT - 30))
        
        # 游戏结束
        if self.player.hp <= 0:
            game_over_text = self.large_font.render("游戏结束!", True, RED)
            restart_text = self.font.render("按R键重新开始", True, WHITE)
            screen.blit(game_over_text, (WIDTH//2 - 100, HEIGHT//2 - 50))
            screen.blit(restart_text, (WIDTH//2 - 100, HEIGHT//2 + 10))
    
    def reset(self):
        # 重置游戏
        self.__init__()

# 主游戏循环
def main():
    game = Game()
    running = True
    mouse_down = False
    
    while running:
        clock.tick(FPS)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                # 武器切换
                if event.key == pygame.K_1:
                    game.player.switch_weapon(0)
                if event.key == pygame.K_2:
                    game.player.switch_weapon(1)
                if event.key == pygame.K_3:
                    game.player.switch_weapon(2)
                if event.key == pygame.K_4:
                    game.player.switch_weapon(3)
                if event.key == pygame.K_5:
                    game.player.switch_weapon(4)
                
                # 重新开始
                if event.key == pygame.K_r and game.player.hp <= 0:
                    game.reset()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_down = True
            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
        
        # 游戏逻辑
        if game.player.hp > 0:
            game.update(mouse_x, mouse_y)
            
            # 射击（按住左键连续射击）
            if mouse_down:
                bullets, grenades = game.player.shoot(mouse_x, mouse_y)
                game.bullets.extend(bullets)
                game.grenades.extend(grenades)
        else:
            # 游戏结束，等待重启
            pass
        
        # 绘制
        game.draw(mouse_x, mouse_y)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
