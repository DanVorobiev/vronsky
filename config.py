#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
from pprint import pprint as pretty
from dataclasses import dataclass

from const import *


@dataclass
class AliasConfig:
    ALIASES_ZNAK: dict
    ALIASES_PLANET: dict
    ALIASES_ASPECT: dict
    ALIASES_GENDER: dict
    ALIASES_DOMAIN: dict

@dataclass
class VronskyTableConfig:
    MAJOR_ASPECT_ORBIS: dict
    AVG_PLANET_SPD: dict
    CARDINAL_FIXED_MUTABLE_BONUS_RANGE: list
    ZNAK_DOMINANTS: dict
    PLANET_ATTRS: dict
    BONUS_POINTS: dict
    WEEKDAY_DOMINANTS: dict
    YEAR_DOMINANTS: dict
    BONUS_GRADUS: dict
    PLANET_MASKS: dict
    BONUS_ASPECTS: list
    HOUSE_THIRD_POINTS: dict
    BONUS_TERMY: dict
    OWN_GRADUS: dict
    DAY_HOUR_OWNER: dict
    NIGHT_HOUR_OWNER: dict
    PLANET_GRADUS_BONUSES: dict
    ASPECT_WEIGHT: dict
    PLANET_WEIGHT: dict
    ASPECT_COEFFS: dict

@dataclass
class PlanetAttrs:
    gender: int
    stihia: int
    is_evil: bool
    exalt_gradus: float  # OVEN:20*

@dataclass
class BonusAspect:
    planet_mask: list
    aspect: int
    to_planets: list
    from_orbis: float
    to_orbis: float
    bonus_type: str
    bonus_points: int

class Config:
    NAME_2_PLANET = {}  # {"Солнце": SOL}
    PLANET_2_NAME = {}  # {SOL: "Солнце"}
    NAME_2_ZNAK = {}  # {"Овен": OVEN(0)}
    ZNAK_2_NAME = {}  # {OVEN(0): "Овен"}
    NAME_2_ASPECT = {}  # {"трин": 120}
    ASPECT_2_NAME = {}  # {120: "трин"}
    MAJOR_ORBS = {}  # {SOL: {LUNA: orbis(float)}}
    AVG_SPD = {}  # {SOL: gradus(float)}
    ZNAK_BONUS_RANGES = {}  # {OVEN: [(0, 12.51), (25.43, 30.0)]}, all cardinal/fixed/mutable bonus arcs.
    ZNAK_ROLES = {}  # {OVEN: {SOL: EXALTATION}}
    PLANET_ZNAK_ROLES = {}  # {SOL: {OVEN: EXALTATION}}
    NAME_2_GENDER = {}  # {"м": MALE(0)}
    GENDER_2_NAME = {}  # {MALE: "м"}
    NAME_2_STIHIA = {}  # {"огонь": FIRE(0)}
    STIHIA_2_NAME = {}  # {FIRE: "огонь"}
    PLANET_ATTRS = {}  # {SOL: PlanetAttrs}
    BONUS_POINTS = {}  # {BONUS.NAME: +/-value}
    WEEKDAY_DOMINANTS = {}  # {(weekday % 7): planet}
    YEAR_DOMINANTS = {}  # {(year % 7): planet}
    BONUS_GRADUS = {}
    NAME_2_PLANET_MASK = {}
    BONUS_ASPECTS = []
    HOUSE_THIRD_POINTS = {}
    BONUS_TERMY = {}
    OWN_GRADUS = {}
    DAY_HOUR_OWNER = {}
    NIGHT_HOUR_OWNER = {}
    PLANET_GRADUS_BONUSES = {}
    ASPECT_WEIGHT = {}
    PLANET_WEIGHT = {}
    ASPECT_COEFFS = {}

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
            cls.NAME_2_ASPECT[ru_key] = val = getattr(ASPECT, name)
            cls.ASPECT_2_NAME[val] = ru_key
        for ru_key, name in aliasCfg.ALIASES_GENDER.items():
            val = getattr(GENDER, name)
            cls.NAME_2_GENDER[ru_key] = val
            cls.GENDER_2_NAME[val] = ru_key
        for ru_key, name in aliasCfg.ALIASES_DOMAIN.items():
            val = getattr(STIHIA, name)
            cls.NAME_2_STIHIA[ru_key] = val
            cls.STIHIA_2_NAME[val] = ru_key

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
                if verbose: print(znak_type_, cls.ZNAK_2_NAME[znak], cls.ZNAK_BONUS_RANGES[znak])

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

        for planet_name, attrs in vronskyCfg.PLANET_ATTRS.items():
            if verbose: print("PLANET_ATTRS %s %s" % (planet_name, attrs))
            planet_id = cls.NAME_2_PLANET[planet_name]
            gender = cls.NAME_2_GENDER[attrs.get('пол', GENDER.NEUTRAL)]
            stihia = cls.NAME_2_STIHIA[attrs.get('стихия', STIHIA.NONE)]
            is_evil = bool(attrs.get('зловред'))
            znak_, gradus = attrs.get('exalt_gradus', (None, BAD_GRADUS))
            exalt_gradus = absGradus(cls.NAME_2_ZNAK[znak_], gradus) if znak_ is not None else BAD_GRADUS
            planet_attrs = PlanetAttrs(gender=gender, stihia=stihia, is_evil=is_evil, exalt_gradus=exalt_gradus)
            cls.PLANET_ATTRS[planet_id] = planet_attrs

        cls.BONUS_POINTS = vronskyCfg.BONUS_POINTS

        # {(weekday % 7): planet}
        # i.e. {0: MOON}
        cls.WEEKDAY_DOMINANTS = {k:cls.NAME_2_PLANET[v] for k, v in vronskyCfg.WEEKDAY_DOMINANTS.items()}
        if verbose: pretty(['WEEKDAY_DOMINANTS', cls.WEEKDAY_DOMINANTS])

        # {(year % 7): planet}
        cls.YEAR_DOMINANTS = {(y % 7):cls.NAME_2_PLANET[v] for y, v in vronskyCfg.YEAR_DOMINANTS.items()}
        if verbose: pretty(['YEAR_DOMINANTS', cls.YEAR_DOMINANTS])

        # BONUS_GRADUS
        cls.BONUS_GRADUS = {}
        for bonus_key, range_pairs in vronskyCfg.BONUS_GRADUS.items():
            (znak1_, gradus1_), (znak2_, gradus2_) = range_pairs
            znak1, znak2 = cls.NAME_2_ZNAK[znak1_], cls.NAME_2_ZNAK[znak2_]
            gradus1, gradus2 = cls.parse_gradus(gradus1_), cls.parse_gradus(gradus2_)
            assert getattr(BONUS, bonus_key)
            cls.BONUS_GRADUS[bonus_key] = (absGradus(znak1, gradus1), absGradus(znak2, gradus2))
        if verbose: pretty(['cfg.BONUS_GRADUS', vronskyCfg.BONUS_GRADUS])
        if verbose: pretty(['BONUS_GRADUS', cls.BONUS_GRADUS])

        cls.NAME_2_PLANET_MASK = {}
        for ru_key, mask_name in vronskyCfg.PLANET_MASKS.items():
            planet_set = getattr(PLANET_MASK, mask_name)
            cls.NAME_2_PLANET_MASK[ru_key] = planet_set
        if verbose: pretty(['cfg.PLANET_MASKS', vronskyCfg.PLANET_MASKS])
        if verbose: pretty(['NAME_2_PLANET_MASK', cls.NAME_2_PLANET_MASK])

        cls.BONUS_ASPECTS = []
        for (mask_, planet_, aspect_, from_, to_, bonus_points) in vronskyCfg.BONUS_ASPECTS:
            if verbose: print('BONUS_ASPECT:', (mask_, aspect_, planet_, from_, to_, bonus_points))
            mask = cls.NAME_2_PLANET_MASK.get(mask_)
            aspect = cls.NAME_2_ASPECT.get(aspect_)
            pid = cls.NAME_2_PLANET.get(planet_)
            from_orbis = -1 if (from_ == '-') else cls.parse_gradus(from_)
            to_orbis = -1 if (from_ == '-') else cls.parse_gradus(to_)
            bonus_type = "%s(%s)" % (aspect_, planet_[:3])
            cls.BONUS_ASPECTS.append(BonusAspect(
                planet_mask=mask, aspect=aspect, to_planets=[pid, pid ^ PLANET._RETRO],
                from_orbis=from_orbis, to_orbis=to_orbis, bonus_type=bonus_type, bonus_points=bonus_points
            ))
        if verbose: pretty(['cfg.BONUS_ASPECTS', vronskyCfg.BONUS_ASPECTS])
        if verbose: pretty(['BONUS_ASPECTS', cls.BONUS_ASPECTS])

        for planet_, house_points in vronskyCfg.HOUSE_THIRD_POINTS.items():
            pid = cls.NAME_2_PLANET.get(planet_)
            cls.HOUSE_THIRD_POINTS[pid] = house_points

        for planet_, termy_ in vronskyCfg.BONUS_TERMY.items():
            pid = cls.NAME_2_PLANET.get(planet_)
            planet_termy = cls.BONUS_TERMY.setdefault(pid, {})
            for znak_, (gradus1, gradus2, bonus_points) in termy_.items():
                znak = cls.NAME_2_ZNAK.get(znak_)
                planet_termy[znak] = (absGradus(znak, gradus1), absGradus(znak, gradus2), bonus_points)
        if verbose: pretty(['BONUS_TERMY', cls.BONUS_TERMY])

        for znak_, gradus_planets in vronskyCfg.OWN_GRADUS.items():
            znak = cls.NAME_2_ZNAK.get(znak_)
            cls.OWN_GRADUS[znak] = fill_dict = {}
            for gradus, planets_ in gradus_planets.items():
                fill_dict[gradus] = set([cls.NAME_2_PLANET[planet_] for planet_ in planets_])
            # NB(!): только градусы 0-6 заполнены в табличке, см. is_own_gradus_dominant(), там берем % 7
            if verbose: pretty(['OWN_GRADUS', cls.OWN_GRADUS])

        for weekday, planets_ in vronskyCfg.DAY_HOUR_OWNER.items():
            cls.DAY_HOUR_OWNER[weekday] = [cls.NAME_2_PLANET[p] for p in planets_]
        for weekday, planets_ in vronskyCfg.NIGHT_HOUR_OWNER.items():
            cls.NIGHT_HOUR_OWNER[weekday] = [cls.NAME_2_PLANET[p] for p in planets_]
        if verbose: pretty(['DAY_HOUR_OWNER', cls.DAY_HOUR_OWNER])
        if verbose: pretty(['NIGHT_HOUR_OWNER', cls.NIGHT_HOUR_OWNER])

        for planet_, planet_graduses_ in vronskyCfg.PLANET_GRADUS_BONUSES.items():
            pid = cls.NAME_2_PLANET.get(planet_)
            planet_graduses = cls.PLANET_GRADUS_BONUSES.setdefault(pid, {})
            for znak_, gradus_array in planet_graduses_.items():
                znak = cls.NAME_2_ZNAK.get(znak_)
                planet_graduses[znak] = gradus_array
                assert(len(gradus_array) == 30)
            assert (len(planet_graduses) == 12)
        # нужно продублировать таблицы градусов по списку:
        DUPLICATE_TABLES = [
            (PLANET.MERCURY, PLANET.MERCURY_RETRO),  # для Меркурия одна таблица (вне зависимости от ретроградности)
            (PLANET.VENERA, PLANET.VENERA_RETRO),  # для Венеры одна таблица (вне зависимости от ретроградности)
            (PLANET.MARS, PLANET.MARS_RETRO),   # для Марса одна таблица (вне зависимости от ретроградности)
            (PLANET.MARS, PLANET.PLUTON_RETRO),  # Марс + Плутон-R
            (PLANET.MARS, PLANET.PLUTON),  # для обычного Плутона нет таблицы, видимо та же что для Плутона-R?
            (PLANET.JUPITER, PLANET.NEPTUN_RETRO),  # Юпитер + Нептун-R
            (PLANET.SATURN, PLANET.URAN_RETRO),  # Сатурн + Уран-R
            (PLANET.NEPTUN, PLANET.JUPITER_RETRO),  # Нептун + Юпитер-R
            (PLANET.URAN, PLANET.SATURN_RETRO),  # Уран + Сатурн-R
        ]
        for tbl_from, tbl_to in DUPLICATE_TABLES:
            cls.PLANET_GRADUS_BONUSES[tbl_to] = cls.PLANET_GRADUS_BONUSES[tbl_from]
        if verbose: pretty(['PLANET_GRADUS_BONUSES keys:', cls.PLANET_GRADUS_BONUSES.keys()])

        for planet_, planet_weight in vronskyCfg.PLANET_WEIGHT.items():
            pid = cls.NAME_2_PLANET.get(planet_)
            cls.PLANET_WEIGHT[pid] = planet_weight
        #if verbose:
        pretty(['PLANET_WEIGHT:', cls.PLANET_WEIGHT])

        for aspect_, aspect_weight in vronskyCfg.ASPECT_WEIGHT.items():
            aid = cls.NAME_2_ASPECT.get(aspect_)
            cls.ASPECT_WEIGHT[aid] = aspect_weight
        #if verbose:
        pretty(['ASPECT_WEIGHT:', cls.PLANET_WEIGHT])

        cls.ASPECT_COEFFS = vronskyCfg.ASPECT_COEFFS

    @classmethod
    def get_year_dominant(self, year):
        return self.YEAR_DOMINANTS[year % 7]

    @classmethod
    def get_weekday_dominant(self, weekday):
        return self.WEEKDAY_DOMINANTS[weekday % 7]

    @classmethod
    def make_planet_args(self, planet_, znak_, gradus_):
        planet = self.NAME_2_PLANET.get(planet_)
        znak = self.NAME_2_ZNAK.get(znak_)
        gradus = self.parse_gradus(gradus_)
        if (planet is not None) and (znak is not None) and (gradus is not None):
            return planet, znak, gradus
        err = "BAD can_make_planet: %s, %s, %s" % (planet, znak, gradus)
        print(err)
        raise BaseException(err)
        return None, None, None

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


ALIAS_CFG = None
VRONSKY_CFG = None


def init():
    global ALIAS_CFG
    global VRONSKY_CFG

    with open("aliases.yaml", encoding='utf8') as cfg_file:
        ALIAS_CFG = AliasConfig(**yaml.safe_load(cfg_file))
    if verbose: print(f"ALIAS_CFG: '{ALIAS_CFG}'")

    with open("vronsky_tables.yaml", encoding='utf8') as cfg_file:
        VRONSKY_CFG = VronskyTableConfig(**yaml.safe_load(cfg_file))
    if verbose:
        print(f"VRONSKY_CFG: '{VRONSKY_CFG}'")
        pretty(VRONSKY_CFG.ZNAK_DOMINANTS)

