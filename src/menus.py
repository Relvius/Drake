import libtcodpy as lt


def render_inventory(args):
    w = 50
    h = 40
    divide = 11
    window = lt.console_new(w, h)
    player, con = args

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
        held_item = player.inv.holding_slots[part]
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
        equipped_item = player.inv.equipment_slots[part]
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
    width = lt.console_get_width(con)
    height = lt.console_get_height(con)
    lt.console_blit(window, 0, 0, 0, 0, 0, (width+2)/4, (height+2)/4, 1, 0.8)
    lt.console_flush()

    # Inventory controls.
    while True:
        key = lt.console_wait_for_keypress(True)
        if key.vk == lt.KEY_ESCAPE:
            lt.console_delete(window)
            return "no turn"


def menu(header, options, width, con, MAP_WIDTH, MAP_HEIGHT):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    elif len(options) == 0:
        raise ValueError('Attempted menu with no options.')

    header_height = lt.console_get_height_rect(con, 0, 0, width, MAP_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height

    window = lt.console_new(width, height)

    current_choice = 0

    while True:
        lt.console_clear(window)
        lt.console_set_default_foreground(window, lt.white)
        lt.console_print_rect_ex(window, 0, 0, width, height, lt.BKGND_NONE, lt.LEFT, header)

        i = 0
        y = header_height
        code = ord('a')
        for option in options:
            text = '(' + chr(code) + ') ' + option
            if i == current_choice:
                lt.console_set_default_foreground(window, lt.black)
                lt.console_set_default_background(window, lt.white)
                lt.console_print_ex(window, 0, y, lt.BKGND_SET, lt.LEFT, text)
            else:
                lt.console_set_default_foreground(window, lt.white)
                lt.console_set_default_background(window, lt.black)
                lt.console_print_ex(window, 0, y, lt.BKGND_NONE, lt.LEFT, text)
            y += 1
            code += 1
            i += 1

        x = MAP_WIDTH - width - 2
        y = MAP_HEIGHT - height - 2
        lt.console_blit(window, 0, 0, width, height, 0, x, y, 1)
        lt.console_flush()

        print current_choice

        while True:
            key = lt.console_check_for_keypress(lt.KEY_PRESSED)
            if key.vk == lt.KEY_ESCAPE:
                return 'exit'
            elif key.vk == lt.KEY_DOWN or key.vk == lt.KEY_KP2:
                current_choice += 1 if current_choice < len(options)-1 else 0
                break
            elif key.vk == lt.KEY_UP or key.vk == lt.KEY_KP2:
                current_choice -= 1 if current_choice > 0 else 0
                break

            if key.vk == lt.KEY_ENTER:
                return current_choice

            index = key.c - ord('a')
            if 0 <= index < len(options):
                return index


def main_menu(SCREEN_WIDTH, SCREEN_HEIGHT, saved_game):
    current_choice = -1
    options = ['new game', 'load game', 'options']
    while True:
        y = 1
        x = 10
        lt.console_set_default_background(0, lt.black)
        lt.console_print_frame(0, SCREEN_WIDTH/2 - x-1, SCREEN_HEIGHT/2 - y - 1, 22, 10, True, lt.BKGND_SET)
        lt.console_set_default_foreground(0, lt.white)
        lt.console_print_frame(0, SCREEN_WIDTH/2 - x-1, SCREEN_HEIGHT/2 - y - 1, 22, 10, False)

        if current_choice == 0:
            lt.console_set_default_background(0, lt.white)
            lt.console_set_default_foreground(0, lt.black)
        else:
            lt.console_set_default_background(0, lt.black)
            lt.console_set_default_foreground(0, lt.white)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y, lt.BKGND_SET, lt.LEFT, '(N)ew Game')

        if not saved_game:
            lt.console_set_default_foreground(0, lt.gray)
            lt.console_set_default_background(0, lt.black)
        elif current_choice == 1:
            lt.console_set_default_background(0, lt.white)
            lt.console_set_default_foreground(0, lt.black)
        elif saved_game:
            lt.console_set_default_background(0, lt.black)
            lt.console_set_default_foreground(0, lt.white)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y + 1, lt.BKGND_SET, lt.LEFT, '(L)oad Game')

        if current_choice == 2:
            lt.console_set_default_background(0, lt.white)
            lt.console_set_default_foreground(0, lt.black)
        else:
            lt.console_set_default_background(0, lt.black)
            lt.console_set_default_foreground(0, lt.white)
        lt.console_print_ex(0, SCREEN_WIDTH/2 - x, SCREEN_HEIGHT/2 + y + 2, lt.BKGND_SET, lt.LEFT, '(O)ptions')

        lt.console_flush()

        while True:
            key = lt.console_check_for_keypress(lt.KEY_PRESSED)
            if key.vk == lt.KEY_ESCAPE:
                return 'exit'
            elif key.vk == lt.KEY_DOWN or key.vk == lt.KEY_KP2:
                current_choice += 1 if current_choice < 2 else 0
                if current_choice == 1 and not saved_game:
                    current_choice = 2
                break
            elif key.vk == lt.KEY_UP or key.vk == lt.KEY_KP2:
                current_choice -= 1 if current_choice > 0 else 0
                if current_choice == 1 and not saved_game:
                    current_choice = 0
                break
            if key.vk == lt.KEY_ENTER:
                return options[current_choice]

            if key.c == ord('n') or key.c == ord('N'):
                return 'new game'