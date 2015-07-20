"""
Deals with the procedural generation of indiivudal areas.
"""
"""
"""

import libtcodpy as lt
import random

"""
Parameters for stand-alone generation
"""

viz = False
"""

WIDTH = 100
HEIGHT = 100
biome = "cave"
EXITS = 0

WORLD_SEED = 127
"""
"""
Setup
"""


def make_area(area, biome, exits, seed):
    height = len(area)
    width = len(area[0])
    terrain = False
    exitlist = []

    """
        p_blocked = what percent must be blocked
        p_unblocked = what percent must be unblocked
        nudge = higher = more blocked
        steps = steps for cellular automata
        border = require border around map
        connect = require all areas to be connected
    """

    while not terrain:
        ######################## Caves
        if biome == "cave":
            terrain = area_cell_create(
                width, height,
                p_blocked=.45,
                p_unblocked=.4,
                nudge=0.07,
                steps=10,
                border=True,
                connect=True,
                seed=seed
            )

        ######################## Forests
        elif biome == "sparse forest":
            terrain = area_cell_create(
                width, height,
                p_blocked=.03,
                p_unblocked=.7,
                nudge=-0.04,
                steps=1,
                border=False,
                connect=False,
                seed=seed
            )

    if viz:
        return

    for col in xrange(height):
        for row in xrange(width):
            if terrain[col][row] > 1:
                area[col][row].distance = terrain[col][row]

            ################################# Caves
            if biome == "cave":
                if terrain[col][row] > 1 or terrain[col][row] == 0:
                    area[col][row].char = random_choice([' ']*30 + ['.']*3 + ['o'])
                    area[col][row].f_color = lt.darkest_sepia
                    n = random.randint(30, 35)
                    area[col][row].b_color = lt.Color(n + 10, n, n)
                    area[col][row].blocks_light = False
                    area[col][row].blocks_movement = False
                elif terrain[col][row] == 1:
                    area[col][row].char = '#'
                    area[col][row].f_color = lt.black
                    area[col][row].b_color = lt.Color(30, 25, 25)
                    area[col][row].blocks_light = True
                    area[col][row].blocks_movement = True
                elif terrain[col][row] == -1:
                    area[col][row].char = '>'
                    area[col][row].f_color = lt.black
                    area[col][row].b_color = lt.Color(255, 255, 230)
                    area[col][row].blocks_light = False
                    area[col][row].blocks_movement = True
                    exitlist.append((col, row))

            ################################# Forests
            if biome == "sparse forest":
                if terrain[col][row] != 1:
                    area[col][row].char = random_choice([' ']*30 + [',']*8 + ['v'])
                    area[col][row].f_color = lt.dark_green
                    area[col][row].b_color = lt.Color(random.randint(0, 10), random.randint(130, 135), 20)
                    area[col][row].blocks_light = False
                    area[col][row].blocks_movement = False
                elif terrain[col][row] == 1:
                    area[col][row].char = random_choice(['Y']*4 + ['|']*3)
                    area[col][row].f_color = lt.black
                    area[col][row].b_color = lt.darkest_green
                    area[col][row].blocks_light = True
                    area[col][row].blocks_movement = True

    # Create FOV map.
    fov_map = lt.map_new(height, width)
    for col in xrange(height):
        for row in xrange(width):
            lt.map_set_properties(fov_map, col, row, not area[col][row].blocks_light, True)

    if biome == "cave" and exits > 0:
        for exit in exitlist:
            col, row = exit
            if col == height - 1:
                lt.map_compute_fov(fov_map, col, row, 50, True, 0)
                for col in xrange(height):
                    for row in xrange(width):
                        if lt.map_is_in_fov(fov_map, col, row):
                            if area[col][row].blocks_light:
                                distance = 0.2 / (terrain[col][row]*2.8)
                            else:
                                distance = 3. / (terrain[col][row]*2.8)
                            if distance > 0:
                                area[col][row].b_color = lt.color_lerp(area[col][row].b_color, lt.lightest_yellow, distance)

    return area, fov_map


def random_choice(choices):
    return choices[random.randint(0, len(choices) - 1)]



"""
Cellular Automata Generation
"""


def area_cell_create(width, height, p_blocked, p_unblocked, nudge, steps, border=True, exits=0, connect=True, seed=lt.random_get_instance()):
    """
    :param width:
    :param height:
    :param p_blocked: - At least what percent of a valid area must be unblocked spaces.
    :param p_unblocked: - At least what percent of a valid area must be blocked spaces.
    :param nudge: - Higher number means more blocked space.
    :param steps: - How many steps to run the automata.
    :param border: - Requires a solid border?
    :param exits: - If there's a solid border, how many exits should there be?
    :return:
    """
    print "---"
    area = [[True for row in xrange(width)] for col in xrange(height)]
    # Create noise
    print "Generating noise..."
    area_noise = lt.noise_new(2, random=seed)
    for col in xrange(height):
        for row in xrange(width):
            if border:
                if row < 3 or row > width - 3:
                    area[col][row] = 1
                elif col < 3 or col > height - 3:
                    area[col][row] = 1
                else:
                    coords = (col, row)
                    n = lt.noise_get(area_noise, coords)
                    area[col][row] = int(round(abs(n) + nudge, 0))
            else:
                coords = (col, row)
                n = lt.noise_get(area_noise, coords)
                area[col][row] = int(round(abs(n) + nudge, 0))
    visualize(area)

    # Add in exits.
    print "Adding exits..."
    if exits > 0:
        exitcoords = []
        for direction in xrange(exits):
            row_size = random.randint(4, 10)
            col_size = random.randint(4, 10)
            if direction == 0:
                row_loc = random.randint(width/2 - width/4, width/2 + width/4)
                col_loc = height - col_size
                for col in xrange(col_size):
                    for row in xrange(row_size):
                        area[col_loc+col][row_loc+row] = 0
                for row in xrange(row_size):
                    coords = (height - 2, row_loc + row)
                    area[coords[0] + 1][coords[1]] = -1
                    exitcoords.append(coords)


    visualize(area)

    # Begin cellular automata
    print "Running automata..."
    for i in xrange(steps):
        next_step = area
        for col in xrange(height):
            for row in xrange(width):
                neighbors = count_neighbors(col, row, area)

                # Check births and survivals.
                # Current rules are: B5678 / S45678. May want to add the ability to affect that too.
                if area[col][row] == 1 and neighbors < 4:
                    next_step[col][row] = 0
                elif area[col][row] == 0 and neighbors > 4:
                    next_step[col][row] = 1
        area = next_step
        visualize(area)

    # Mark as ground only those ground tiles which can be reached from an arbitrary point near the center OR an exit.
    print "Counting reach..."
    while True:
        if exits == 0:
            row = random.randint(width/2 - 10, width/2 + 10)
            col = random.randint(height/2 - 10, height/2 + 10)
        elif exits > 0:
             col, row = exitcoords.pop()
        if area[col][row] == 0:
            reachable(col, row, area, 1)
            break
    # Replace 0's (unreachable sections) with 1 (blocked). and 2's (reachable sections)
    # with 0 (unblocked), while counting how many there are.
    unblocked_n = 0.
    blocked_n = 0.
    for col in xrange(height):
        for row in xrange(width):
            if area[col][row] == 1 or (area[col][row] == 0 and connect):
                area[col][row] = 1
                blocked_n += 1
            elif area[col][row] > 1 or (area[col][row] == 0 and not connect):
                if col == 0 or col == height - 1 or row == 0 or row == width - 1:
                    area[col][row] = -1
                unblocked_n += 1

    # Ensure the map fits our parameters.
    print "Testing parameters..."
    visualize(area)
    if unblocked_n <= width * height * p_unblocked:
        print "Not enough unblocked: ", unblocked_n, "<", width * height * p_unblocked
        if blocked_n <= width * height * p_blocked:
            print "Not enough blocked.", blocked_n, "<", width * height * p_blocked
        return False
    print "Area generated."
    return area


def count_neighbors(col, row, area):
    neighbor_count = 0
    for col_c in xrange(col-1, col+2):
        if 0 <= col_c < len(area):
            for row_c in xrange(row-1, row+2):
                if 0 <= row_c < len(area[0]):
                    neighbor_count += area[col_c][row_c]
    return neighbor_count


def reachable(col, row, area, n):
    # Basic flood fill algorithm.
    stack = {(col, row, n)}
    while stack:
        (col, row, n) = stack.pop()
        n += 1
        if area[col][row] == 0:
            area[col][row] = n
            if col > 0:
                stack.add((col - 1, row, n))
            if col < len(area) - 1:
                stack.add((col + 1, row, n))
            if row > 0:
                stack.add((col, row - 1, n))
            if row < len(area[0]) - 1:
                stack.add((col, row + 1, n))
    return area


#########################################################################################


def visualize(area):
    if viz:
        lt.console_clear(con)
        y = 0
        for row in area:
            x = 0
            for tile in row:
                if tile == 1:
                    lt.console_set_char_background(con, x, y, lt.white)
                elif tile == -1:
                    lt.console_set_char_background(con, x, y, lt.green)
                elif tile > 1:
                    lt.console_set_char_background(con, x, y, lt.Color(tile, tile, 225))
                x += 1
            y += 1
        lt.console_blit(con, 0, 0, 0, 0, 0, 0, 0)
        lt.console_flush()

if viz:
    lt.console_set_custom_font('data/fonts/terminal8x8_gs_ro.png', lt.FONT_TYPE_GRAYSCALE | lt.FONT_LAYOUT_ASCII_INROW)
    lt.console_init_root(WIDTH, HEIGHT, 'Visualizer', False)
    con = lt.console_new(WIDTH, HEIGHT)

    area = [[' ' for row in xrange(WIDTH)] for col in xrange(HEIGHT)]
    while True:
        key = lt.console_wait_for_keypress(False)
        if key.vk == lt.KEY_ESCAPE:
            quit()
        else:
            make_area(area, biome, exits, WORLD_SEED)