#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
from dataclasses import dataclass, asdict
import logging
from pprint import pprint as pretty
from itertools import combinations

verbose = False
#verbose = True

class ZNAK:
    _NONE = -1
    OVEN = 0
    TELEC = 1
    BLIZNECY = 2
    RAK = 3
    LEV = 4
    DEVA = 5
    VESY = 6
    SCORPION = 7
    STRELEC = 8
    KOZEROG = 9
    VODOLEY = 10
    RYBY = 11


ZNAK_ALL = [k for k in ZNAK.__dict__.keys() if not k.startswith('_')]


class PLANET:
    _NONE = 0
    SOL = 1
    LUNA = 2
    MERCURY = 3
    VENERA = 4
    MARS = 5
    JUPITER = 6
    SATURN = 7
    URAN = 8
    NEPTUN = 9
    PLUTON = 10

    HIRON = 11
    SELENA = 12
    LILIT = 13

    # Лунные узлы (восходящий/нисходящий)
    KARM_NISHOD = 14
    KARM_VOSHOD = 15

    PROZERPINA = 16
    VERTEX = 17
    PARS_FORTUNY = 18

    _HOUSE = 21  # 21-32 reserved for house cuspids

    # Add flag to base planet to get retro-planet
    _RETRO = 1024

    MERCURY_RETRO = MERCURY + _RETRO
    VENERA_RETRO = VENERA + _RETRO
    MARS_RETRO = MARS + _RETRO
    JUPITER_RETRO = JUPITER + _RETRO
    SATURN_RETRO = SATURN + _RETRO
    URAN_RETRO = URAN + _RETRO
    NEPTUN_RETRO = NEPTUN + _RETRO
    PLUTON_RETRO = PLUTON + _RETRO

    HIRON_RETRO = HIRON + _RETRO

    # Add flag to house cuspids (to discriminate them from planets)
    _HOUSE_FLAG = 128
    _HOUSE_BASE = _HOUSE_FLAG + _HOUSE - 1

    _FIRST = 1 + _HOUSE_BASE
    SECOND = 2 + _HOUSE_BASE
    THIRD = 3 + _HOUSE_BASE
    _FOURTH = 4 + _HOUSE_BASE
    FIFTH = 5 + _HOUSE_BASE
    SIXTH = 6 + _HOUSE_BASE
    _SEVENTH = 7 + _HOUSE_BASE
    EIGHTH = 8 + _HOUSE_BASE
    NINTH = 9 + _HOUSE_BASE
    _TENTH = 10 + _HOUSE_BASE
    ELEVENTH = 11 + _HOUSE_BASE
    TWELVETH = 12 + _HOUSE_BASE

    _HOUSE_FIRST = _FIRST
    _HOUSE_LAST = TWELVETH

    ASC = _FIRST
    MC = _TENTH
    DSC = _SEVENTH
    IC = _FOURTH

    _KUSPIDS = [ASC, SECOND, THIRD, IC, FIFTH, SIXTH, DSC, EIGHTH, NINTH, MC, ELEVENTH, TWELVETH]


PLANET_ALL = [k for k in PLANET.__dict__.keys() if not k.startswith('_')]


class ASPECT:
    CON = 0
    POLU_SEXT = 30
    SEXT = 60
    QUAD = 90
    TRIN = 120
    KVINK = 150
    OPP = 180

    _MINORS = [POLU_SEXT, KVINK]

ASPECT_ALL = [k for k in ASPECT.__dict__.keys() if not k.startswith('_')]

MINOR_ASPECT_ORBIS = 3.0
LESSER_KUSPID_ORBIS = 2.0

ZNAK_ARC = 30.0

HALF_ARC = 180.0
FULL_ARC = 360.0

ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

def toRoman(num):
    try:
        return ROMANS[num-1]
    except:
        return str(num)



def absGradus(znak, gradus):
    return znak * ZNAK_ARC + gradus


def orb(abs_gradus1, abs_gradus2):
    diff = abs(abs_gradus1 - abs_gradus2)
    if diff > HALF_ARC:
        diff = FULL_ARC - diff
    return diff


def orbz(znak1, gradus1, znak2, gradus2):
    return orb(absGradus(znak1, gradus1), absGradus(znak2, gradus2))



class Planet(object):
    def __init__(self, planet=PLANET._NONE, znak=ZNAK._NONE, gradus=0.0):
        self.planet = planet
        self.znak = znak
        self.gradus = gradus
        self.abs_gradus = absGradus(znak, gradus)

        # house size (for 1/3 calc)
        self.size = 0.0

        # in which house, and which 1/3 of the house planet dwells
        self.house = None
        self.third = None

    def orb(self, planet2):
        return orbz(self.znak, self.gradus, planet2.znak, planet2.gradus)

    def __str__(self):
        s = "Planet(%s, %s, %0.3f, abs=%0.3f" % (
            Config.PLANET_2_NAME.get(self.planet), Config.ZNAK_2_NAME.get(self.znak), self.gradus,
            absGradus(self.znak, self.gradus))
        if self.house is not None:
            s += ', %s дом' % toRoman(self.house - PLANET._HOUSE_BASE)
            #s += ' [%s/3]' % self.third
        elif self.size:
            s += ', size=%0.2f' % (self.size)
        return s + ')'

    def name(self):
        return Config.PLANET_2_NAME.get(self.planet)

    # get base planet sign, without retrograde component
    def get_non_retro(self):
        p = self.planet
        return p if (p & PLANET._RETRO) == 0 else (p ^ PLANET._RETRO)


@dataclass
class AliasConfig:
    ALIASES_ZNAK: dict
    ALIASES_PLANET: dict
    ALIASES_ASPECT: dict

@dataclass
class VronskyTableConfig:
    MAJOR_ASPECT_ORBIS: dict


class Config:
    NAME_2_PLANET = {}  # {"Солнце": PLANET.SOL(int)}
    PLANET_2_NAME = {}  # {PLANET.SOL(int): "Солнце"}
    NAME_2_ZNAK = {}  # {"Овен": ZNAK.OVEN(int)}
    ZNAK_2_NAME = {}  # {ZNAK.OVEN(int): "Овен"}
    NAME_2_ASPECT = {}  # {"трин": 120}
    MAJOR_ORBS = {}  # {SOL: {LUNA: orbis(float)}}

    def __init__(self):
        pass

    @classmethod
    def readAliases(cls, aliasCfg):
        for ru_key, name in aliasCfg.ALIASES_ZNAK.items():
            znak = getattr(ZNAK, name)
            cls.NAME_2_ZNAK[ru_key] = znak
            cls.ZNAK_2_NAME[znak] = ru_key
        for ru_key, name in aliasCfg.ALIASES_PLANET.items():
            planet = getattr(PLANET, name)
            cls.NAME_2_PLANET[ru_key] = planet
            cls.PLANET_2_NAME[planet] = ru_key
        for ru_key, name in aliasCfg.ALIASES_ASPECT.items():
            cls.NAME_2_ASPECT[ru_key] = getattr(ASPECT, name)

    @classmethod
    def readAspectOrbises(cls, vronskyCfg):
        for planet1_name, planet_2_orbis in vronskyCfg.MAJOR_ASPECT_ORBIS.items():
            planet1 = cls.NAME_2_PLANET[planet1_name]
            planet1_dict = cls.MAJOR_ORBS.setdefault(planet1, {})
            for planet2_name, orbis in planet_2_orbis.items():
                planet2 = cls.NAME_2_PLANET[planet2_name]
                planet1_dict[planet2] = orbis

    @classmethod
    def make_planet(self, planet_, znak_, gradus_):
        planet = self.NAME_2_PLANET.get(planet_)
        znak = self.NAME_2_ZNAK.get(znak_)
        gradus = self.parse_gradus(gradus_)
        if (planet is not None) and (znak is not None) and (gradus is not None):
            return Planet(planet, znak, gradus)
        err = "BAD make_planet: %s, %s, %s" % (planet, znak, gradus)
        print(err)
        raise BaseException(err)
        return None

    @classmethod
    def parse_gradus(self, gradus_):
        gradus = None
        rest = ''
        try:
            g, rest = gradus_.split('°')
            gradus = float(g)
        except:
            pass
        try:
            g, rest = gradus_.split('*')
            gradus = float(g)
        except:
            pass
        # TODO: handle minutes & seconds
        minutes = None
        try:
            m, rest = rest.split("'")
            minutes = float(m)
        except:
            pass
        if minutes is not None:
            gradus += minutes/60.0
        seconds = None
        try:
            if rest.endswith('"'):
                seconds = float(rest)
        except:
            pass
        if seconds is not None:
            gradus += seconds/3600.0
        return gradus


class Horoscope:
    def __init__(self):
        self.planets = {}  # PLANET.SOL(int): Planet
        self.houses = {}  # PLANET.ASC(int): Planet with extra "house" fields (notably .size)

    def parsePlanet(self, line):
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose: print(elems)
        planet_ = znak_ = gradus_ = None
        for token in elems:
            if (planet_ is None) and Config.NAME_2_PLANET.get(token) is not None: planet_ = token
            if (znak_ is None) and Config.NAME_2_ZNAK.get(token) is not None: znak_ = token
            if (gradus_ is None) and token.find('*') > 0 or token.find('°') > 0:
                gradus_ = token
        try:
            p = Config.make_planet(planet_, znak_, gradus_)
            print("PARSED:", p)
            self.planets[p.planet] = p
        except:
            print(elems)

    def calcHouses(self):
        planets = [planet for pid, planet in self.planets.items() if pid not in PLANET._KUSPIDS]
        if verbose: print('planets at start:', [str(planet) for planet in planets])
        for house_id in PLANET._KUSPIDS:
            next_id = house_id + 1 if house_id + 1 <= PLANET._HOUSE_LAST else PLANET._HOUSE_FIRST
            house, next = self.planets[house_id], self.planets[next_id]
            house.size = size = orb(house.abs_gradus, next.abs_gradus)
            if verbose: print("house SIZE:", house.size, house, next)

            # для всех еще не посчитанных планет:
            for planet in planets[:]:
                # учитываем, что градусы зациклены, так что проще посмотреть орбы от начала и конца дома
                start_orb = orb(planet.abs_gradus, house.abs_gradus)
                end_orb = orb(planet.abs_gradus, next.abs_gradus)
                if start_orb < size and end_orb < size:
                    planet.house = house_id
                    if start_orb < size/3:
                        planet.third = 1  # ближе к началу дома
                    elif end_orb < size/3:
                        planet.third = 3  # ближе к концу дома
                    else:
                        planet.third = 2  # посерединке
                    print("THIRD: %s %d/3 size=%0.2f/3=%0.2f orb=%0.2f %s" % (
                        planet, planet.third, size, size/3, start_orb, house))
                    planets.remove(planet)  # ок, посчитали => удаляем из непосчитанных
                    if verbose: print('planets left:', [str(planet) for planet in planets])

    def findAspects(self):
        self.aspects = []
        planets = self.planets.values()
        aspects = Config.NAME_2_ASPECT.items()
        for p1 in planets:
            for p2 in planets:
                arc = p1.orb(p2)
                p1nr, p2nr = p1.get_non_retro(), p2.get_non_retro()
                ORBS = Config.MAJOR_ORBS
                table_orbis = ORBS.get(p1nr, {}).get(p2nr, None) or ORBS.get(p2nr, {}).get(p1nr, None)
                isKuspid1 = p1nr in PLANET._KUSPIDS
                isKuspid2 = p2nr in PLANET._KUSPIDS
                if (table_orbis is None) and (isKuspid1 or isKuspid2) and not(isKuspid1 and isKuspid2):
                    # Only one of the actors is house kuspid (but not both):
                    table_orbis = LESSER_KUSPID_ORBIS
                if table_orbis is None:
                    if verbose: print("--- BAD orbis:", p1, p2, table_orbis)
                    continue
                for aname, aspect in aspects:
                    # minor aspects are 3.0 for planets (but could be less for kuspids etc.)
                    orbis = table_orbis if aspect not in ASPECT._MINORS else min(table_orbis, MINOR_ASPECT_ORBIS)
                    if abs(arc - aspect) < orbis:
                        self.aspects.append((p1, p2, aspect))
                        print("ASPECT: %s %s %s %d %0.3f %0.1f" % (p1.name(), aname, p2.name(), aspect, arc, orbis))


with open("aliases.yaml", encoding='utf8') as cfg_file:
    ALIAS_CFG = AliasConfig(**yaml.safe_load(cfg_file))
if verbose: print(f"ALIAS_CFG: '{ALIAS_CFG}'")

with open("vronsky_tables.yaml", encoding='utf8') as cfg_file:
    VRONSKY_CFG = VronskyTableConfig(**yaml.safe_load(cfg_file))
if verbose: print(f"VRONSKY_CFG: '{VRONSKY_CFG}'")

cfg = Config()
cfg.readAliases(ALIAS_CFG)
if verbose:
    print(f"NAME_2_PLANET: '{Config.NAME_2_PLANET}'")
    print(f"NAME_2_ZNAK: '{Config.NAME_2_ZNAK}'")
    print(f"NAME_2_ASPECT: '{Config.NAME_2_ASPECT}'")

cfg.readAspectOrbises(VRONSKY_CFG)
#print("MAJOR ORBISES:")
#pretty(cfg.MAJOR_ORBS)
print("SOL to LUNA orbis:", cfg.MAJOR_ORBS[PLANET.SOL][PLANET.LUNA], cfg.MAJOR_ORBS[PLANET.LUNA][PLANET.SOL])

hor = Horoscope()

#with open("in.txt", "rt", encoding='utf8') as horoscope_file:
with open("data/A.txt", "rt", encoding='utf8') as horoscope_file:
    for line in horoscope_file:
        hor.parsePlanet(line)

hor.calcHouses()
hor.findAspects()
