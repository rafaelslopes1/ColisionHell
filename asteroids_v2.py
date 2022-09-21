import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import asyncio

import numpy as np


class Asteroids:
    def __init__(self):
        self.vertices = self.genSquareVertices()
        self.squareEdges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        self.default_position = [0, 0, 0]
        self.scale = np.random.randint(1, 3)

    def solid(self):
        glPushMatrix()
        glTranslatef(
            self.default_position[0], self.default_position[1], self.default_position[2])
        glScalef(self.scale, self.scale, 0)
        glBegin(GL_QUADS)
        for squareEdge in self.squareEdges:
            for squareVertex in squareEdge:
                glVertex2fv(self.vertices[squareVertex])
        glEnd()
        glPopMatrix()

    def genSquareVertices(self):
        mu, sigma = 0, 2  # mean and standard deviation
        y1 = 6
        y0 = y1 + 0.5
        y2 = y1
        y3 = y0
        x1 = np.random.normal(mu, sigma)
        x2 = x1 - 0.5
        x3 = x2
        x0 = x1
        return [[x1, y1-1], [x2, y2-1], [x3, y3-1], [x0, y0-1]]

    def getCenter(self, vertices):
        x = (vertices[0][0] - vertices[3][0])/2
        y = (vertices[0][1] - vertices[3][1])/2
        z = 0
        return [x, y, z]


class Player:
    def __init__(self):
        self.triangleVertices_2 = [[-0.5, -5], [0.5, -5], [0, -4]]
        self.triangleEdges = [[0, 1], [0, 2], [1, 2]]
        self.default_position = [0, 0, 0, 0]

        self.right = False
        self.left = False

    def solid(self):
        glPushMatrix()

        glTranslatef(self.default_position[0], self.default_position[1], self.default_position[2])

        if not self.right and not self.left:
            glTranslatef(self.default_position[0], self.default_position[1], self.default_position[2])
            glRotatef(0, 0, 0, 1)
        elif self.right:
            glTranslatef(self.default_position[0]+0.5, self.default_position[1], self.default_position[2])
            glRotatef(-7, 0, 0, 1)
        elif self.left:
            glTranslatef(self.default_position[0]-0.5, self.default_position[1], self.default_position[2])
            glRotatef(7, 0, 0, 1)

        glBegin(GL_QUADS)
        for triangleEdge in self.triangleEdges:
            for triangleVertex in triangleEdge:
                glVertex2fv(self.triangleVertices_2[triangleVertex])
        glEnd()
        glPopMatrix()

    def move(self):
        keys = pg.key.get_pressed()

        if keys[pg.K_LEFT]:
            self.default_position[0] -= 0.05
            self.left = True
        elif keys[pg.K_RIGHT]:
            self.default_position[0] += 0.05
            self.right = True

        if not keys[pg.K_LEFT]:
            self.left = False
        if not keys[pg.K_RIGHT]:
            self.right = False


async def collision(player, asteroid):
    # print(player.triangleVertices_2[2][0] + player.default_position[0], asteroid.vertices[0][1] + asteroid.default_position[1], asteroid.vertices[2][1] + asteroid.default_position[1])
    if (
            asteroid.vertices[1][0]*asteroid.scale <= player.triangleVertices_2[2][0] + player.default_position[0] <=
            asteroid.vertices[0][0]*asteroid.scale and
            asteroid.vertices[0][1]*asteroid.scale + asteroid.default_position[1] <= player.triangleVertices_2[2][1] <=
            asteroid.vertices[2][1]*asteroid.scale +
        asteroid.default_position[1]
    ):
        return True
    else:
        return False


def createScreen(width, height):
    pg.init()
    screen = pg.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pg.display.set_caption('Collision HELL')
    return screen


def draw_text(position, text_string, size=50, from_center=False, color=(255, 255, 255), back_color=None):
    """Function for drawing text on screen"""
    font = pg.font.SysFont('timesnewroman', size)
    text_surface = font.render(text_string, True, color, back_color)
    img_data = pg.image.tostring(text_surface, "RGBA", True)
    ix, iy = text_surface.get_width(), text_surface.get_height()
    x = 20
    if from_center:
        x = position[0] - int(ix / 2)
    else:
        x = position[0]
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glWindowPos2i(x, position[1])
    glDrawPixels(ix, iy, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glDisable(GL_BLEND)


async def main():
    count_fall = 0
    count_new = 0
    count_score = 0
    full = False
    game_over = False
    score = 0

    width, height = 1200, 800
    window = createScreen(width, height)

    gluPerspective(90, (width / height), 0.1, 50.0)

    bg = pg.image.load("bg.jpg")
    bg = pg.transform.scale(bg, (width, height))

    glTranslatef(0.0, 0.0, -5)

    player = Player()
    asteroids = []
    
    song = 'song.mp3'
    pg.mixer.init()
    pg.mixer.music.load(song)
    pg.mixer.music.play()

    while True:
        window.fill((0, 0, 0))
        window.blit(bg, (0, 0))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()

        player.move()

        if count_score % 30 == 0:
            score += 1
            count_score = 0

        count_score += 1

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_text([40, 50], "Score: {}".format(score), 22)

        player.solid()

        # A cada 30 unidades surge um novo asteroid
        # e caso a quantidade máxima seja atingida,
        # sai de tela e é deletado o asteroid mais antigo na lista
        if count_new % 50 == 0:
            if full:
                asteroids.pop(0)
            asteroid = Asteroids()
            asteroid.solid()

            asteroids.append(asteroid)
            count_new = 0

        count_new += 1

        # Quando a fila enche, o contador limita a lista a N elementos
        if not full:
            count_fall += 1

        if count_fall >= 400:
            full = True

        # Lógica acima
        for element in asteroids:
            element.default_position[1] -= 0.05
            element.solid()

        if game_over:
            pg.quit()
            quit()

        for element in asteroids:
            # Collision
            if await collision(player, element):
                game_over = True

        pg.display.flip()
        pg.time.wait(10)


if __name__ == '__main__':
    asyncio.run(main())
