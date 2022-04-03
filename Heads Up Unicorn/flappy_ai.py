import pygame
import neat
# import time
import os
import random
# import visualize
# import pickle
pygame.font.init()

WIN_WIDTH = 350
WIN_HEIGHT = 600
FLOOR = 550
STAT_FONT = pygame.font.SysFont("Times New Roman", 20)
DRAW_LINES = False
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

UNICORN = pygame.image.load('gallery/sprites/uni1.1.png').convert_alpha()
BARRIER = pygame.image.load('gallery/sprites/pipe.png').convert_alpha()
BASE = pygame.image.load('gallery/sprites/base1.1.png').convert_alpha()
BACKGROUND1 = pygame.image.load('gallery/sprites/bg.png').convert_alpha()

gen = 0


class Unicorn:
    IMGS = UNICORN
    MAX_ROTATION = 25
    ROTATION_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS

    def jump(self):
        self.vel = -5.5
        self.tick_count = 0  # for how many sec the unicorn is moving for
        self.height = self.y

    def move(self):
        self.tick_count += 1

        # for downward acceleration
        displacement = self.vel*self.tick_count + 1.5*3*self.tick_count**2

        # terminal velocity
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16
        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # rotation
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VEL

    def draw(self, win):
        self.img_count += 1
        # when unicorn is nose diving
        if self.tilt <= -80:
            self.img = self.IMGS
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Barrier:
    GAP = 120
    BARRIER_VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100 # check
        self.top = 0
        self.bottom = 0
        self.BARRIER_TOP = pygame.transform.flip(BARRIER, False, True)  # rotated pipe
        self.BARRIER_BOTTOM = BARRIER  # original pipe
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 300)
        self.top = self.height - self.BARRIER_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.BARRIER_VEL

    def draw(self, win):
        win.blit(self.BARRIER_TOP, (self.x, self.top))
        win.blit(self.BARRIER_BOTTOM, (self.x, self.bottom))

    def collide(self, unicorn, win):
        # mask collision, to get pixel perfect collision
        # get list of pixels and compare if two pixels are overlapping or not
        unicorn_mask = unicorn.get_mask()
        top_mask = pygame.mask.from_surface(self.BARRIER_TOP)
        bottom_mask = pygame.mask.from_surface(self.BARRIER_BOTTOM)

        # offset of bird from mask
        top_offset = (self.x - unicorn.x, self.top - round(unicorn.y))
        bottom_offset = (self.x - unicorn.x, self.bottom - round(unicorn.y))

        # finding point of collision
        bottom_point = unicorn_mask.overlap(bottom_mask, bottom_offset)
        top_point = unicorn_mask.overlap(top_mask, top_offset)

        if top_point or bottom_point:
            return True
        else:
            return False


class Base:
    BASE_VEL = 5
    WIDTH = BASE.get_width()
    IMG = BASE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        # move base to left , once it moves out of screen place the 2nd one on screen . then place the first one
        # behind the 2nd one
        self.x1 -= self.BASE_VEL
        self.x2 -= self.BASE_VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, unicorns, barriers, base, score, gen, barrier_ind):
    if gen == 0:
        gen = 1
    win.blit(BACKGROUND1, (0, 0))

    for b in barriers:
        b.draw(win)

    base.draw(win)
    for unicorn in unicorns:
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0),
                                 (unicorn.x + unicorn.img.get_width() / 2, unicorn.y + unicorn.img.get_height() / 2),
                                 (barriers[barrier_ind].x + barriers[barrier_ind].PIPE_TOP.get_width() / 2,
                                  barriers[barrier_ind].height),
                                 5)
                pygame.draw.line(win, (255, 0, 0),
                                 (unicorn.x + unicorn.img.get_width() / 2, unicorn.y + unicorn.img.get_height() / 2), (
                                 barriers[barrier_ind].x + barriers[barrier_ind].PIPE_BOTTOM.get_width() / 2,
                                 barriers[barrier_ind].bottom), 5)
            except:
                pass
        unicorn.draw(win)

    # blit score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - 10 - score_label.get_width(), 10))
    # blit generations
    gen_label = STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 255))
    win.blit(gen_label, (10, 10))
    # blit alive
    alive_label = STAT_FONT.render("Alive: " + str(score), 1, (255, 255, 255))
    win.blit(alive_label, (10, 50))

    pygame.display.update()


def main(genomes, config):
    global WIN, gen
    win = WIN
    gen += 1
    pygame.display.set_caption('Heads Up Unicorn 🦄')
    nets = []
    ge = []
    # unicorn = Unicorn(130, 170)  # 230 , 350  for 1 unicorn
    unicorns = []  # to make algorithm work for many unicorns

    # ge is a tuple has has (genome id, genome object) therefore we run the loop with _ (for genome id)
    for genome_id, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        unicorns.append(Unicorn(130, 170))
        ge.append(g)

    base = Base(FLOOR)
    barriers = [Barrier(400)]
    # win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run and len(unicorns) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        barrier_ind = 0
        if len(unicorns) > 0:
            if len(barriers) > 1 and unicorns[0].x > barriers[0].x + barriers[0].BARRIER_TOP.get_width():
                barrier_ind = 1  # if bird crosses a barrier then look for the coordinates of next pipe
        # check for it
        # else:
        #     run = False
        #     break  # if no birds left the quit the game

        for x, unicorn in enumerate(unicorns):  # give each unicorn a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.1
            unicorn.move()

            output = nets[unicorns.index(unicorn)].activate((unicorn.y, abs(unicorn.y - barriers[barrier_ind].height),
                                                             abs(unicorn.y - barriers[barrier_ind].bottom)))
            if output[0] > 0.5:
                unicorn.jump()

        base.move()
        add_barrier = False
        rem = []  # list of pipes to remove
        for b in barriers:
            b.move()
            # check for collision
            for unicorn in unicorns:
                if b.collide(unicorn, win):
                    ge[unicorns.index(unicorn)].fitness -= 1  # if unicorn hits pipe, then reduce 1 from fitness score
                    nets.pop(unicorns.index(unicorn))
                    ge.pop(unicorns.index(unicorn))
                    unicorns.pop(unicorns.index(unicorn))

            if b.x + b.BARRIER_TOP.get_width() < 0:
                # once barrier moves out of screen , generate new barrier
                rem.append(b)

            if not b.passed and b.x < unicorn.x:
                # check is bird passed the barrier, if yes generate new pipe
                b.passed = True
                add_barrier = True

        if add_barrier:
            score += 1
            for g in ge:
                g.fitness += 5
            barriers.append(Barrier(WIN_WIDTH))  # Barrier(400)

        for r in rem:
            barriers.remove(r)

        for unicorn in unicorns:
            if unicorn.y + unicorn.img.get_height() - 10 >= FLOOR or unicorn.y < -50:
                nets.pop(unicorns.index(unicorn))
                ge.pop(unicorns.index(unicorn))
                unicorns.pop(unicorns.index(unicorn))

        draw_window(WIN, unicorns, barriers, base, score, gen, barrier_ind)


def run(conf_path):
    # defining the properties from the config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, conf_path)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(main, 50)
    # 50 is the no of generations for which the neural network will run

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    run(config_path)








'''
NEAT is a genetic algorithm which helps the unicorn to learn by itself to play the game i.e not collide with the 
barrier. 
NEAT = Neural Evolution of Augmenting Topology
it is based on Natural Selection
    NATURAL SELECTION ( means learn and get better till you become best at it)
    
Neural networks on layers
first layer: Input layer. it contains the info we provide to our neural network
we are providing 3 parameters or info in the input layer:
    1. position y of unicorn
    2. position of top barrier
    3. position of bottom barrier
Last Layer: Output Layer. it tells us what we need to do. or the best move. here it tells whether to jump or go down

here each of input neuron will be connected to output neuron using 1 connection
each connection has a weight associated to it
we will then calculate the weighted sum ie. sum of (weight* input value) of all inputs

after this we perform 2 operation on the output neuron
    1. Bias = helps to shift the position of unicorn up or down and bring it in the right position
        add this Bias to weighted sum
    2. Activation Function = Apply this func to the above calculated value
        it helps in getting the value for output neuron between 2 fixed nos. so we can decide whether ot jump or not
        the function used here is TanH
        TanH will check if the value is closest to 1 or -1
        
    eg. if weighted sum = -2755
    then output = F(-2755)
    => TanH(-2755) = -1 , since it more closer to -1
    so we can set a criteria like:
    if output > 0.5: 
        jump
    else:
        don't jump
        
   So we will start by generating a random population of unicorns. Each population will be controlled by a Neural Network
   it will have random weights and random biases. We consider population size of 100
   we will test all these networks on the game 
   
   here the fitness of network will be determined by how far the bird can go or what is the highest score
   after this we will select the population of unicorns with the highest fitness score and breed them together to
    produce a new species or population. 
    this way we will get the most fit population of unicorns
    
    
    NEAT will randomly assign weights to the connection and also generate new neurons randomly and remove some neurons 
    to generate a topology or architecture that is best suitable
    It will automatically decide whether a complex architecture is required or our game can work best with a simple one
         
   
'''






