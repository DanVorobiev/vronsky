#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
from dataclasses import dataclass, asdict
import logging
from pprint import pprint as pretty
from itertools import combinations

verbose = False
#verbose = True

PREV_TAG = "PREV"

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

    _CARDINAL = [OVEN, RAK, VESY, KOZEROG]
    _FIXED = [TELEC, LEV, SCORPION, VODOLEY]
    _MUTABLE = [BLIZNECY, DEVA, STRELEC, RYBY]

ZNAK_ALL = [k for k in ZNAK.__dict__.keys() if not k.startswith('_')]

def getZnakType(znak):
    if znak in ZNAK._CARDINAL:
        return "Кард"
    elif znak in ZNAK._FIXED:
        return "Фикс"
    elif znak in ZNAK._MUTABLE:
        return "Мутаб"
    return "?"


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
    PROZERPINA_RETRO = PROZERPINA + _RETRO

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


class ROLE:
    _NONE = 0
    DOMICILE = 1
    EXALTATION = 2
    EXILE = 3
    FALL = 4

    _NAMES = {
        DOMICILE: 'дом+',
        EXALTATION: 'экз+',
        EXILE:'экс-',
        FALL: 'фалл-'
    }

ROLE_NAMES = {v:ROLE._NAMES[v] for k, v in ROLE.__dict__.items() if not k.startswith('_')}


ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

def toRoman(num):
    try:
        return ROMANS[num-1]
    except:
        return str(num)


class NATAL:
    DATE_TIME = 'нат'
    VOSHOD = 'восход'
    ZAKAT = 'закат'

NATAL_TAGS = dict([(v, k) for k, v in NATAL.__dict__.items() if not k.startswith('_')])

def absGradus(znak, gradus):
    return znak * ZNAK_ARC + gradus


def orb(abs_gradus1, abs_gradus2):
    diff = abs(abs_gradus1 - abs_gradus2)
    if diff > HALF_ARC:
        diff = FULL_ARC - diff
    return diff


def orbz(znak1, gradus1, znak2, gradus2):
    return orb(absGradus(znak1, gradus1), absGradus(znak2, gradus2))


def formatOrb(abs_gradus):
    gradus = int(abs_gradus)
    mins_secs = (abs_gradus - gradus) * 60
    mins = int(mins_secs)
    secs = round((mins_secs - mins) * 60)
    return("%d°%02d'%02d\"" % (gradus, mins, secs))


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

        # can be calculated with prev.day gradus (use PREV tag in the beginning of the planet line)
        self.day_speed = None

        self.speed = ''
        self.speedBonus = 0
        self.znakBonus = ''

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
        if self.day_speed is not None:
            s += ', spd=%s' % formatOrb(self.day_speed)
        return s + ')'

    def name(self):
        return Config.PLANET_2_NAME.get(self.planet)

    # get base planet sign, without retrograde component
    def get_non_retro(self):
        p = self.planet
        return p if (p & PLANET._RETRO) == 0 else (p ^ PLANET._RETRO)

    def has_znak_bonus(self):
        bonus_ranges = Config.ZNAK_BONUS_RANGES.get(self.znak)
        for (start, end) in bonus_ranges:
            if start <= self.abs_gradus <= end:
                return True
        return False


@dataclass
class AliasConfig:
    ALIASES_ZNAK: dict
    ALIASES_PLANET: dict
    ALIASES_ASPECT: dict

@dataclass
class VronskyTableConfig:
    MAJOR_ASPECT_ORBIS: dict
    AVG_PLANET_SPD: dict
    CARDINAL_FIXED_MUTABLE_BONUS_RANGE: list
    ZNAK_DOMINANTS: dict
    EXALTATION_GRADUS: dict

class Config:
    NAME_2_PLANET = {}  # {"Солнце": PLANET.SOL(int)}
    PLANET_2_NAME = {}  # {PLANET.SOL(int): "Солнце"}
    NAME_2_ZNAK = {}  # {"Овен": ZNAK.OVEN(int)}
    ZNAK_2_NAME = {}  # {ZNAK.OVEN(int): "Овен"}
    NAME_2_ASPECT = {}  # {"трин": 120}
    MAJOR_ORBS = {}  # {SOL: {LUNA: orbis(float)}}
    AVG_SPD = {}  # {SOL: gradus(float)}
    ZNAK_BONUS_RANGES = {}  # {ZNAK.OVEN(int): [(0, 12.51), (25.43, 30.0)]}, all cardinal/fixed/mutable bonus arcs.
    ZNAK_ROLES = {}  # {OVEN: {SOL: EXALTATION}}
    PLANET_ZNAK_ROLES = {}  # {SOL: {OVEN: EXALTATION}}

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

        # Average planet speeds
        for planet_name, gradus_ in vronskyCfg.AVG_PLANET_SPD.items():
            if verbose: print("AVG SPD %s %s" % (planet_name, gradus_))
            planet = cls.NAME_2_PLANET[planet_name]
            abs_gradus = cls.parse_gradus(gradus_)
            cls.AVG_SPD[planet] = abs_gradus
            if verbose: print("AVG SPD %s [%d] = %0.3f (%s)" % (planet_name, planet, abs_gradus, gradus_))

        # CARDINAL_FIXED_MUTABLE_BONUS_RANGE
        for (znak_type_, start_, end_) in vronskyCfg.CARDINAL_FIXED_MUTABLE_BONUS_RANGE:
            applicable_signs = getattr(ZNAK, '_' + znak_type_)
            start_orb = cls.parse_gradus(start_)
            end_orb = cls.parse_gradus(end_)
            for znak in applicable_signs:
                abs_start = absGradus(znak, start_orb)
                abs_end = absGradus(znak, end_orb)
                range_list = cls.ZNAK_BONUS_RANGES.setdefault(znak, [])
                range_list.append((abs_start, abs_end))

        # ZNAK_DOMINANTS
        for (znak_name, planet_2_role) in vronskyCfg.ZNAK_DOMINANTS.items():
            znak = cls.NAME_2_ZNAK[znak_name]
            roles = cls.ZNAK_ROLES.setdefault(znak, {})
            for planet_name, role_name in planet_2_role.items():
                planet_id = cls.NAME_2_PLANET[planet_name]
                role = getattr(ROLE, role_name)
                roles[planet_id] = role
                if verbose: print("set znak[%s] planet [%s] %d role = %s" % (znak, planet_name, planet_id, role))
                planet_znak_roles = cls.PLANET_ZNAK_ROLES.setdefault(planet_id, {})
                planet_znak_roles[znak] = role
                if verbose: print("set planet[%s] %d znak[%s] role = %s" % (planet_name, planet_id, znak, role))

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
        gradus = 0.0
        rest = gradus_
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
        # handle minutes & seconds
        minutes = None
        try:
            m, rest = rest.split("'")
            minutes = float(m)
        except:
            pass
        try:
            if rest.endswith("'"):
                minutes = float(rest[:-1])
        except:
            pass
        if verbose: print("min/rest", minutes, repr(rest), gradus)
        if minutes is not None:
            gradus += minutes/60.0
        seconds = None
        try:
            if rest.endswith('"'):
                seconds = float(rest[:-1])
        except:
            pass
        if verbose: print("sec/rest", seconds, repr(rest), gradus)
        if seconds is not None:
            gradus += seconds/3600.0
        return gradus


def newline():
    print('---')


def hasGradus(token):
    return token.find('*') > 0 or token.find('°') > 0


class Horoscope:
    def __init__(self):
        self.planets = {}  # PLANET.SOL(int): Planet
        self.houses = {}  # PLANET.ASC(int): Planet with extra "house" fields (notably .size)
        self.natDate = None
        self.natTime = None
        self.natHour = None
        self.isDayBirth = False

    def parseLine(self, line):
        if line.startswith("//") or line.startswith("#"):
            return
        elif line.startswith(PREV_TAG):
            self.parsePlanetSpeed(line)
        elif hasGradus(line):
            self.parsePlanet(line)
        else:
            self.parseNatals(line)

    def parseNatals(self, line):
        tokens = line.split()
        if verbose: print('natal tokens:', tokens)

        natal_tag = None
        for token in tokens:
            if token.find('.') > 0:
                # parse date: "01.01.2000"
                day, month, year = map(int, token.split('.'))
            elif token.find(':') > 0:
                # parse time: "12:20"
                hours, minutes = map(int, token.split(':')[:2])
            elif token in NATAL_TAGS:
                natal_tag = NATAL_TAGS[token]
                if verbose: print('natal_tag:', natal_tag)

        if natal_tag == 'DATE_TIME':
            self.natDate = (day, month, year)
            self.natHour = (hours, minutes)
            print("NATAL DATE:", self.natDate, self.natHour)
        elif natal_tag == 'VOSHOD':
            self.natVoshod = (hours, minutes)
            print("NATAL VOSHOD:", self.natVoshod)
        elif natal_tag == 'ZAKAT':
            self.natZakat = (hours, minutes)
            print("NATAL ZAKAT:", self.natZakat)

    def calcNatals(self):
        if not (self.natHour and self.natVoshod and self.natZakat):
            return
        newline()
        print("NATAL DATE:", self.natDate, self.natHour)
        hours, minutes = self.natHour
        minsNat = hours*60 + minutes
        hours, minutes = self.natVoshod
        minsVoshod = hours*60 + minutes
        hours, minutes = self.natZakat
        minsZakat = hours*60 + minutes

        if minsNat < minsVoshod or minsNat >= minsZakat:
            # ночное рождение
            self.isDayBirth = False
            minsTillMidnight = 24*60 - minsZakat
            minsTotal = minsTillMidnight + minsVoshod # ночь до полуночи + ночь до рассвета (всего ночных минут)
            if minsNat < minsVoshod:
                minsNat += minsTillMidnight
            else:
                minsNat = minsNat - minsZakat
            fHour = float(minsNat) / minsTotal * 12
            self.natHour = int(fHour) + 1
            print("NIGHT BIRTH: natal hour %d (%0.2f), %d/%d" % (self.natHour, fHour, minsNat, minsTotal))
        else:
            # дневное рождение
            self.isDayBirth = True
            minsTotal = minsZakat - minsVoshod
            fHour = float(minsNat - minsVoshod) / (minsZakat - minsVoshod) * 12
            self.natHour = int(fHour) + 1
            print("DAY BIRTH: natal hour %d (%0.2f), %d/%d" % (self.natHour, fHour, minsNat - minsVoshod, minsTotal))

    def _parsePlanet(self, line):
        if not hasGradus(line):
            return
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose: print(elems)
        planet_ = znak_ = gradus_ = None
        for token in elems:
            if (planet_ is None) and Config.NAME_2_PLANET.get(token) is not None: planet_ = token
            if (znak_ is None) and Config.NAME_2_ZNAK.get(token) is not None: znak_ = token
            if (gradus_ is None) and hasGradus(token):
                gradus_ = token
        try:
            p = Config.make_planet(planet_, znak_, gradus_)
            return p
        except:
            print(elems)

    def parsePlanet(self, line):
        p = self._parsePlanet(line)
        if p is None:
            return
        print("PARSED:", p)
        self.planets[p.planet] = p

    def parsePlanetSpeed(self, line):
        prev = self._parsePlanet(line)
        if prev is None:
            return
        if verbose: print("PREV:", prev)
        p = self.planets.get(prev.planet)
        p.day_speed = abs(p.abs_gradus - prev.abs_gradus)
        avg_spd = Config.AVG_SPD.get(p.get_non_retro())
        speedStr = '-'
        if avg_spd is not None:
            if p.day_speed < avg_spd:
                p.speed = speedStr = 'SLOW'
                p.speedBonus = -2
            else:
                p.speed = speedStr = 'FAST'
                p.speedBonus = 2
        znak_type = getZnakType(p.znak)
        if p.has_znak_bonus():
            p.znakBonus = znakBonusStr = znak_type+':+4'
        else:
            znakBonusStr = znak_type+':-'
            p.znakBonus = ''

        print("day SPEED: %s (%s) avg:%s %s %s [%s]" % (formatOrb(p.day_speed), speedStr,
                                                        formatOrb(avg_spd or 0), p, prev, znakBonusStr))

    def calcHouses(self):
        newline()
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
                    role = Config.ZNAK_ROLES[planet.znak].get(planet.planet)
                    roleStr = "{%s}" % ROLE_NAMES[role] if role is not None else ''
                    print("THIRD: %s %d/3 size=%0.2f/3=%0.2f orb=%0.2f %s %s" % (
                        planet, planet.third, size, size/3, start_orb, house, roleStr))
                    planets.remove(planet)  # ок, посчитали => удаляем из непосчитанных
                    if verbose: print('planets left:', [str(planet) for planet in planets])

    def findAspects(self):
        self.aspects = []
        planets = self.planets.values()
        aspects = Config.NAME_2_ASPECT.items()
        last_planet = None
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
                        if p1 != last_planet: newline()
                        print("ASPECT: %s %s %s %d %0.3f %0.1f" % (p1.name(), aname, p2.name(), aspect, arc, orbis))
                        last_planet = p1

    def printoutPlanets(self):
        "Уран; Рыбы 4*39';	II;	3/3; FAST; 2"
        print("--- PLANETS: ---")
        for pid, p in self.planets.items():
            role = Config.ZNAK_ROLES[p.znak].get(pid)
            roleStr = "{%s}" % ROLE_NAMES[role] if role is not None else ''

            znak = Config.ZNAK_2_NAME[p.znak]
            znakStr = "%s %s %s" % (znak, formatOrb(p.gradus), roleStr)

            houseStr = toRoman(p.house - PLANET._HOUSE_BASE) if p.house else ''

            print("%s; %s; %s; %s; %s; %d; %s" % (
                p.name(), znakStr, houseStr, p.third, p.speed, p.speedBonus, p.znakBonus))



with open("aliases.yaml", encoding='utf8') as cfg_file:
    ALIAS_CFG = AliasConfig(**yaml.safe_load(cfg_file))
if verbose: print(f"ALIAS_CFG: '{ALIAS_CFG}'")

with open("vronsky_tables.yaml", encoding='utf8') as cfg_file:
    VRONSKY_CFG = VronskyTableConfig(**yaml.safe_load(cfg_file))
if verbose:
    print(f"VRONSKY_CFG: '{VRONSKY_CFG}'")
    pretty(VRONSKY_CFG.ZNAK_DOMINANTS)

cfg = Config()
cfg.readAliases(ALIAS_CFG)
if verbose:
    print(f"NAME_2_PLANET: '{Config.NAME_2_PLANET}'")
    print(f"NAME_2_ZNAK: '{Config.NAME_2_ZNAK}'")
    print(f"NAME_2_ASPECT: '{Config.NAME_2_ASPECT}'")
    print('NATAL_TAGS:', NATAL_TAGS)

cfg.readAspectOrbises(VRONSKY_CFG)
#print("MAJOR ORBISES:")
#pretty(cfg.MAJOR_ORBS)
if verbose:
    pretty(Config.ZNAK_BONUS_RANGES)
    pretty(Config.ZNAK_ROLES)
    pretty(Config.PLANET_ZNAK_ROLES)
print("SOL to LUNA orbis:", cfg.MAJOR_ORBS[PLANET.SOL][PLANET.LUNA], cfg.MAJOR_ORBS[PLANET.LUNA][PLANET.SOL])

hor = Horoscope()

#with open("data/_example.txt", "rt", encoding='utf8') as horoscope_file:
with open("data/M.txt", "rt", encoding='utf8') as horoscope_file:
    for line in horoscope_file:
        hor.parseLine(line)

hor.calcHouses()
hor.findAspects()
hor.calcNatals()

hor.printoutPlanets()
