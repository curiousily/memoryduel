from random import Random
from tkinter import *
from tkinter import ttk
from configparser import ConfigParser

LEFT = 1
UP = 2
RIGHT = 3
DOWN = 4

sides = [0, 3, 4, 1, 2]

NO_ID = -1

def opposite_side(side):
    return sides[side]

class IdGenerator():

    def __init__(self, starting_at = 0):
        self.id = starting_at - 1

    def next_id(self):
        self.id += 1
        return self.id

config = ConfigParser()
config.read('config.ini')
game_config = config['DEFAULT']

id_generator = IdGenerator()

class Board:
    def __init__(self, rows, columns):
        self.tiles = {}
        self.flipped_tiles = []
        self.rows = rows
        self.columns = columns
        self.unsolved_count = rows * columns

    def add_tile(self, tile):
        self.tiles[tile.id] = tile

    def connect_all_tiles(self):
        for row in range(1, self.rows + 1):
            for col in range(1, self.columns + 1):
                tile_id = self._tile_id(row, col)
                left_parent = self.tile_at(row, col - 1)
                if not left_parent == None:
                    self.connect_tiles(left_parent.id, tile_id, RIGHT)
                top_parent = self.tile_at(row - 1, col)
                if not top_parent == None:
                    self.connect_tiles(top_parent.id, tile_id, DOWN)

    def connect_tiles(self, parent_id, child_id, side):
        self.tiles[parent_id].add_neighbour(child_id, side)
        self.tiles[child_id].add_neighbour(parent_id, opposite_side(side))

    def _tile_id(self, row, column):
        row -= 1
        column -= 1
        return row * self.columns + column

    def tile_at(self, row, column):
        if row < 1 or column < 1:
            return None
        return self.tiles[self._tile_id(row, column)]

    def flip_tile(self, row, column):
        tile_id = self._tile_id(row, column)
        self.tiles[tile_id].flip()
        self.flipped_tiles.append(tile_id)
        return tile_id

    def has_two_flipped_tiles(self):
        return len(self.flipped_tiles) == 2

    def tiles_not_same(self):
        if not self.tiles[self.flipped_tiles[0]].image_path == self.tiles[self.flipped_tiles[1]].image_path :
            self.tiles[self.flipped_tiles[0]].flip()
            self.tiles[self.flipped_tiles[1]].flip()
            return True
        else:
            self.tiles[self.flipped_tiles[0]].set_solved()
            self.tiles[self.flipped_tiles[1]].set_solved()
            self.unsolved_count -= 2
            return False

    def clear_flipped_tiles(self):
        self.flipped_tiles = []

    def is_solved(self):
        return self.unsolved_count == 0

    def cannot_flip_tile(self, row, column):
        return self.tiles[self._tile_id(row, column)].is_flipped()

    def mark_tiles_opened(self):
        self.tiles[self.flipped_tiles[0]].set_opened()
        self.tiles[self.flipped_tiles[1]].set_opened()

    def at_least_one_tile_opened(self):
        return self.tiles[self.flipped_tiles[0]].is_opened() or self.tiles[self.flipped_tiles[1]].is_opened()

    def __print(self):
        for row in range(1, self.rows + 1):
            for col in range(1, self.columns + 1):
                tile = self.tile_at(row, col)
                print(tile.image_path)

class Tile:

    def __init__(self, image_path):
        self.neighbours = {LEFT : None, UP : None, RIGHT : None, DOWN : None}
        self.id = id_generator.next_id()
        self.image_path = image_path
        self.flipped = False
        self.solved = False
        self.opened = False

    def add_neighbour(self, tile_id, side):
        self.neighbours[side] = tile_id

    def flip(self):
        self.flipped = not self.flipped

    def is_flipped(self):
        return self.flipped

    def set_solved(self):
        self.solved = True

    def is_solved(self):
        return self.solved

    def set_opened(self):
        self.opened = True

    def is_opened(self):
        return self.opened

class Player:

    def __init__(self, name, row, column):
        self.id = NO_ID
        self.name = name
        self.orientation = UP
        self.column = column
        self.row = row

    def move(self, side, constraint = 0):
        if side == LEFT:
            self.orientation = LEFT
            if self.column - 1 > 0:
                self.column -= 1
        if side == UP:
            self.orientation = UP
            if self.row - 1 > 0:
                self.row -= 1
        if side == RIGHT:
            self.orientation = RIGHT
            if self.column + 1 <= constraint:
                self.column += 1
        if side == DOWN:
            self.orientation = DOWN
            if self.row + 1 <= constraint:
                self.row += 1

#noinspection PyUnusedLocal
class ApplicationFrame(Frame):

    NO_TIME = 1
    LEVEL_COMPLETE = 2

    def __init__(self, player, board, master = None):
        Frame.__init__(self, master)
        self.grid()
        self.board = board
        self.player = player
        self.canvas = Canvas(self)
        position_descriptor = PositionDescriptor(self.board.rows, self.board.columns)
        self.board_painter = BoardPainter(self.board, self.canvas, position_descriptor)
        self.player_painter = PlayerPainter(self.player, self.canvas, position_descriptor)
        self.create_widgets()
        self.bind_events()
        self.remaining_seconds = int(game_config['RemainingSeconds'])
        self.is_running = True
        self.update_timer()

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")
        self.style.configure("RemainingTime.Label", relief="flat", foreground = "#006600")

        self.quit_button = ttk.Button(self, text="Quit", command = self.quit)
        self.quit_button.pack(anchor = 'nw', side = 'top')
        self.time_label = ttk.Label(self, font=("Arial", 16), style="RemainingTime.Label")
        self.time_label.pack(anchor = 'center', side = 'top')
        self.canvas.pack(side = 'bottom')
        self.board_painter.draw()
        self.player_painter.draw()

    def bind_events(self):
        self.canvas.bind_all("<Key-Up>", self.on_up_handler)
        self.canvas.bind_all("<Key-Down>", self.on_down_handler)
        self.canvas.bind_all("<Key-Left>", self.on_left_handler)
        self.canvas.bind_all("<Key-Right>", self.on_right_handler)
        self.canvas.bind_all("<Key-space>", self.on_space_handler)

    def unbind_events(self):
        self.canvas.unbind_all("<Key-Up>")
        self.canvas.unbind_all("<Key-Down>")
        self.canvas.unbind_all("<Key-Left>")
        self.canvas.unbind_all("<Key-Right>")
        self.canvas.unbind_all("<Key-space>")

    def on_up_handler(self, event):
        self.player.move(UP)
        self.player_painter.draw(UP)

    def on_down_handler(self, event):
        self.player.move(DOWN, self.board.rows)
        self.player_painter.draw(DOWN)

    def on_left_handler(self, event):
        self.player.move(LEFT)
        self.player_painter.draw(LEFT)

    def on_right_handler(self, event):
        self.player.move(RIGHT, self.board.columns)
        self.player_painter.draw(RIGHT)

    def on_space_handler(self, event):
        if self.board.cannot_flip_tile(self.player.row, self.player.column):
            return
        tile_id = self.board.flip_tile(self.player.row, self.player.column)
        self.board_painter.draw_tile(tile_id, self.player.row, self.player.column)

        if self.board.has_two_flipped_tiles():
            self.update()
            self.after(500)
            if self.board.tiles_not_same():
                self.board_painter.draw_tile(self.board.flipped_tiles[0], self.player.row, self.player.column)
                self.board_painter.draw_tile(self.board.flipped_tiles[1], self.player.row, self.player.column)
                if self.board.at_least_one_tile_opened():
                    self.add_remaining_seconds(int(game_config['PairNotFoundBonus']))
                self.board.mark_tiles_opened()
            else:
                self.add_remaining_seconds(int(game_config['PairFoundBonus']))
            self.board.clear_flipped_tiles()
        self.player_painter.draw(self.player.orientation)
        if self.board.is_solved():
            self.on_game_complete_handler(self.LEVEL_COMPLETE)

    def on_game_complete_handler(self, reason = NO_TIME):
        self.is_running = False
        self.unbind_events()
        if reason == self.NO_TIME:
            self.style.configure("RemainingTime.Label", relief="flat", foreground = game_config['LittleTimeRemainingColor'])
            self.time_label.config(text = "0 Seconds")
            dialog = DialogWindow(game_config['NoTimeTitle'], game_config['NoTimeDescription'])
        else:
            self.style.configure("RemainingTime.Label", relief="flat", foreground = game_config['PlentyTimeRemainingColor'])
            dialog = DialogWindow(game_config['LevelCompleteTitle'], game_config['LevelCompleteDescription'])
        dialog.show()

    def add_remaining_seconds(self, seconds):
        self.remaining_seconds += seconds
        if self.remaining_seconds <= 0:
            self.on_game_complete_handler()

    def update_timer(self):
        if not self.is_running:
            return
        self.remaining_seconds -= 1
        if self.remaining_seconds <= int(game_config['CriticalTimeLeft']):
            self.style.configure("RemainingTime.Label", relief="flat", foreground = game_config['LittleTimeRemainingColor'])
        else:
            self.style.configure("RemainingTime.Label", relief="flat", foreground = game_config['PlentyTimeRemainingColor'])
        self.time_label.config( text = str(self.remaining_seconds) + " Seconds")
        if self.remaining_seconds <= 0:
            self.on_game_complete_handler()
        self.after(1000, self.update_timer)


class DialogWindow():

    WIDTH = int(game_config['EndGameWindowWidth'])
    HEIGHT = int(game_config['EndGameWindowHeight'])

    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.dialog = Toplevel()

    def show(self):
        self.dialog.focus()
        self.dialog.title(self.title)

        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()

        ttk.Label(self.dialog, text = self.description, font=("Arial", 16)).pack(ipady = self.HEIGHT / 3)
        button = ttk.Button(self.dialog, text = "Ok", command = self.dialog.quit)
        button.focus()
        button.pack()

        self.dialog.geometry('%dx%d+%d+%d' % (self.WIDTH, self.HEIGHT, (screen_width / 2) - (self.WIDTH / 2), (screen_height / 2) - (self.HEIGHT / 2)))
        self.dialog.grid()


class BoardPainter:

    def __init__(self, board, canvas, position_descriptor):
        self.board = board
        self.canvas = canvas
        self.canvas.configure(width =  int(game_config['BoardWidth']), height = int(game_config['BoardHeight']))
        self.position_descriptor = position_descriptor
        self.id_mappings = {}
        self.tile_images = {}
        self.image_id_mappings = {}
        for tile in self.board.tiles.values():
            self.tile_images[tile.id] = PhotoImage(file = tile.image_path)
        self.trap_image = PhotoImage(file = game_config['TileBackgroundImage'])

    def draw(self):
        self.background_image = PhotoImage(file = game_config['BackgroundImage'])
        self.canvas.create_image(int(game_config['BoardWidth']) / 2, int(game_config['BoardHeight']) / 2, image = self.background_image)

        for row in range(1, self.board.rows + 1):
            for column in range(1, self.board.columns + 1):
                self.id_mappings[self.board._tile_id(row, column)] = self.canvas.create_image(self.position_descriptor.next_tile(row, column), image = self.trap_image)

    def draw_tile(self, tile_id, row = 0, column = 0):
        if self.board.tiles[tile_id].is_flipped():
            self.image_id_mappings[tile_id] = self.canvas.create_image(self.position_descriptor.next_tile_image(row, column), image = self.tile_images[tile_id])
        else:
            self.canvas.delete(self.image_id_mappings[tile_id])

class PlayerPainter:

    PLAYER_WIDTH = int(game_config['PlayerWidth'])
    PLAYER_HEIGHT = int(game_config['PlayerHeight'])

    def __init__(self, player, canvas, position_descriptor):
        self.player = player
        self.canvas = canvas
        self.position_descriptor = position_descriptor

    def draw(self, orientation = UP):
        if not self.player.id == NO_ID:
            self.canvas.delete(self.player.id)
        file = game_config['PlayerUpImage']
        if orientation == LEFT:
            file = game_config['PlayerLeftImage']
        if orientation == DOWN:
            file = game_config['PlayerDownImage']
        if orientation == RIGHT:
            file = game_config['PlayerRightImage']
        player_image = PhotoImage(file = file)
        self.player.id = self.canvas.create_image(self.position_descriptor.player(self.player.row, self.player.column), image = player_image)
        self.player_image = player_image

class PositionDescriptor:

    TILE_WIDTH = int(game_config['TileWidth'])
    TILE_HEIGHT = int(game_config['TileHeight'])
    TILE_PADDING = int(game_config['TilePadding'])

    def __init__(self, board_rows, board_columns):
        self.board_rows = board_rows
        self.board_columns = board_columns

    def initial_padding_width(self):
        tiles_width = self.board_columns * (self.TILE_WIDTH + self.TILE_PADDING) - (self.TILE_PADDING + self.TILE_PADDING)
        return (int(game_config['BoardWidth']) - tiles_width) / 2

    def initial_padding_height(self):
        tiles_height = self.board_rows * (self.TILE_HEIGHT + self.TILE_PADDING) - (self.TILE_PADDING + self.TILE_PADDING)
        return (int(game_config['BoardHeight']) - tiles_height) / 2

    def next_tile(self, row, column):
        current_x = (column - 1) * self.TILE_WIDTH
        current_y = (row - 1) * self.TILE_HEIGHT
        return current_x + self.TILE_PADDING + self.initial_padding_width() + 65,  \
               current_y + self.TILE_PADDING + self.initial_padding_height() + 65

    def next_tile_image(self, row, column):
        current_x = (column - 1) * self.TILE_WIDTH
        current_y = (row - 1) * self.TILE_HEIGHT
        return current_x + self.TILE_PADDING + self.initial_padding_width() + self.TILE_WIDTH / 2 - self.TILE_PADDING / 2,  \
               current_y + self.TILE_PADDING + self.initial_padding_height() + self.TILE_HEIGHT / 2 - self.TILE_PADDING / 2

    def player(self, row, column):
        current_x = (column - 1)  * self.TILE_WIDTH
        current_y = (row - 1) * self.TILE_HEIGHT
        return current_x + self.TILE_PADDING + 60 + self.initial_padding_width(),  \
               current_y + self.TILE_PADDING + 60 + self.initial_padding_height()

class GameCreator:

    def __init__(self, rows, columns, player_name):
        self.tiles = rows * columns
        if not self.tiles % 2 == 0:
            return
        if self.tiles > int(game_config['MaxPairTiles']):
            return
        self.board = Board(rows, columns)
        self.player = Player(player_name, 1, 1)

    def start_game(self):
        self._fill_board()
        width = int(game_config['BoardWidth'])
        height = int(game_config['BoardHeight'])
        root_window = Tk()
        screen_width = root_window.winfo_screenwidth()
        screen_height = root_window.winfo_screenheight()
        application_frame = ApplicationFrame(self.player, self.board, root_window)
        application_frame.master.title(game_config['GameTitle'])
        root_window.geometry('%dx%d+%d+%d' % (width, height, (screen_width / 2) - (width / 2), (screen_height / 2) - (height / 2)))
        application_frame.mainloop()

    def _fill_board(self):
        tiles_needed = self.tiles / 2
        tiles_available = int(game_config['MaxPairTiles']) / 2
        random_generator = Random()
        tiles_to_get = set()
        while not len(tiles_to_get) == tiles_needed:
            rand_num = random_generator.randint(1, tiles_available)
            if not rand_num in tiles_to_get:
                tiles_to_get.add(rand_num)

        all_tiles = []
        while not len(tiles_to_get) == 0:
            tile_num = tiles_to_get.pop()
            all_tiles.append(tile_num)
            all_tiles.append(tile_num)
        random_generator.shuffle(all_tiles)

        for tile in all_tiles:
            self.board.add_tile(Tile('%s%s.gif' % (game_config['TilesDir'], (str(tile)))))
        self.board.connect_all_tiles()

creator = GameCreator(int(game_config['BoardRows']), int(game_config['BoardColumns']), game_config['PlayerName'])
creator.start_game()