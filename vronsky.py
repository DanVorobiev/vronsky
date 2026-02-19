#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pprint import pprint as pretty
#from itertools import combinations

from const import *
import config
from config import Config
from planet import Planet, BONUS


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
            planet, znak, gradus = Config.make_planet_args(planet_, znak_, gradus_)
            p = Planet(planet, znak, gradus)
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

        # скорость за день (сравниваем со средней угловой скоростью, табличной)
        pnr = p.get_non_retro()
        p.day_speed = abs(p.abs_gradus - prev.abs_gradus)
        avg_spd = Config.AVG_SPD.get(pnr)
        speedStr = '-'
        if avg_spd is not None:
            if p.day_speed < avg_spd:
                p.set_bonus(BONUS.SPEED, Config.BONUS_POINTS['SLOW_SPEED'])
            else:
                p.set_bonus(BONUS.SPEED, Config.BONUS_POINTS['FAST_SPEED'])

        # в каком типе знака (кардинальный, фиксированный, мутабельный) - там свои бонусы по отдельным дугам
        znak_bonus_type = Planet.get_znak_bonus_type(p.znak)
        if p.has_znak_bonus():
            p.set_bonus(znak_bonus_type, Config.BONUS_POINTS['CARD_ZNAK_BONUS'])
        znakBonusStr = p.get_bonus_str(())

        planet_attrs = Config.PLANET_ATTRS.get(pnr)
        if planet_attrs:
            if (planet_attrs.stihia >= 0) and (planet_attrs.stihia == ZNAK._stihia(p.znak)):
                # в знаке своей стихии (огонь, вода и т.п.)
                p.set_bonus(BONUS.STIHIA, Config.BONUS_POINTS['OWN_STIHIA'])

            if (planet_attrs.gender >= 0):
                if (planet_attrs.gender == ZNAK._gender(p.znak)):
                    # в знаке своего пола
                    p.set_bonus(BONUS.GENDER, Config.BONUS_POINTS['OWN_GENDER'])
                else:
                    # в знаке противоположногно пола
                    p.set_bonus(BONUS.GENDER, Config.BONUS_POINTS['WRONG_GENDER'])

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
                    # номер дома
                    planet.house = house_id - PLANET._HOUSE_BASE  # 1..12

                    # в какой трети дома
                    if start_orb < size/3:
                        planet.third = 1  # ближе к началу дома
                    elif end_orb < size/3:
                        planet.third = 3  # ближе к концу дома
                    else:
                        planet.third = 2  # посерединке

                    # в "своем" поле/доме (например, Марс в I доме, а считая от равноденствия I дом = Овен, "свой" дом)
                    house_znak = planet.house - 1
                    role = Config.ZNAK_ROLES[house_znak].get(planet.planet, -1)
                    if role == ROLE.DOMICILE:
                        planet.set_bonus(BONUS.OWN_HOUSE, Config.BONUS_POINTS['OWN_HOUSE'])

                    roleStr = ''
                    role = Config.ZNAK_ROLES[planet.znak].get(planet.planet)
                    if role is not None:
                        role_key = ROLE_KEYS[role]  # 'DOMICILE'
                        bonus_points = Config.BONUS_POINTS.get(role_key)
                        if bonus_points:
                            bonus_type = getattr(BONUS, role_key)
                            planet.set_bonus(bonus_type, bonus_points)
                            roleStr = "{%s}" % planet.get_bonus_str(BONUS._HOUSE_ROLES)[:-1]

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
            roleStr = "{%s}" % p.get_bonus_str(BONUS._HOUSE_ROLES)[:-1]

            znak = Config.ZNAK_2_NAME[p.znak]
            znakStr = "%s %s %s" % (znak, formatOrb(p.gradus), roleStr)

            houseStr = toRoman(p.house) if p.house else ''

            speedBonus = p.get_bonus(BONUS.SPEED) or 0
            speedStr = "-" if not speedBonus else "FAST" if speedBonus > 0 else "SLOW"

            allBonuses = p.get_bonus_str()
            bonusSum = p.sum_bonuses()
            bonusSumStr = ('+' if bonusSum > 0 else '') + str(bonusSum)

            print("%-10s; %-28s; %4s; %-4s; %4s; %3d;      %50s;      %4s" % (
                p.name(), znakStr, houseStr, p.third or '-', speedStr, speedBonus, allBonuses, bonusSumStr))


if __name__ == '__main__':
    config.init()

    cfg = Config()
    cfg.readAliases(config.ALIAS_CFG)
    if verbose:
        print(f"NAME_2_PLANET: '{Config.NAME_2_PLANET}'")
        print(f"NAME_2_ZNAK: '{Config.NAME_2_ZNAK}'")
        print(f"NAME_2_ASPECT: '{Config.NAME_2_ASPECT}'")
        print('NATAL_TAGS:', NATAL_TAGS)
        pretty(Config.PLANET_ATTRS)

    cfg.readAspectOrbises(config.VRONSKY_CFG)
    #print("MAJOR ORBISES:")
    #pretty(cfg.MAJOR_ORBS)
    if verbose:
        pretty(Config.ZNAK_BONUS_RANGES)
        pretty(Config.ZNAK_ROLES)
        pretty(Config.PLANET_ZNAK_ROLES)
    print("SOL to LUNA orbis:", cfg.MAJOR_ORBS[PLANET.SOL][PLANET.LUNA], cfg.MAJOR_ORBS[PLANET.LUNA][PLANET.SOL])

    hor = Horoscope()

    #with open("data/_example.txt", "rt", encoding='utf8') as horoscope_file:
    with open("data/D.txt", "rt", encoding='utf8') as horoscope_file:
        for line in horoscope_file:
            hor.parseLine(line)

    hor.calcHouses()
    hor.findAspects()
    hor.calcNatals()

    hor.printoutPlanets()
