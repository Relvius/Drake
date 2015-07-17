import libtcodpy as lt
from src.world import gen

"""
Entities
"""


class Location(object):
    def __init__(self, col, row, char, f_color=lt.white):
        self.row = row
        self.col = col

        self.char = char
        self.f_color = f_color

    def draw(self):
        if lt.map_is_in_fov(fov_map, self.col, self.row):
            lt.console_set_char_foreground(area_con, self.row, self.col, self.f_color)
            light = area[self.col][self.row].b_color
            if light.r > 175 and light.g > 175 and light.b > 130:
                lt.console_set_char_foreground(area_con, self.row, self.col, lt.black)
            lt.console_set_char(area_con, self.row, self.col, self.char)

    def distance(self, other):
        return int((self.row - other.row) ** 2 + (self.col - other.col) ** 2) ** 0.5

    def clear(self):
        lt.console_put_char(area_con, self.row, self.col, ' ', lt.BKGND_NONE)


class Tile(Location):
    def __init__(self, col, row, char, f_color=lt.white, b_color=lt.black, blocks_movement=True, blocks_light=False, distance=-1):
        super(Tile, self).__init__(col, row, char, f_color)
        self.b_color = b_color
        self.explored = False
        self.distance = distance

        self.blocks_movement = blocks_movement
        self.blocks_light = blocks_light

    def draw(self, in_sight):
        if in_sight:
            lt.console_set_char_foreground(area_con, self.row, self.col, self.f_color)
            lt.console_set_char_background(area_con, self.row, self.col, self.b_color)
            lt.console_set_char(area_con, self.row, self.col, self.char)
            self.explored = True
        elif self.explored:
            f_color = lt.color_lerp(fog_color, self.f_color, fog_density)
            b_color = lt.color_lerp(fog_color, self.b_color, fog_density)
            lt.console_set_char_background(area_con, self.row, self.col, b_color)
            lt.console_set_default_foreground(area_con, f_color)
            lt.console_put_char(area_con, self.row, self.col, self.char)
        else:
            lt.console_set_char_background(area_con, self.row, self.col, fog)


class Structure():
    def __init__(self, col, row, graphic, f_color):
        self.col = col
        self.row = row
        self.graphic = graphic
        self.f_color = f_color

    def draw(self):
        for col_offset in xrange(len(self.graphic)):
            for row_offset in xrange(len(self.graphic[0])):
                row = self.row + row_offset
                col = self.col + col_offset
                char = self.graphic[col_offset][row_offset]
                if lt.map_is_in_fov(fov_map, col, row):
                    lt.console_set_default_foreground(area_con, self.f_color)
                    lt.console_put_char(area_con, row, col, char)
                elif area[col][row].explored:
                    color = lt.color_lerp(fog_color, self.f_color, fog_density)
                    lt.console_set_default_foreground(area_con, color)
                    lt.console_put_char(area_con, row, col, char)


"""
Rendering
"""


def render_area(fov_map, offset_col, offset_row, MAP_WIDTH, MAP_HEIGHT):
    lt.console_clear(area_con)
    for n_row in xrange(MAP_WIDTH):
        for n_col in xrange(MAP_HEIGHT):
            row = n_row + offset_row
            col = n_col + offset_col
            if 0 <= row < len(area[0]) and 0 <= col < len(area):
                if lt.map_is_in_fov(fov_map, col, row):
                    area[col][row].draw(True)
                else:
                    area[col][row].draw(False)
    for structure in structures:
        structure.draw()
    return area_con, fog


"""
Creation
"""


def new_area(biome, width, height):
    global area_con
    area_con = lt.console_new(width, height)

    global area, fov_map, fov_recompute, fog_color, fog_density, fog
    area = [[Tile(col, row, ' ') for row in xrange(width)] for col in xrange(height)]
    area, fov_map = gen.make_area(area, biome, 1)

    if biome == "cave":
        fog_color = lt.Color(30, 0, 0)
        fog_density = 0.55
        fog = lt.Color(20, 10, 15)

    global structures
    structures = []

    return area, area_con, structures, fov_map