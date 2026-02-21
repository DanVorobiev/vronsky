#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pprint import pprint as pretty
#from itertools import combinations

from const import *
import config
from config import Config
from planet import Planet


class Horoscope:
    def __init__(self):
        self.planets = {}  # PLANET.SOL(int): Planet
        self.houses = {}  # PLANET.ASC(int): Planet with extra "house" fields (notably .size)
        self.natDate = None
        self.natTime = None
        self.natHour = None
        self.isDayBirth = False
        self.closestToMC = (0, FULL_ARC)  # орбис для ближайшей к MC планеты (только в пределах X/IX домов)

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
                print("DMY", day, month, year)
            elif token.find(':') > 0:
                # parse time: "12:20"
                hours, minutes = map(int, token.split(':')[:2])
                print("HM", hours, minutes)
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

        import datetime
        day, month, year = self.natDate
        weekday = datetime.date(year=year, month=month, day=day).weekday()

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
            birthHourOwnerID = Config.NIGHT_HOUR_OWNER[weekday][self.natHour - 1]
        else:
            # дневное рождение
            self.isDayBirth = True
            minsTotal = minsZakat - minsVoshod
            fHour = float(minsNat - minsVoshod) / (minsZakat - minsVoshod) * 12
            self.natHour = int(fHour) + 1
            print("DAY BIRTH: natal hour %d (%0.2f), %d/%d" % (self.natHour, fHour, minsNat - minsVoshod, minsTotal))
            birthHourOwnerID = Config.DAY_HOUR_OWNER[weekday][self.natHour - 1]

        planet = self.planets.get(birthHourOwnerID) or self.planets.get(birthHourOwnerID + PLANET._RETRO)
        planet.set_bonus(BONUS.HOUR_DOMINANT, Config.BONUS_POINTS['HOUR_DOMINANT'])

        # доминант года рождения
        planet_id = Config.get_year_dominant(year)
        planet = self.planets.get(planet_id) or self.planets.get(planet_id + PLANET._RETRO)
        planet.set_bonus(BONUS.YEAR_DOMINANT, Config.BONUS_POINTS['YEAR_DOMINANT'])

        # доминант дня рождения (этого дня недели)
        planet_id = Config.get_weekday_dominant(weekday)
        planet = self.planets.get(planet_id) or self.planets.get(planet_id + PLANET._RETRO)
        planet.set_bonus(BONUS.WEEKDAY_DOMINANT, Config.BONUS_POINTS['WEEKDAY_DOMINANT'])

        # доминант рождения (ASC)
        self.hasASCDominant = False
        asc_pids = set()
        asc = self.planets.get(PLANET.ASC)
        planet_roles = Config.ZNAK_ROLES[asc.znak]
        for pid, role in planet_roles.items():
            if role == ROLE.DOMICILE:
                planet = self.planets.get(pid)
                asc_pids.add(pid)
                if planet is not None:
                    planet.set_bonus(BONUS.ASC_DOMINANT, Config.BONUS_POINTS['ASC_DOMINANT'])
                    self.hasASCDominant = True
        if not self.hasASCDominant: print("(!) NOTE: Нет доминанта ASC (%s)" % str(
            [Config.PLANET_2_NAME[pid] for pid in list(asc_pids)]))

        # доминант MC
        self.hasMCDominant = False
        mc = self.planets.get(PLANET.MC)
        mc_pids = set()
        planet_roles = Config.ZNAK_ROLES[mc.znak]
        for pid, role in planet_roles.items():
            if role == ROLE.DOMICILE:
                mc_pids.add(pid)
                planet = self.planets.get(pid)
                if planet is not None:
                    planet.set_bonus(BONUS.MC_DOMINANT, Config.BONUS_POINTS['MC_DOMINANT'])
                    self.hasMCDominant = True
        if not self.hasMCDominant: print("NOTE: Нет доминанта MC (%s)" % str(
            [Config.PLANET_2_NAME[pid] for pid in list(mc_pids)]))

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
        p = self.planets.get(prev.planet) or self.planets.get(prev.planet + PLANET._RETRO)

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

        print("day SPEED: %s (%s) avg:%s %s %s" % (formatOrb(p.day_speed), speedStr,
                                                   formatOrb(avg_spd or 0), p, prev))

    def calcHouses(self):
        newline()
        mc = self.planets.get(PLANET.MC)
        self.closestToMC = (PLANET._NONE, FULL_ARC)
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

                    # баллы за дом/треть
                    planet_house3_points = Config.HOUSE_THIRD_POINTS.get(planet.planet)
                    if planet_house3_points is not None:
                        points = planet_house3_points[planet.house][planet.third-1]
                        planet.set_bonus(BONUS.HOUSE_THIRD, points)

                    # баллы за знак/градус
                    planet_gradus_points = Config.PLANET_GRADUS_BONUSES.get(planet.planet, {}).get(planet.znak)
                    if planet_gradus_points is not None:
                        points = planet_gradus_points[int(planet.gradus)]
                        planet.set_bonus(BONUS.PLANET_GRADUS, points)

                    # доп.баллы за термы
                    pnr = planet.get_non_retro()
                    planet_termy_points = Config.BONUS_TERMY.get(pnr)
                    if planet_termy_points is not None:
                        gradus1, gradus2, bonus_points = planet_termy_points[planet.znak]
                        if gradus1 <= planet.abs_gradus < gradus2:
                            planet.set_bonus(BONUS.TERMY, bonus_points)

                    # в "своем" поле/доме (например, Марс в I доме, а считая от равноденствия I дом = Овен, "свой" дом)
                    house_znak = planet.house - 1
                    role = Config.ZNAK_ROLES[house_znak].get(planet.planet, -1)
                    if role == ROLE.DOMICILE:
                        planet.set_bonus(BONUS.OWN_HOUSE, Config.BONUS_POINTS['OWN_HOUSE'])

                    # в своем градусе (из таблицы управителей градусов по Вронскому)
                    if planet.is_own_gradus_dominant():
                        planet.set_bonus(BONUS.OWN_GRADUS, Config.BONUS_POINTS['OWN_GRADUS'])

                    # ищем ближайшую планету к MC
                    if mc and (planet.house in (9,10)) and (pnr in PLANET._REAL_PLANETS):
                        range = orb(planet.abs_gradus, mc.abs_gradus)
                        if range < self.closestToMC[1]:
                            self.closestToMC = (planet.planet, range)

                    # в ретрограде
                    if planet.planet & PLANET._RETRO:
                        planet.set_bonus(BONUS.RETRO, Config.BONUS_POINTS['RETRO'])

                    # в каком типе знака (кардинальный, фиксированный, мутабельный) - там свои бонусы по отдельным дугам
                    znak_bonus_type = Planet.get_znak_bonus_type(planet.znak)
                    if planet.has_znak_bonus():
                        planet.set_bonus(znak_bonus_type, Config.BONUS_POINTS['CARD_ZNAK_BONUS'])

                    # особые диапазоны градусов (в Тельце, Льве, Деве, комбуста..)
                    for bonus_key, (gradus1, gradus2) in Config.BONUS_GRADUS.items():
                        if gradus1 <= planet.abs_gradus <= gradus2:
                            bonus_type = getattr(BONUS, bonus_key)
                            planet.set_bonus(bonus_type, Config.BONUS_POINTS[bonus_key])

                    planet_attrs = Config.PLANET_ATTRS.get(pnr)
                    if planet_attrs:
                        if (planet_attrs.stihia >= 0) and (planet_attrs.stihia == ZNAK._stihia(planet.znak)):
                            # в знаке своей стихии (огонь, вода и т.п.)
                            planet.set_bonus(BONUS.STIHIA, Config.BONUS_POINTS['OWN_STIHIA'])

                        if (planet_attrs.gender >= 0):
                            if (planet_attrs.gender == ZNAK._gender(planet.znak)):
                                # в знаке своего пола
                                planet.set_bonus(BONUS.GENDER, Config.BONUS_POINTS['OWN_GENDER'])
                            else:
                                # в знаке противоположного пола
                                planet.set_bonus(BONUS.GENDER, Config.BONUS_POINTS['WRONG_GENDER'])

                        # в своем градусе экзальтации ("королевском градусе")
                        if planet_attrs.exalt_gradus != BAD_GRADUS:
                            eg = planet_attrs.exalt_gradus
                            if eg <= planet.abs_gradus < eg+1:
                                planet.set_bonus(BONUS.EXALT_GRADUS, Config.BONUS_POINTS['EXALT_GRADUS'])

                    # в своем домициле/экзальте/эксиле/фалле
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

        # есть ли у нас победитель в конкурсе "кто ближе всех к MC"?
        winner, actual_orbis = self.closestToMC
        if winner != PLANET._NONE:
            winner_planet = self.planets.get(winner)
            self.checkAspectBonus(winner_planet, mc, ASPECT._CLOSEST_MC, actual_orbis)

    def findAspects(self):
        self.aspects = []
        planets = self.planets.values()
        aspects = ASPECT_VALUES
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
                for aspect in ASPECT_VALUES:
                    aname = Config.ASPECT_2_NAME[aspect]
                    # minor aspects are 3.0 for planets (but could be less for kuspids etc.)
                    orbis = table_orbis if aspect not in ASPECT._MINORS else min(table_orbis, MINOR_ASPECT_ORBIS)
                    actual_orbis = abs(arc - aspect)
                    if actual_orbis < orbis:
                        self.aspects.append((p1, p2, aspect))
                        if p1 != last_planet: newline()
                        print("ASPECT: %s %s %s %d %0.3f %0.1f" % (p1.name(), aname, p2.name(), aspect, arc, orbis))
                        last_planet = p1
                        self.checkAspectBonus(p1, p2, aspect, actual_orbis)

    def checkAspectBonus(self, p1, p2, aspect, actual_orbis):
        for bonus in Config.BONUS_ASPECTS:
            if ((aspect == bonus.aspect) and (p2.planet in bonus.to_planets) and (p1.planet in bonus.planet_mask)):
                if ((bonus.from_orbis < 0) or (bonus.from_orbis <= actual_orbis <= bonus.to_orbis)):
                    if verbose:print("ASPECT BONUS:", bonus.bonus_type, bonus.bonus_points, p1, p2,
                                     bonus.from_orbis, actual_orbis, bonus.to_orbis)
                    p1.set_bonus(bonus.bonus_type, bonus.bonus_points)

    def printoutPlanets(self, include_bonuses=True):
        "Уран; Рыбы 4*39';	II;	3/3; FAST; 2"
        print("--- PLANETS: ---")
        for pid, p in self.planets.items():
            roleBonus = p.get_bonus_str(BONUS._HOUSE_ROLES)
            roleStr = "{%s}" % roleBonus[:-1] if roleBonus else ''

            znak = Config.ZNAK_2_NAME[p.znak]
            znakStr = "%s %s %s" % (znak, formatOrb(p.gradus), roleStr)

            houseStr = toRoman(p.house) if p.house else '-'

            speedBonus = p.get_bonus(BONUS.SPEED) or 0
            speedStr = "-" if not speedBonus else "FAST" if speedBonus > 0 else "SLOW"

            allBonuses = p.get_bonus_str()
            bonusSum = p.sum_bonuses()
            bonusSumStr = ('+' if bonusSum > 0 else '') + str(bonusSum)

            outputStr = "%3s %-10s %-30s %4s/%s" % (bonusSumStr, p.name(), znakStr, houseStr, p.third or '-')
            if include_bonuses: outputStr += '   # %s' % allBonuses
            print(outputStr)

            #print("%3s %-10s %-30s; %4s; %-2s; %4s; %2d; %90s;" % (
            #    bonusSumStr, p.name(), znakStr, houseStr, p.third or '-', speedStr, speedBonus, allBonuses))


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

    with open("data/_example.txt", "rt", encoding='utf8') as horoscope_file:
    #with open("data/NT-0630.txt", "rt", encoding='utf8') as horoscope_file:
    #with open("data/SB-0640.txt", "rt", encoding='utf8') as horoscope_file:
        for line in horoscope_file:
            hor.parseLine(line)

    hor.calcHouses()
    hor.findAspects()
    hor.calcNatals()

    INCLUDE_BONUSES = True
    hor.printoutPlanets(INCLUDE_BONUSES)
