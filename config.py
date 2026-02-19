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

