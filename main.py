"""
Title: Drake
Author: A. Parish
Version: 0.0.1
Last Updated: 07/07/2015

With a lot of help from Jotaf's tutorial, of course. :)
"""
import random
import textwrap
from collections import OrderedDict, Counter
import src.world.area as world
import src.items as itt
import libtcodpy as lt


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


class Body:
    def __init__(self, name):
        self.name, self.names = name
        self.parts = []
        self.head = None
        self.chest = None

    def add_limb(self, kind, hp, str, dex, loc):
        self.parts.append(Limb(kind, hp, str, dex, loc))

    def add_head(self, hp, str, dex, int, per):
        self.head = Head(hp, str, dex, int, per)
        self.parts.append(self.head)

    def add_chest(self, hp, str, dex, end):
        self.chest = Chest(hp, str, dex, end)
        self.parts.append(self.chest)

    def overall_health(self):
        hp = 0
        for part in self.parts:
            hp += (part.hp / part.max_hp) * 100
        hp /= len(self.parts)
        return hp


class Part(object):
    def __init__(self, hp, str, dex):
        self.hp = hp
        self.max_hp = hp
        self.str = str
        self.dex = dex
        self.name = "you shouldn't see this"
        self.holds = False

    def health(self):
        return (float(self.hp) / self.max_hp) * 100

    def injure(self, amount):
        self.hp -= amount
        return


class Limb(Part):
    def __init__(self, kind, hp, str, dex, loc):
        """
        kind = "leg", "arm", "legarm", "tail", or "wing"
        loc = standard: left/right
        """
        super(Limb, self).__init__(hp, str, dex)
        self.loc = loc
        self.is_leg = False
        self.is_arm = False
        self.is_wing = False

        # Component system stuff?
        if kind == "leg":
            self.is_leg = True
        elif kind == "wing":
            self.is_wing = True
        elif kind == "arm":
            self.is_arm = True
        elif kind == "legarm":
            self.is_arm = True
            self.is_leg = True
            kind = "arm"
        if self.is_arm:
            self.holds = True

        self.name = loc + " " + kind

    # TODO: lots of limb shit


class Head(Part):
    def __init__(self, hp, str, dex, int, per):
        super(Head, self).__init__(hp, str, dex)
        self.int = int
        self.per = per
        self.name = "head"


class Chest(Part):
    def __init__(self, hp, str, dex, end):
        super(Chest, self).__init__(hp, str, dex)
        self.end = end
        self.name = "chest"


class Inventory:
    def __init__(self, owner):
        self.owner = owner
        self.holding_slots = OrderedDict()
        self.equipment_slots = OrderedDict()
        for part in self.owner["body"].parts:
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
        col = self.owner["loc"].col
        row = self.owner["loc"].row
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
            ord('i'): (render_inventory, None),
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
        target_row = player["loc"].row + dx
        target_col = player["loc"].col + dy

        if is_blocked(target_col, target_row):
            message("Bump.")
            return "no turn"
        else:
            player["loc"].move(dx, dy)
            if dx != 0 or dy != 0:
                adjacent = adjacent_items(player["loc"].col, player["loc"].row)
                if len(adjacent) > 0:
                    message(examine_tile_contents(player["loc"].col, player["loc"].row))
            return "took turn"

    def drop(self):
        options = []
        part_list = []
        for key, value in player["inv"].holding_slots.iteritems():
            item_name = 'Nothing'
            if value:
                item_name = value["item"].name.capitalize()
            part_list.append(key)
            text = item_name + '   {' + key + '}'
            options.append(text)
        key = menu('Drop what?', options, 40)
        if key == 'exit':
            return "no turn"
        else:
            choice = part_list[key]
        if player["inv"].holding_slots[choice] is not None:
            item_name = player["inv"].holding_slots[choice]["item"].name
            message("You drop the " + item_name + ".", lt.yellow)
            player["inv"].drop(choice, items)
            return "took turn"
        else:
            message("You're not holding anything with that.", lt.yellow)
            return "no turn"

    def pickup(self):
        indexes = adjacent_items(player["loc"].col, player["loc"].row)
        if len(indexes) == 0:
            message("You don't see anything around you.")
            return "no turn"
        elif len(indexes) > 0:
            n = 0
            if len(indexes) > 1:
                options = [items[x]["item"].name.capitalize() for x in indexes]
                n = menu('Pick what up', options, 40)
            item = items[indexes[n]]
            held = player["inv"].pick_up(item)
            if held != '':
                # Picked it up with an empty hamd/mouth.
                message("You pick up the " + item["item"].name + " with your " + held + ".", lt.yellow)
                items.pop(indexes[n])
                return "took turn"

            else:
                # Hands/mouth are full.
                part_list = []
                options = []
                # Presents a modified version of the self.drop menu.
                for key, value in player["inv"].holding_slots.iteritems():
                    item_name = value["item"].name.capitalize()
                    part_list.append(key)
                    text = item_name + '   {' + key + '}'
                    options.append(text)
                key = menu('You struggle to hold so much. What do you want to drop?', options, MENU_WIDTH)
                if key == 'exit':
                    return "no turn"
                else:
                    choice = part_list[key]
                player["inv"].drop(choice, items)

                # Need to repeat the ["inv"].pick_up() call, because the first must have failed:
                player["inv"].pick_up(item)
                items.pop(indexes[n])
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


def render_inventory():
    w = 50
    h = 40
    divide = 11
    window = lt.console_new(w, h)

    # Lots of shit getting text into the right position.
    # First the labels...
    lt.console_set_default_foreground(window, lt.light_yellow)
    lt.console_print(window, 1, 4, "Left Hand:")
    lt.console_print_ex(window, w-2, 4, lt.BKGND_NONE, lt.RIGHT, "Right Hand:")
    lt.console_print_ex(window, w/2, 4, lt.BKGND_NONE, lt.CENTER, "Mouth:")
    lt.console_print_ex(window, w/2, divide+3, lt.BKGND_NONE, lt.CENTER, "Head:")
    lt.console_print(window, 1, divide+6, "Left Arm:")
    lt.console_print_ex(window, w-2, divide+6, lt.BKGND_NONE, lt.RIGHT, "Right Arm:")
    lt.console_print_ex(window, w/2, divide+8, lt.BKGND_NONE, lt.CENTER, "Chest:")
    lt.console_print(window, 1, divide+10, "Left Wing:")
    lt.console_print_ex(window, w-2, divide+10, lt.BKGND_NONE, lt.RIGHT, "Right Wing:")
    lt.console_print(window, 1, divide+14, "Left Leg:")
    lt.console_print_ex(window, w-2, divide+14, lt.BKGND_NONE, lt.RIGHT, "Right Leg:")
    lt.console_print_ex(window, w/2, divide+16, lt.BKGND_NONE, lt.CENTER, "Tail:")

    # Then the held items.
    lt.console_set_default_foreground(window, lt.white)
    lt.console_print_ex(window, w/2, 1, lt.BKGND_NONE, lt.CENTER, "Held Items")
    lt.console_print_ex(window, w/2, divide, lt.BKGND_NONE, lt.CENTER, "Equipment")
    for part in ["left hand", "right hand", "mouth"]:
        text = "Nothing"
        held_item = player["inv"].holding_slots[part]
        if held_item:
            text = held_item["item"].name.capitalize()
        if part == "left hand":
            lt.console_print(window, 4, 5, text)
        elif part == "right hand":
            lt.console_print_ex(window, w-5, 5, lt.BKGND_NONE, lt.RIGHT, text)
        elif part == "mouth":
            lt.console_print_ex(window, w/2, 5, lt.BKGND_NONE, lt.CENTER, text)

    # Then the equipped items.
    for part in ["head", "chest", " tail", "left arm", "left wing", "left leg", "right arm", "right wing", "right leg"]:
        text = "Nothing"
        equipped_item = player["inv"].equipment_slots[part]
        if equipped_item:
            text = equipped_item["item"].name.capitalize()
        if part == "head":
            lt.console_print_ex(window, w/2, divide+4, lt.BKGND_NONE, lt.CENTER, text)
        elif part == "chest":
            lt.console_print_ex(window, w/2, divide+9, lt.BKGND_NONE, lt.CENTER, text)
        elif part == " tail":
            lt.console_print_ex(window, w/2, divide+17, lt.BKGND_NONE, lt.CENTER, text)
        elif part == "left arm":
            lt.console_print(window, 4, divide+7, text)
        elif part == "left wing":
            lt.console_print(window, 4, divide+11, text)
        elif part == "left leg":
            lt.console_print(window, 4, divide+15, text)
        elif part == "right arm":
            lt.console_print_ex(window, w-5, divide+7, lt.BKGND_NONE, lt.RIGHT, text)
        elif part == "right wing":
            lt.console_print_ex(window, w-5, divide+11, lt.BKGND_NONE, lt.RIGHT, text)
        elif part == "right leg":
            lt.console_print_ex(window, w-5, divide+15, lt.BKGND_NONE, lt.RIGHT, text)

    # And flush.
    lt.console_blit(window, 0, 0, 0, 0, 0, (MAP_WIDTH+2)/4, (MAP_HEIGHT+2)/4, 1, 0.8)
    lt.console_flush()

    # Inventory controls.
    while True:
        key = lt.console_wait_for_keypress(True)
        if key.vk == lt.KEY_ESCAPE:
            lt.console_delete(window)
            render_all()
            return "no turn"


def initialize_player():
    global player, fov_recompute
    fov_recompute = True
    player = dict()
    player["ai"] = PlayerControl()

    # Set up body and parts.
    player["body"] = Body(['dragon', 'dragons'])
    player["body"].add_limb("legarm", 5, 5, 5, 'right')
    player["body"].add_limb("legarm", 5, 5, 5, 'left')
    player["body"].add_limb("wing", 5, 5, 5, 'right')
    player["body"].add_limb("wing", 5, 5, 5, 'left')
    player["body"].add_limb("leg", 5, 5, 5, 'right')
    player["body"].add_limb("leg", 5, 5, 5, 'left')
    player["body"].add_limb("tail", 5, 5, 5, '')
    player["body"].add_head(10, 5, 5, 5, 5)
    player["body"].add_chest(10, 5, 5, 5)
    player["body"].head.holds = True  # Dragons can hold things with their mouths. :>

    player["inv"] = Inventory(player)

    # Place player.
    print "Placing player..."
    flatten = []
    for section in area:
        for tile in section:
            flatten.append(tile)
    flatten.sort(key=lambda x: x.distance, reverse=True)
    starting = random_choice_list(flatten[:25])
    player['loc'] = Mobile(starting.col, starting.row, '@', lt.white)

    return player

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


def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    elif len(options) == 0:
        raise ValueError('Attempted menu with no options.')

    header_height = lt.console_get_height_rect(area_con, 0, 0, width, MAP_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    window = lt.console_new(width, height)
    lt.console_set_default_foreground(window, lt.white)
    lt.console_print_rect_ex(window, 0, 0, width, height, lt.BKGND_NONE, lt.LEFT, header)

    y = header_height
    code = ord('a')
    for option in options:
        text = '(' + chr(code) + ') ' + option
        lt.console_print_ex(window, 0, y, lt.BKGND_NONE, lt.LEFT, text)
        y += 1
        code += 1

    x = MAP_WIDTH - width - 2
    y = MAP_HEIGHT - height - 2
    lt.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    lt.console_flush()

    while True:
        key = lt.console_wait_for_keypress(lt.KEY_PRESSED)
        if key.vk == lt.KEY_ESCAPE:
            return 'exit'
        index = key.c - ord('a')
        if 0 <= index < len(options):
            return index

"""
Map Functions
"""


def is_blocked(col, row):
    return area[col][row].blocks_movement


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
        contents.append(items[content]["item"])
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
        for item in items:
            if item["loc"].row == row and item["loc"].col == col:
                adjacent.append(n)
            n += 1
        return adjacent


"""
Rendering
"""


def render_all():
    offset_row = player["loc"].row - (MAP_WIDTH/2)
    offset_col = player["loc"].col - (MAP_HEIGHT/2)

    global area_con
    lt.map_compute_fov(fov_map, player["loc"].col, player["loc"].row, SIGHT_RADIUS, True, FOV_ALGO)
    area_con, fog = world.render_area(fov_map, offset_col, offset_row, MAP_WIDTH, MAP_HEIGHT)
    for item in items:
        item["loc"].draw()
    player["loc"].draw()
    lt.console_set_key_color(area_con, lt.black)

    # Panel Rendering
    lt.console_clear(panel)
    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 2, 'Overall:')
    text, color = injury_level(player["body"].overall_health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 3, text)

    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 5, 'Chest:')
    text, color = injury_level(player["body"].chest.health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 6, text)

    lt.console_set_default_foreground(panel, lt.white)
    lt.console_print(panel, 1, 8, 'Head:')
    text, color = injury_level(player["body"].head.health())
    lt.console_set_default_foreground(panel, color)
    lt.console_print(panel, 1, 9, text)

    # Fog background behind the map.
    lt.console_set_default_background(frame, fog)
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
    lt.console_blit(area_con, offset_row, offset_col, MAP_WIDTH, MAP_HEIGHT, 0, 1, 1)
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

    global area, area_con, structures, items, fov_map
    # Starting cave
    area, area_con, structures, fov_map = world.new_area("cave", 50, 100)
    items = []

    # FIXME
    for n in xrange(25):
        col = random.randint(0, 99)
        row = random.randint(0, 49)
        if not is_blocked(col, row):
            item = {
                'loc': world.Location(col, row, '%', lt.light_gray),
                'item': itt.Item(['bone', 'bones'], 0.5)
            }
            items.append(item)
    for n in xrange(40):
        col = random.randint(0, 99)
        row = random.randint(0, 49)
        if not is_blocked(col, row):
            item = {
                'loc': world.Location(col, row, 'O', lt.desaturated_amber),
                'item': itt.Item(['large rock', 'large rocks'], 2)
            }
            items.append(item)

    global game_msgs
    game_msgs = []
    message(' ')  # Ensures log is rendered.

    global player
    player = initialize_player()

    global gamestate
    gamestate = "main"

    return True

"""
Game
"""


def main():
    while True:
        render_all()

        player_action = player["ai"].take_turn()
        if player_action == "exit":
            for console in [area_con, frame, panel, log]:
                lt.console_delete(console)
            lt.console_clear(0)
            lt.console_flush()
            return 'exit'


def main_menu():
    while not lt.console_is_window_closed():
        background = lt.image_load('data/gfx/main-menu-silhouette.png')
        lt.image_invert(background)
        lt.image_scale(background, int(SCREEN_WIDTH*2.5), int(SCREEN_WIDTH*2.5))
        lt.image_blit_2x(background, 0, -7, -25)
        lt.console_set_default_foreground(0, lt.white)
        lt.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 7, lt.BKGND_NONE, lt.CENTER, 'Drake')

        # Options
        y = 1
        x = 10
        lt.console_set_default_background(0, lt.black)
        lt.console_print_frame(0, SCREEN_WIDTH/2 - x-1, SCREEN_HEIGHT/2 - y - 1, 22, 10, True, lt.BKGND_MULTIPLY)
        lt.console_set_default_foreground(0, lt.white)
        lt.console_print_frame(0, SCREEN_WIDTH/2 - x-1, SCREEN_HEIGHT/2 - y - 1, 22, 10, False)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y, lt.BKGND_NONE, lt.LEFT, '(N)ew Game')
        if not saved_game:
            lt.console_set_default_foreground(0, lt.gray)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y + 1, lt.BKGND_NONE, lt.LEFT, '(L)oad Game')
        lt.console_set_default_foreground(0, lt.white)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y + 2, lt.BKGND_NONE, lt.LEFT, '(O)ptions')
        lt.console_flush()

        key = lt.console_wait_for_keypress(lt.KEY_PRESSED)
        if key.vk == lt.KEY_ESCAPE:
            break
        elif key.c == ord('n') or key.c == ord('N'):
            new_game()
            main()

if ro:
    lt.console_set_custom_font(FONT, lt.FONT_TYPE_GRAYSCALE | lt.FONT_LAYOUT_ASCII_INROW)
else:
    lt.console_set_custom_font(FONT, lt.FONT_TYPE_GRAYSCALE | lt.FONT_LAYOUT_TCOD)
lt.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Drake v0.0', False)
saved_game = False

main_menu()