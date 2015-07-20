"""
Holds data for the body parts and the creation of all creatures (including player).
"""

from src.world import area as world
from random import randint
import libtcodpy as lt

"""
Creatures
"""


class Animal(object):
    def __init__(self, name):
        self.body = Body(name)
        self.loc = None
        self.ai = None


class Player(Animal):
    def __init__(self):
        super(Player, self).__init__(['dragon', 'error'])

        for side in ('left', 'right'):
            for part in ('legarm', 'wing', 'leg'):
                hp = 5
                str = 5
                dex = 5
                self.body.add_limb(part, hp, str, dex, side)

        # Tail
        hp = 5
        str = 5
        dex = 5
        self.body.add_limb("tail", hp, str, dex, '')

        # Head
        hp = 5
        str = 5
        dex = 5
        int = 5
        per = 5
        self.body.add_head(hp, str, dex, int, per)
        self.body.head.holds = True     # Dragons can hold things with their mouths. :>

        # Chest
        hp = 5
        str = 5
        dex = 5
        end = 5
        self.body.add_chest(hp, str, dex, end)



"""
Body Parts
"""


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
        self.name = "error"
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


"""
Creation Functions
"""


def create_player(area):
    player = Player()

    # Place player.
    print "Placing player..."
    flatten = []
    for section in area:
        for tile in section:
            flatten.append(tile)
    flatten.sort(key=lambda x: x.distance, reverse=True)
    starting = flatten[randint(0, 25)]
    player.loc = world.Location(starting.col, starting.row, '@', lt.white)
    return player

"""
Other
"""