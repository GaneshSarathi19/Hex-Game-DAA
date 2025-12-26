import pygame as pg
from funcs import *
from Game import *
from consts import *

game = Game(SIZE)
game.loadData()

# button initializing
pause = Button((30, 30), 50, img=game.pause_img)
buttons = [pause]
#print(game.state)
# draw()
run = True
while run:
    # sticking to fps
    game.clock.tick(FPS)
    if not game.started:
        run = game.startScreen()
    else:
        # --------------------EVENTS---------------------
        game.highlight(pg.mouse.get_pos())
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # if exit button is pressed
                run = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                # human player (player 1) moves
                old_move = game.move
                game.tick(pg.mouse.get_pos())
                # If human made a move, CPU moves automatically
                if old_move == 1 and game.move == 2:
                    game.cpuMove()
                if pause.triggered(channel=game.click_sound_channel,
                                   sound=game.click_sound,
                                   playing=game.sound_state):
                    run = game.pauseScreen()

        # highlight buttons
        for button in buttons:
            button.highlighted()

        # --------------------STUFF-----------------------
        game.screen.fill(game.bg_color)
        game.showGrid()
        for button in buttons:
            button.show(game.screen)
        if game.checkWin():
            run = game.GOScreen(game.checkWin())
    # double processing
    pg.display.flip()

pg.quit()
