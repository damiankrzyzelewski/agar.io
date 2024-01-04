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

    def __init__(self, startx, starty, color=(255, 0, 0)):
        self.x = startx
        self.y = starty
        self.velocity = 2
        self.color = color

    def draw(self, g):
        pygame.draw.circle(g, self.color, (self.x + self.radius, self.y + self.radius), self.radius)

    def move(self, dirn):
        if dirn == 0:
            self.x += self.velocity
        elif dirn == 1:
            self.x -= self.velocity
        elif dirn == 2:
            self.y -= self.velocity
        else:
            self.y += self.velocity


class Game:

    def __init__(self, w, h):
        self.net = Network()
        self.width = w
        self.height = h
        self.player = Player(50, 50)
        self.player2 = Player(50, 50)
        self.player3 = Player(50, 50)
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

                if event.type == pygame.K_ESCAPE:
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
                initial_positions_received = self.receive_initial_positions()
            # Send Network Stuff
            self.player2.x, self.player2.y, self.player3.x, self.player3.y = self.parse_data(self.send_data(), self.net.id)

            # Update Canvas
            self.canvas.draw_background()
            self.player.draw(self.canvas.get_canvas())
            self.player2.draw(self.canvas.get_canvas())
            self.player3.draw(self.canvas.get_canvas())
            self.canvas.update()

        pygame.quit()

    def receive_initial_positions(self):
        initial_positions = self.net.receive()
        if initial_positions and ":" in initial_positions:
            positions = initial_positions.split("|")
            if len(positions) == 3:
                for player_info in positions:
                    player_id, position = player_info.split(":")
                    if int(player_id) == int(self.net.id):
                        x, y = map(int, position.split(","))
                        self.player.x = x
                        self.player.y = y
                        return True
        return False

    def send_data(self):
        data = str(self.net.id) + ":" + str(self.player.x) + "," + str(self.player.y)
        reply = self.net.send(data)
        return reply

    @staticmethod
    def parse_data(data, current_player_id):
        try:
            player_positions = []
            for player_info in data.split("|"):
                player_id, position = player_info.split(":")
                x, y = map(int, position.split(","))
                player_positions.append((x, y))

            # Pobieramy indeks bieżącego gracza
            current_player_index = int(current_player_id)

            # Usuwamy dane bieżącego gracza z listy
            player_positions.pop(current_player_index)

            # Zwracamy pozycję bieżącego gracza i pozycje obu przeciwników jako osobne wartości
            return player_positions[0][0], player_positions[0][1], player_positions[1][0], player_positions[1][1]
        except:
            return 0, 0, 0, 0


if __name__ == "__main__":
    game = Game(800, 600)
    game.run()

