import random

import pygame
from pygame.time import delay, get_ticks

from network import Network


class Canvas:

    def __init__(self, w, h, name="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w, h))
        pygame.display.set_caption(name)

    @staticmethod
    def update():
        pygame.display.update()

    def draw_text(self, text, size, x, y):
        pygame.font.init()
        font = pygame.font.SysFont("comicsans", size)
        render = font.render(text, 1, (0, 0, 0))
        self.screen.blit(render, (x, y))

    def get_canvas(self):
        return self.screen

    def draw_background(self):
        self.screen.fill((255, 255, 255))


class Player:
    radius = 25  # Set the radius for the circles

    def __init__(self, startx, starty, max_x, min_x, max_y, min_y, color=(255, 0, 0)):
        self.x = startx
        self.y = starty
        self.velocity = int(50 / 10 ** (5 / 6))
        self.color = color
        self.max_x = max_x
        self.min_x = min_x
        self.max_y = max_y
        self.min_y = min_y

    def draw(self, g, text):
        pygame.draw.circle(g, self.color, (self.x + self.radius, self.y + self.radius), self.radius)
        text_size = 20
        text_font = pygame.font.SysFont("comicsans", text_size)
        text_render = text_font.render(text, 1, (0, 0, 0))
        g.blit(text_render, (self.x + self.radius - text_render.get_width() // 2, self.y + self.radius - text_render.get_height() // 2))

    def move(self, dirn):
        if dirn == 0 and self.x + self.velocity + 2 * self.radius <= self.max_x:
            self.x += self.velocity
        elif dirn == 1 and self.x + self.radius - self.velocity >= self.min_x:
            self.x -= self.velocity
        elif dirn == 2 and self.y + self.radius - self.velocity >= self.min_y:
            self.y -= self.velocity
        elif dirn == 3 and self.y + self.velocity + 2 * self.radius <= self.max_y:
            self.y += self.velocity


class Game:

    def __init__(self, w, h):
        self.small_balls = None
        self.net = Network()
        self.width = w
        self.height = h
        self.player = Player(50, 50, self.width, 0, self.height, 0)
        self.player2 = Player(50, 50, self.width, 0, self.height, 0)
        self.player3 = Player(50, 50, self.width, 0, self.height, 0)
        self.canvas = Canvas(self.width, self.height, "Agar.io")
        self.resumeflag = 1
        self.start_time = None  # Zmienna do przechowywania czasu rozpoczęcia gry
        self.game_duration = 180000  # Czas gry w milisekundach (3 minuty)
        self.eat_cooldown = False
        self.eat_cooldown_duration = 1000  # 1000 milliseconds (1 second)
        pygame.font.init()

    def check_collision(self):
        # Funkcja pomocnicza do obliczania środka kuli
        def get_player_center(player):
            return player.x + player.radius, player.y + player.radius

        # Sprawdź, czy aktualny gracz zjadł innego gracza
        for player_info in [self.player2, self.player3]:
            player_center = get_player_center(self.player)
            player_info_center = get_player_center(player_info)

            distance = ((player_center[0] - player_info_center[0]) ** 2 + (
                        player_center[1] - player_info_center[1]) ** 2) ** 0.5

            if distance < self.player.radius + player_info.radius and self.player.radius > player_info.radius:
                if not self.eat_cooldown:
                    # Aktualny gracz zjadł innego gracza
                    self.player.radius += player_info.radius // 2
                    self.send_data()
                    delay(20)
                    # Activate eat cooldown
                    self.eat_cooldown = True
                    pygame.time.set_timer(pygame.USEREVENT, self.eat_cooldown_duration)  # Set a timer for cooldown

        # Sprawdź, czy aktualny gracz został zjedzony przez innego gracza
        for player_info in [self.player2, self.player3]:
            player_center = get_player_center(self.player)
            player_info_center = get_player_center(player_info)

            distance = ((player_center[0] - player_info_center[0]) ** 2 + (
                        player_center[1] - player_info_center[1]) ** 2) ** 0.5

            if distance < self.player.radius + player_info.radius and player_info.radius > self.player.radius:
                # Aktualny gracz został zjedzony przez innego gracza
                self.send_data()
                self.player.x, self.player.y = 0, 0  # Przesuń aktualnego gracza na początkową pozycję
                self.player.velocity = max(int(50 / self.player.radius ** (5 / 6)), 0.3)  # Zaktualizuj prędkość gracza
                self.canvas.draw_text("You have been eaten!", 60, self.width//8, self.height//3)
                self.canvas.draw_text("press space to respawn...", 40, self.width//8 + 20, self.height//3 + 50)
                self.canvas.update()
                delay(10)
                self.resumeflag = 0

            if self.resumeflag == 0:
                self.player.x = 2000
                self.player.y = 2000
                self.send_data()
                waiting_for_space = True
                while waiting_for_space:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                            waiting_for_space = False
                            self.resumeflag = 1
                self.player.x = 0
                self.player.y = random.randint(1, self.height)
                self.player.radius = 10
                self.send_data()
                self.canvas.draw_background()  # Wyczyść ekran po opóźnieniu

    def run(self):
        clock = pygame.time.Clock()
        run = True
        initial_positions_received = False
        remaining_seconds = 180
        while run:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        run = False
                elif event.type == pygame.USEREVENT:
                    # Deactivate eat cooldown when the timer expires
                    self.eat_cooldown = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT]:
                if self.player.x <= self.width - self.player.velocity:
                    self.player.move(0)
            if keys[pygame.K_LEFT]:
                if self.player.x >= self.player.velocity:
                    self.player.move(1)
            if keys[pygame.K_UP]:
                if self.player.y >= self.player.velocity:
                    self.player.move(2)
            if keys[pygame.K_DOWN]:
                if self.player.y <= self.height - self.player.velocity:
                    self.player.move(3)


            while not initial_positions_received:
                self.canvas.draw_background()
                self.canvas.draw_text("Waiting for other players...", 30, self.width//8, self.height//3)
                self.canvas.update()
                initial_positions_received, small_balls_info = self.receive_initial_positions()
                self.initialize_small_balls(small_balls_info)
            # Inicjalizacja czasu gry przy pierwszym obiegu pętli
            if self.start_time is None:
                self.start_time = get_ticks()
            # Oblicz pozostały czas
            elapsed_time = get_ticks() - self.start_time
            remaining_time = max(0, self.game_duration - elapsed_time)
            # Konwersja czasu z milisekund na sekundy
            remaining_seconds = remaining_time // 1000
            self.check_collision()
            # Send Network Stuff
            try:
                self.player.radius, self.player2.x, self.player2.y, self.player2.radius, self.player3.x, self.player3.y, self.player3.radius, self.small_balls = self.parse_data(
                    self.send_data(), self.net.id)
                self.player.velocity = max(int(50 / self.player.radius ** (5 / 6)), 0.3)
            except Exception as e:
                print("Error in communication with server ", e)
            # Update Canvas
            self.canvas.draw_background()
            self.draw_small_balls()
            self.player.draw(self.canvas.get_canvas(), "you")
            self.player2.draw(self.canvas.get_canvas(), "p2")
            self.player3.draw(self.canvas.get_canvas(), "p3")
            # Wyświetl pozostały czas w prawym górnym rogu
            self.canvas.draw_text(f"Time left: {remaining_seconds}s", 20, self.width - 150, 10)
            self.canvas.update()
            # Sprawdź, czy czas gry minął
            if elapsed_time >= self.game_duration:
                print("Game Over - Time's up!")
                run = False
        self.canvas.draw_background()
        self.canvas.draw_text(f"Leaderboard:", 40, self.width // 8, self.height // 60)
        players = [
            [self.player, "you: ", self.player.radius],
            [self.player2, "player2: ", self.player2.radius],
            [self.player3, "player3: ", self.player3.radius]
        ]
        sorted_players = sorted(players, key=lambda x: x[2], reverse=True)
        # Wyświetlenie posortowanych wyników
        text_y_position = self.height//6
        for rank, player_info in enumerate(sorted_players, start=1):
            player, label, radius = player_info
            display_text = f"{rank}. {label} Radius: {radius}"
            self.canvas.draw_text(display_text, 30, self.width // 8, text_y_position)
            text_y_position += self.height // 20
        self.canvas.draw_text("press space to quit the game...", 20, self.width // 8, text_y_position+20)
        self.canvas.update()
        if remaining_seconds < 1:
            waiting_for_space = True
            while waiting_for_space:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        waiting_for_space = False
        pygame.quit()

    def receive_initial_positions(self):
        initial_positions = self.net.receive()
        if initial_positions and "?" in initial_positions:
            player_positions, small_balls_and_color_info = initial_positions.split("?")
            small_balls_info, col_info = small_balls_and_color_info.split("@")
            colours = col_info.split("|")
            colours = [x.split(",") for x in colours]
            self.player.color = tuple(map(int, colours[int(self.net.id)]))
            colours.pop(int(self.net.id))
            self.player2.color = tuple(map(int, colours[0]))
            self.player3.color = tuple(map(int, colours[1]))
            player_positions = player_positions.split("|")
            if len(player_positions) == 3:
                for player_info in player_positions:
                    player_id, player_data = player_info.split(":")
                    x, y, radius = map(int, player_data.split(","))

                    if int(player_id) == int(self.net.id):
                        self.player.x = x
                        self.player.y = y
                        self.player.radius = radius
                        return True, small_balls_info
        return False, ""

    def draw_small_balls(self):
        for ball in self.small_balls:
            pygame.draw.circle(self.canvas.get_canvas(), (0, 0, 255), (ball['x'], ball['y']), 5)

    def initialize_small_balls(self, small_balls_info):
        self.small_balls = []
        balls_data = small_balls_info.split("|")
        for ball_data in balls_data:
            x, y = map(int, ball_data.split(","))
            self.small_balls.append({'x': x, 'y': y})

    def send_data(self):
        data = f"{self.net.id}:{int(self.player.x)},{int(self.player.y)},{self.player.radius}"
        reply = self.net.send(data)
        return reply

    @staticmethod
    def parse_data(data, current_player_id):
        try:
            player_info_list = []
            current_player_radius = 0  # Zmienna do przechowywania radiusa aktualnego gracza

            # Rozdzielamy dane dotyczące graczy i małych piłek
            players_and_balls = data.split("?")
            players_data = players_and_balls[0]
            balls_data = players_and_balls[1]

            # Parsujemy dane graczy
            for player_info in players_data.split("|"):
                player_id, player_data = player_info.split(":")
                x, y, radius = map(int, player_data.split(","))
                player_info_list.append((x, y, radius))

                # Jeśli to aktualny gracz, zapisz jego radius
                if int(player_id) == int(current_player_id):
                    current_player_radius = radius

            # Pobieramy indeks bieżącego gracza
            current_player_index = int(current_player_id)

            # Usuwamy dane bieżącego gracza z listy
            player_info_list.pop(current_player_index)

            # Parsujemy dane małych piłek
            balls_list = []
            for ball_info in balls_data.split("|"):
                ball_x, ball_y = map(int, ball_info.split(","))
                balls_list.append({'x': ball_x, 'y': ball_y})

            # Zwracamy pozycję bieżącego gracza, pozycje obu przeciwników, radius aktualnego gracza i pozycje małych piłek jako osobne wartości
            return (
                current_player_radius, player_info_list[0][0], player_info_list[0][1], player_info_list[0][2],
                player_info_list[1][0], player_info_list[1][1], player_info_list[1][2],
                balls_list
            )
        except Exception as e:
            print(f"Error parsing data: {e}", )
            return 0, 0, 0, 0, 0, 0, 0, []


if __name__ == "__main__":
    game = Game(800, 600)
    game.run()