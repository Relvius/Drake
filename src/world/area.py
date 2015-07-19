"""
Puts together a lot of the information about area generation. Essentially "packages up" the raw data from gen.py.
"""

import libtcodpy as lt
from src.world import gen
import src.items as itt
import random

"""
Entities
"""


class Location(object):
    def __init__(self, col, row, char, f_color=lt.white):
        self.row = row
        self.col = col

        self.char = char
        self.f_color = f_color

    def draw(self, area):
        if lt.map_is_in_fov(area.fov_map, self.col, self.row):
            lt.console_set_char_foreground(area.con, self.row, self.col, self.f_color)
            light = area.area[self.col][self.row].b_color
            if light.r > 175 and light.g > 175 and light.b > 130:
                lt.console_set_char_foreground(area.con, self.row, self.col, lt.black)
            lt.console_set_char(area.con, self.row, self.col, self.char)

    def distance(self, other):
        return int((self.row - other.row) ** 2 + (self.col - other.col) ** 2) ** 0.5

    def clear(self, area):
        lt.console_put_char(area.con, self.row, self.col, ' ', lt.BKGND_NONE)


class Tile(Location):
    def __init__(self, col, row, char, f_color=lt.white, b_color=lt.black, blocks_movement=True, blocks_light=False, distance=-1):
        super(Tile, self).__init__(col, row, char, f_color)
        self.b_color = b_color
        self.explored = False
        self.distance = distance

        self.blocks_movement = blocks_movement
        self.blocks_light = blocks_light

    def draw(self, in_sight, area):
        if in_sight:
            lt.console_set_char_foreground(area.con, self.row, self.col, self.f_color)
            lt.console_set_char_background(area.con, self.row, self.col, self.b_color)
            lt.console_set_char(area.con, self.row, self.col, self.char)
            self.explored = True
        elif self.explored:
            f_color = lt.color_lerp(area.fog, self.f_color, area.fog_density)
            b_color = lt.color_lerp(area.fog, self.b_color, area.fog_density)
            lt.console_set_char_background(area.con, self.row, self.col, b_color)
            lt.console_set_default_foreground(area.con, f_color)
            lt.console_put_char(area.con, self.row, self.col, self.char)
        else:
            lt.console_set_char_background(area.con, self.row, self.col, area.fog)


class Structure:
    def __init__(self, col, row, graphic, f_color):
        self.col = col
        self.row = row
        self.graphic = graphic
        self.f_color = f_color

    def draw(self, area):
        for col_offset in xrange(len(self.graphic)):
            for row_offset in xrange(len(self.graphic[0])):
                row = self.row + row_offset
                col = self.col + col_offset
                char = self.graphic[col_offset][row_offset]
                if lt.map_is_in_fov(area.fov_map, col, row):
                    lt.console_set_default_foreground(area.area.con, self.f_color)
                    lt.console_put_char(area.area.con, row, col, char)
                elif area[col][row].explored:
                    color = lt.color_lerp(area.fog, self.f_color, area.fog_density)
                    lt.console_set_default_foreground(area.con, color)
                    lt.console_put_char(area.con, row, col, char)


class Area:
    def __init__(self, biome, height, width):
        self.con = lt.console_new(width, height)
        self.area = [[Tile(col, row, ' ') for row in xrange(width)] for col in xrange(height)]
        self.area, self.fov_map = gen.make_area(self.area, biome, 1)

        biomes = {
            "cave": {
                "fog": lt.Color(20, 10, 15),
                "fog density": 0.4,    # Lower is more dense
                "items": default_cave_items,
                "structures": []
            },
        }

        biome = biomes[biome]
        self.fog = biome["fog"]
        self.fog_density = biome["fog density"]
        self.items = biome["items"](self.area)
        self.structures = biome["structures"]

    def draw(self, offset_col, offset_row, map_width, map_height):
        lt.console_clear(self.con)
        for n_row in xrange(map_width):
            for n_col in xrange(map_height):
                row = n_row + offset_row
                col = n_col + offset_col
                if 0 <= row < len(self.area[0]) and 0 <= col < len(self.area):
                    if lt.map_is_in_fov(self.fov_map, col, row):
                        self.area[col][row].draw(True, self)
                    else:
                        self.area[col][row].draw(False, self)
        for structure in self.structures:
            structure.draw()
        return


"""
Item Placement
"""


def default_cave_items(area):
    items = []

    for n in xrange(25):
        col = random.randint(0, len(area)-1)
        row = random.randint(0, len(area[0])-1)
        print col, row
        if not area[col][row].blocks_movement:
            item = {
                'loc': Location(col, row, '%', lt.light_gray),
                'item': itt.Item(['bone', 'bones'], 0.5)
            }
            items.append(item)
    for n in xrange(40):
        col = random.randint(0, len(area)-1)
        row = random.randint(0, len(area[0])-1)
        if not area[col][row].blocks_movement:
            item = {
                'loc': Location(col, row, 'O', lt.desaturated_amber),
                'item': itt.Item(['large rock', 'large rocks'], 2)
            }
            items.append(item)

    return items
