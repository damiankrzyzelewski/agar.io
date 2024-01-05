import pygame
from network import Network


class Canvas:

    def __init__(self, w, h, name="None"):
        self.width = w
        self.height = h
        self.screen = pygame.display.set_mode((w,h))
        pygame.display.set_caption(name)

    @staticmethod
    def update():
        pygame.display.update()

    def draw_text(self, text, size, x, y):
        pygame.font.init()
        font = pygame.font.SysFont("comicsans", size)
        render = font.render(text, 1, (0,0,0))
        self.screen.draw(render, (x,y))

    def get_canvas(self):
        return self.screen

    def draw_background(self):
        self.screen.fill((255,255,255))


class Player:
    radius = 25  # Set the radius for the circles

    def __init__(self, startx, starty, max_x, min_x, max_y, min_y, color=(255, 0, 0)):
        self.x = startx
        self.y = starty
        self.velocity = int(50 / 10**(5/6))
        self.color = color
        self.max_x = max_x
        self.min_x = min_x
        self.max_y = max_y
        self.min_y = min_y

    def draw(self, g):
        pygame.draw.circle(g, self.color, (self.x + self.radius, self.y + self.radius), self.radius)

    def move(self, dirn):
        if dirn == 0 and self.x + self.velocity + 2*self.radius <= self.max_x:
            self.x += self.velocity
        elif dirn == 1 and self.x + self.radius - self.velocity >= self.min_x:
            self.x -= self.velocity
        elif dirn == 2 and self.y + self.radius - self.velocity >= self.min_y:
            self.y -= self.velocity
        elif dirn == 3 and self.y + self.velocity + 2*self.radius <= self.max_y:
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
        self.canvas = Canvas(self.width, self.height, "Testing...")

    def run(self):
        clock = pygame.time.Clock()
        run = True
        initial_positions_received = False
        while run:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        run = False

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

            if not initial_positions_received:
                initial_positions_received, small_balls_info = self.receive_initial_positions()
                self.initialize_small_balls(small_balls_info)

            # Send Network Stuff
            self.player.radius, self.player2.x, self.player2.y, self.player2.radius, self.player3.x, self.player3.y, self.player3.radius, self.small_balls = self.parse_data(
                self.send_data(), self.net.id)
            self.player.velocity = int(50 / self.player.radius**(5/6))
            # Update Canvas
            self.canvas.draw_background()
            self.draw_small_balls()
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.player3.draw(self.canvas.get_canvas())
            self.canvas.update()

        pygame.quit()

    def receive_initial_positions(self):
        initial_positions = self.net.receive()
        print(initial_positions)
        if initial_positions and "?" in initial_positions:
            player_positions, small_balls_info = initial_positions.split("?")
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
        data = f"{self.net.id}:{self.player.x},{self.player.y},{self.player.radius}"
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
            print(f"Error parsing data: {e}")
            return 0, 0, 0, 0, 0, 0, 0, []


if __name__ == "__main__":
    game = Game(800, 600)
    game.run()

