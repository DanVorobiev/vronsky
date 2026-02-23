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

    def parseRaw(self, line):
        if line.startswith("//") or line.startswith("#"):
            return
        elif line.startswith(PREV_TAG):
            self.parsePlanetSpeedRaw(line)
        elif hasGradus(line):
            self.parsePlanetRaw(line)
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
        elif natal_tag == 'NAME':
            self.natName = line

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
            self.natHour12 = int(fHour) + 1
            print("NIGHT BIRTH: natal hour %d (%0.2f), %d/%d" % (self.natHour12, fHour, minsNat, minsTotal))
            birthHourOwnerID = Config.NIGHT_HOUR_OWNER[weekday][self.natHour12 - 1]
        else:
            # дневное рождение
            self.isDayBirth = True
            minsTotal = minsZakat - minsVoshod
            fHour = float(minsNat - minsVoshod) / (minsZakat - minsVoshod) * 12
            self.natHour12 = int(fHour) + 1
            print("DAY BIRTH: natal hour %d (%0.2f), %d/%d" % (self.natHour12, fHour, minsNat - minsVoshod, minsTotal))
            birthHourOwnerID = Config.DAY_HOUR_OWNER[weekday][self.natHour12 - 1]

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

    def _parsePlanet(self, elems):
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

    def parsePlanetRaw(self, line):
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose2: print(elems)
        self.parseRawChunks(elems, self._parsePlanet, self._addPlanet)

    def parsePlanetSpeedRaw(self, line):
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose2: print(elems)
        self.parseRawChunks(elems, self._doParsePlanetSpeed, None)

    def parseRawChunks(self, elems, parseChunksCallback, addPlanetCallback):
        chunk = []
        isPlanetChunk = False
        PLANET_NAME_IDX = 0  # we always start chunk with a planet name
        for i, token in enumerate(elems):
            if Config.NAME_2_PLANET.get(token):
                # нашли планету!
                if isPlanetChunk:
                    # в нашем чанке уже есть имя планеты (и мы нашли следующее) -> обрабатываем чанк
                    if verbose2: print("parse complete chunk:", chunk)
                    p = parseChunksCallback(chunk)
                    if (p is not None) and addPlanetCallback is not None:
                        addPlanetCallback(p)
                    # reset chunk (to include just the current "planet-name" token)
                    chunk = [token]
                    isPlanetChunk = True
                else:
                    # начинаем накапливать чанки, начиная с планеты
                    chunk.append(token)
                    isPlanetChunk = True
                    if verbose2: print("start new chunk:", token)
            else:
                if isPlanetChunk:
                    # продолжаем накапливать чанки
                    if verbose: print("add chunk", token)
                    chunk.append(token)
                    if token in ("R", "D"):
                        # и кстати, если нашли признак директности или ретроградности - это относится к имени планеты
                        if not chunk[PLANET_NAME_IDX].endswith(token):
                            chunk[PLANET_NAME_IDX] += "-" + token
                            if verbose2: print("add planet suffix:", chunk[PLANET_NAME_IDX])
                else:
                    # просто скипаем чанки, пока не найдем планету
                    if verbose2: print("skip chunk", token)

        if chunk and isPlanetChunk:
            # дошли до конца, и в нашем чанке есть имя планеты -> обрабатываем чанк
            if verbose2: print("parse final chunk:", chunk)
            p = parseChunksCallback(chunk)
            if (p is not None) and addPlanetCallback is not None:
                addPlanetCallback(p)

    def _addPlanet(self, p):
        print("PARSED:", p)
        self.planets[p.planet] = p

    def parsePlanet(self, line):
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose: print(elems)
        p = self._parsePlanet(elems)
        if p is None:
            return
        print("PARSED:", p)
        self.planets[p.planet] = p

    def parsePlanetSpeed(self, line):
        elems = line.split()
        if (not elems) or len(elems) < 3:
            return
        if verbose: print(elems)
        self._doParsePlanetSpeed(elems)

    def _doParsePlanetSpeed(self, elems):
        prev = self._parsePlanet(elems)
        if prev is None:
            return
        if verbose: print("PREV:", prev)
        p = self.planets.get(prev.planet) or self.planets.get(prev.planet + PLANET._RETRO)

        # скорость за день (сравниваем со средней угловой скоростью, табличной)
        pnr = p.get_non_retro()
        p.prev_gradus = prev.abs_gradus
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

    def exportFile(self, output_file):
        output_file.write("%s\n" % self.natName or "???")
        day, month, year = self.natDate
        hours, minutes = self.natHour
        output_file.write("%s %02d.%02d.%d %02d:%02d\n" % (NATAL.DATE_TIME, day, month, year, hours, minutes))
        hours, minutes = self.natVoshod
        output_file.write("%s %02d:%02d\n" % (NATAL.VOSHOD, hours, minutes))
        hours, minutes = self.natZakat
        output_file.write("%s %02d:%02d\n\n" % (NATAL.ZAKAT, hours, minutes))

        # current positions (planets & houses)
        for pid, p in self.planets.items():
            znak = Config.ZNAK_2_NAME[p.znak]
            outputStr = "%s  %s  %s\n" % (p.name(), znak, formatOrb(p.gradus))
            if pid == PLANET.ASC: output_file.write("\n")
            output_file.write(outputStr)
        output_file.write("\n")

        # PREV day positions (planets only)
        for pid, p in self.planets.items():
            if PLANET._HOUSE_FIRST <= pid <= PLANET._HOUSE_LAST:
                continue
            znak = Config.ZNAK_2_NAME[p.znak]
            outputStr = "PREV  %s  %s  %s\n" % (p.name(), znak, formatOrb(p.prev_gradus))
            output_file.write(outputStr)

    def printoutPlanets(self, include_bonuses=INCLUDE_BONUSES.ALL):
        "Уран; Рыбы 4*39';	II;	3/3; FAST; 2"
        print("--- PLANETS: ---")
        for pid, p in self.planets.items():
            roleBonus = p.get_bonus_str(BONUS._HOUSE_ROLES)
            roleStr = "{%s}" % roleBonus[:-1] if roleBonus else ''

            znak = Config.ZNAK_2_NAME[p.znak]
            znakStr = "%s %s %s" % (znak, formatOrb(p.gradus), roleStr)

            house = toRoman(p.house) if p.house else '-'
            houseStr = "%3s/%s" % (house, p.third or '-')

            speedBonus = p.get_bonus(BONUS.SPEED) or 0
            speedStr = "-" if not speedBonus else "FAST" if speedBonus > 0 else "SLOW"

            if include_bonuses == INCLUDE_BONUSES.ASC_INDEPENDENT_ONLY:
                bonus_types = INCLUDE_BONUSES.ASC_INDEPENDENT_ONLY
                houseStr = '-'
            else:
                bonus_types = None
            allBonuses = p.get_bonus_str(bonus_types)
            bonusSum = p.sum_bonuses(bonus_types)
            bonusSumStr = ('+' if bonusSum > 0 else '') + str(bonusSum)

            outputStr = "%3s %-10s %-30s %6s" % (bonusSumStr, p.name(), znakStr, houseStr)

            if include_bonuses != INCLUDE_BONUSES.NONE:
                outputStr += '   # %s ' % allBonuses
            #if include_bonuses == INCLUDE_BONUSES.ASC_INDEPENDENT_ONLY:
            #    outputStr = '[!ASC] ' + outputStr
            print(outputStr)


def runHoroscope(input_filename, incl_bonuses=0, import_raw=False):
    hor = Horoscope()

    if import_raw:
        with open(input_filename, "rt", encoding='utf8') as horoscope_file:
            for line in horoscope_file:
                hor.parseRaw(line)

    else: # parse preformatted file
        with open(input_filename, "rt", encoding='utf8') as horoscope_file:
            for line in horoscope_file:
                hor.parseLine(line)

    hor.calcHouses()
    hor.findAspects()
    hor.calcNatals()

    hor.printoutPlanets(incl_bonuses)

    if import_raw:
        output_filename = input_filename.split('.')[0] + '.EXP.txt'
        with open(output_filename, "wt", encoding='utf8') as output_file:
            hor.exportFile(output_file)

    return hor


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

    IMPORT_RAW = False  # True
    INCL_BONUSES = INCLUDE_BONUSES.ALL  # NONE
    #INCL_BONUSES = INCLUDE_BONUSES.ASC_INDEPENDENT_ONLY
    INPUT_FILENAME = "data/_example.txt"
    #INPUT_FILENAME = "data/D.txt"
    #INPUT_FILENAME = data/NT-0630.txt"
    #INPUT_FILENAME = "data/SB-0550-raw.txt"

    hor = runHoroscope(INPUT_FILENAME, incl_bonuses=INCL_BONUSES, import_raw=IMPORT_RAW)
