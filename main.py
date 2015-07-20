"""
Working Title: Drake
Author: A. Parish

With a lot of help from Jotaf's tutorial, of course. :)
"""

import random
import textwrap
from collections import OrderedDict, Counter
import libtcodpy as lt

import src.creatures as ccreate
import src.menus as menus
import src.world.area as world

"""
Global Parameters
"""
SCREEN_HEIGHT = 70
SCREEN_WIDTH = 95
LOG_HEIGHT = 10
PANEL_WIDTH = 15
MAP_HEIGHT = SCREEN_HEIGHT - LOG_HEIGHT
MAP_WIDTH = SCREEN_WIDTH - PANEL_WIDTH
BAR_WIDTH = 20
MSG_WIDTH = MAP_WIDTH - 5

MENU_WIDTH = 40

FONT = 'data/fonts/lucida12x12_gs_tc.png'
ro = False

FOV_ALGO = 1
SIGHT_RADIUS = 30

"""
Entities
"""


class Mobile(world.Location):
    def move(self, dx, dy):
        global fov_recompute
        if not is_blocked(self.col + dy, self.row + dx):
            self.row += dx
            self.col += dy
            fov_recompute = True

    def move_towards(self, target_x, target_y):
        dx = target_x - self.row
        dy = target_y - self.col
        dist = (dx ** 2 + dy ** 2) ** 0.5

        dx = int(round(dx / dist))
        dy = int(round(dy / dist))
        self.move(dx, dy)


class Inventory:
    def __init__(self, owner):
        self.owner = owner
        self.holding_slots = OrderedDict()
        self.equipment_slots = OrderedDict()
        for part in self.owner.body.parts:
            self.equipment_slots[part.name] = None
            if part.holds:
                if part.name == "left arm":
                    part_name = "left hand"
                elif part.name == "right arm":
                    part_name = "right hand"
                elif part.name == "head":
                    part_name = "mouth"
                else:
                    part_name = part.name
                self.holding_slots[part_name] = None

    def pick_up(self, item):
        to_hold = ''
        for part in self.holding_slots.keys():
            if not self.holding_slots[part]:
                to_hold = part
                break
        if to_hold != '':
            self.holding_slots[to_hold] = item
        return to_hold

    def drop(self, part, items):
        col = self.owner.loc.col
        row = self.owner.loc.row
        self.holding_slots[part]["loc"].col = col
        self.holding_slots[part]["loc"].row = row
        items.append(self.holding_slots[part])
        self.holding_slots[part] = None


"""
Player
"""


class PlayerControl:
    def take_turn(self):
        action = None
        control_map = {
            lt.KEY_ESCAPE: (self.leave_game, None),
            # Movement Keys
            lt.KEY_KP5: (self.move, (0, 0)),
            lt.KEY_KP7: (self.move, (-1, -1)),
            lt.KEY_KP8: (self.move, (0, -1)),
            lt.KEY_KP9: (self.move, (1, -1)),
            lt.KEY_KP4: (self.move, (-1, 0)),
            lt.KEY_KP6: (self.move, (1, 0)),
            lt.KEY_KP1: (self.move, (-1, 1)),
            lt.KEY_KP2: (self.move, (0, 1)),
            lt.KEY_KP3: (self.move, (1, 1)),

            # Item Keys
            ord('i'): (menus.render_inventory, (player, area.con)),
            ord('g'): (self.pickup, None),
            ord('d'): (self.drop, None)
        }

        while True:
            key = lt.console_check_for_keypress(lt.KEY_PRESSED)
            handler, param = (None, None)
            if key.vk in control_map.keys():
                handler, param = control_map[key.vk]
            elif key.c in control_map.keys():
                handler, param = control_map[key.c]
            if param:
                action = handler(param)
            elif handler:
                action = handler()
            if action:
                return action

    def move(self, coords):
        dx, dy = coords
        target_row = player.loc.row + dx
        target_col = player.loc.col + dy

        if is_blocked(target_col, target_row):
            message("Bump.")
            return "no turn"
        else:
            player.loc.move(dx, dy)
            if dx != 0 or dy != 0:
                adjacent = adjacent_items(player.loc.col, player.loc.row)
                if len(adjacent) > 0:
                    message(examine_tile_contents(player.loc.col, player.loc.row))
            return "took turn"

    def drop(self):
        options = []
        part_list = []
        for key, value in player.inv.holding_slots.iteritems():
            item_name = 'Nothing'
            if value:
                item_name = value["item"].name.capitalize()
            part_list.append(key)
            text = item_name + '   {' + key + '}'
            options.append(text)
        key = menus.menu('Drop what?', options, 40, area.con, MAP_WIDTH, MAP_HEIGHT)
        if key == 'exit':
            return "no turn"
        else:
            choice = part_list[key]
        if player.inv.holding_slots[choice] is not None:
            item_name = player.inv.holding_slots[choice]["item"].name
            message("You drop the " + item_name + ".", lt.yellow)
            player.inv.drop(choice, area.items)
            return "took turn"
        else:
            message("You're not holding anything with that.", lt.yellow)
            return "no turn"

    def pickup(self):
        indexes = adjacent_items(player.loc.col, player.loc.row)
        if len(indexes) == 0:
            message("You don't see anything around you.")
            return "no turn"
        elif len(indexes) > 0:
            n = 0
            if len(indexes) > 1:
                options = [area.items[x]["item"].name.capitalize() for x in indexes]
                n = menus.menu('Pick what up?', options, 40, area.con, MAP_WIDTH, MAP_HEIGHT)
            if n == "exit":
                return "no turn"
            item = area.items[indexes[n]]
            held = player.inv.pick_up(item)
            if held != '':
                # Picked it up with an empty hamd/mouth.
                message("You pick up the " + item["item"].name + " with your " + held + ".", lt.yellow)
                area.items.pop(indexes[n])
                return "took turn"

            else:
                # Hands/mouth are full.
                part_list = []
                options = []
                # Presents a modified version of the self.drop menu.
                for key, value in player.inv.holding_slots.iteritems():
                    item_name = value["item"].name.capitalize()
                    part_list.append(key)
                    text = item_name + '   {' + key + '}'
                    options.append(text)
                key = menus.menu("You can't grab anything else! What do you want to drop?", options, MENU_WIDTH, area.con, MAP_WIDTH, MAP_HEIGHT)
                if key == 'exit':
                    return "no turn"
                else:
                    choice = part_list[key]
                player.inv.drop(choice, area.items)

                # Need to repeat the ["inv"].pick_up() call, because the first must have failed:
                player.inv.pick_up(item)
                area.items.pop(indexes[n])
                message("You drop the " + item["item"].name + " and pick up the " + item["item"].name, lt.yellow)

                return "took turn"

    def leave_game(self):
        window = lt.console_new(30, 10)
        lt.console_set_default_foreground(window, lt.white)
        lt.console_set_default_background(window, lt.black)
        lt.console_print_rect_ex(window, 15, 3, 20, 10, lt.BKGND_NONE, lt.CENTER, 'Do you really want to quit?\nY/N')
        lt.console_blit(window, 0, 0, 0, 0, 0, MAP_WIDTH/2 - 15, MAP_HEIGHT/2 - 5, 1.0, 0.8)
        lt.console_flush()

        while True:
            key = lt.console_wait_for_keypress(True)
            if key.c == ord('y') or key.c == ord('Y'):
                return "exit"
            elif key.c != 27:
                return "no turn"


"""
General Functions
"""


def random_choice_list(choices):
    return choices[random.randint(0, len(choices) - 1)]


def injury_level(hp):
    levels = [("Perfect", lt.white), ("Fine", lt.green), ("Decent", lt.dark_green), ("Injured", lt.yellow),
              ("Wounded", lt.orange), ("Critical", lt.dark_red), ("Dead", lt.gray)]
    if hp >= 100:
        return levels[0]
    elif 100 > hp > 79:
        return levels[1]
    elif 80 > hp > 59:
        return levels[2]
    elif 60 > hp > 39:
        return levels[3]
    elif 40 > hp > 19:
        return levels[4]
    elif 20 > hp > 0:
        return levels[5]
    elif 0 >= hp:
        return levels[6]


"""
Map Functions
"""


def is_blocked(col, row):
    return area.area[col][row].blocks_movement


def is_clear_area(col, row, col_size, row_size):
    for col_offset in xrange(col_size):
        for row_offset in xrange(row_size):
            if is_blocked(col + col_offset, row + row_offset):
                return False
    return True


def examine_tile_contents(col, row):
    # Returns the text like "There is an X here." and "There is an a and a b here.")
    contents = []
    text = "There is something wrong with the items on the ground here."
    for content in adjacent_items(col, row):
        contents.append(area.items[content]["item"])
    if len(contents) == 1:
        if contents[0].name[0] in ('a', 'e', 'i', 'o', 'u'):
            item_text = 'an ' + contents[0].name
        else:
            item_text = 'a ' + contents[0].name
        text = "There is " + item_text + " here."   # e.g. 'There is a deer skull here.'

    elif len(contents) > 1:
        plurals = Counter()
        items_text = []
        for item in contents:
            plurals[item.name] += 1
        for item in contents:
            if plurals[item.name] > 1:
                items_text.append(str(plurals[item.name]) + ' ' + item.names)
                # TODO: convert numbers < 10 to longer strings? e.g. 'two' not '2'
            else:
                if item.name[0] in ('a', 'e', 'i', 'o', 'u'):
                    items_text.append('an ' + item.name)
                else:
                    items_text.append('a ' + item.name)
        items_text = list(set(items_text))
        if len(items_text) == 1:
            text = 'There are ' + items_text[0] + ' here.'      # e.g. 'There are two bones here.'
        elif len(items_text) == 2:
            if items_text[0][0] == 'a':
                text = "There is " + items_text[0] + ' and ' + items_text[1] + ' here.'
            else:
                text = "There are " + items_text[0] + ' and ' + items_text[1] + ' here.'
            # e.g. 'There are two legs and a head here.'
        elif len(items_text) > 2:
            last_item = 'and ' + items_text.pop() + ' here.'
            if items_text[0][0] == 'a':
                text = 'There is '
            else:
                text = 'There are '
            for item_text in items_text:
                text = text + item_text + ', '
            text += last_item
            # e.g. 'There is a bug, 5 bones, and a rock of iron ore here.'
    return text


def adjacent_items(col, row):
        # returns a list of ints, referring to the index(es) of global list item(s) that share the same location
        adjacent = []
        n = 0       # Counts the index
        for item in area.items:
            if item["loc"].row == row and item["loc"].col == col:
                adjacent.append(n)
            n += 1
        return adjacent


"""
Rendering
"""


def render_all():
    offset_row = player.loc.row - (MAP_WIDTH/2)
    offset_col = player.loc.col - (MAP_HEIGHT/2)

    lt.map_compute_fov(area.fov_map, player.loc.col, player.loc.row, SIGHT_RADIUS, True, FOV_ALGO)
    area.draw(offset_col, offset_row, MAP_WIDTH, MAP_HEIGHT)
    for item in area.items:
        item["loc"].draw(area)
    player.loc.draw(area)
    lt.console_set_key_color(area.con, lt.black)

    # Panel Rendering
    lt.console_clear(panel)
    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 2, 'Overall:')
    text, color = injury_level(player.body.overall_health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 3, text)

    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 5, 'Chest:')
    text, color = injury_level(player.body.chest.health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 6, text)

    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 8, 'Head:')
    text, color = injury_level(player.body.head.health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 9, text)

    # Fog background behind the map.
    lt.console_set_default_background(frame, area.fog)
    lt.console_rect(frame, 1, 1, MAP_WIDTH, MAP_HEIGHT, True, lt.BKGND_SET)
    # A frame around the map
    lt.console_set_default_foreground(frame, lt.desaturated_amber)
    lt.console_set_default_background(frame, lt.Color(70, 60, 0))
    for n in xrange(MAP_WIDTH + 2):
        lt.console_put_char(frame, n, 0, "+", lt.BKGND_SET)
        lt.console_put_char(frame, n, MAP_HEIGHT + 1, "+", lt.BKGND_SET)
        lt.console_put_char(frame, 0, n, "+", lt.BKGND_SET)
        lt.console_put_char(frame, MAP_WIDTH + 1, n, "+", lt.BKGND_SET)

    # Blit all
    lt.console_blit(frame, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    lt.console_blit(panel, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, MAP_WIDTH + 2, 1)
    lt.console_blit(area.con, offset_row, offset_col, MAP_WIDTH, MAP_HEIGHT, 0, 1, 1)
    lt.console_flush()


def message(new_msg, color=lt.white):
    new_msg_lines = textwrap.wrap(str(new_msg), MSG_WIDTH)

    for line in new_msg_lines:
        if len(game_msgs) == LOG_HEIGHT - 4:
            del game_msgs[0]
        game_msgs.append((line, color))

    # Render message log.
    # A frame around the log
    lt.console_clear(log)
    lt.console_set_default_foreground(log, lt.lighter_grey)
    lt.console_print_frame(log, 0, 0, MAP_WIDTH, LOG_HEIGHT-2, False)
    # Message log rendering
    col = 1
    for (line, color) in game_msgs:
        lt.console_set_default_foreground(log, color)
        lt.console_print_ex(log, 3, col, lt.BKGND_NONE, lt.LEFT, line)
        col += 1

    lt.console_blit(log, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, MAP_HEIGHT + 2)
    lt.console_flush()



"""
Initializing
"""


def new_game():
    # Initialize consoles
    lt.console_clear(0)
    lt.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, lt.BKGND_NONE, lt.CENTER, 'Loading...')
    lt.console_flush()
    global panel, log, frame
    panel = lt.console_new(PANEL_WIDTH, SCREEN_HEIGHT)
    log = lt.console_new(SCREEN_WIDTH - PANEL_WIDTH + 2, LOG_HEIGHT)
    frame = lt.console_new(MAP_WIDTH + 2, MAP_HEIGHT + 2)

    # Starting cave
    global area
    area = world.Area("cave", 50, 100)

    global game_msgs
    game_msgs = []
    message(' ')  # Ensures log is rendered.

    # Create player entity
    global player
    player = ccreate.create_player(area.area)
    player.loc = Mobile(player.loc.col, player.loc.row, player.loc.char, player.loc.f_color)
    player.ai = PlayerControl()
    player.inv = Inventory(player)

    global gamestate
    gamestate = "main"

    return True

"""
Game
"""


def main():
    while True:
        render_all()

        player_action = player.ai.take_turn()
        if player_action == "exit":
            for console in [area.con, frame, panel, log]:
                lt.console_delete(console)
            lt.console_clear(0)
            lt.console_flush()
            return 'exit'


def main_menu():
    background = lt.image_load('data/gfx/main-menu-silhouette.png')
    lt.image_invert(background)
    lt.image_scale(background, int(SCREEN_WIDTH*2.5), int(SCREEN_WIDTH*2.5))
    lt.image_blit_2x(background, 0, -7, -25)
    lt.console_set_default_foreground(0, lt.white)
    lt.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 7, lt.BKGND_NONE, lt.CENTER, 'Drake')

    action = menus.main_menu(SCREEN_WIDTH, SCREEN_HEIGHT, saved_game)
    if action == 'new game':
        new_game()
        main()

if ro:
    lt.console_set_custom_font(FONT, lt.FONT_TYPE_GRAYSCALE | lt.FONT_LAYOUT_ASCII_INROW)
else:
    lt.console_set_custom_font(FONT, lt.FONT_TYPE_GRAYSCALE | lt.FONT_LAYOUT_TCOD)
lt.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Drake v0.0', False)
saved_game = False

main_menu()
