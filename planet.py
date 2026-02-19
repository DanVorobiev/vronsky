#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from const import *
from config import Config


class BONUS:
    SPEED = 'spd'
    CARDINAL_ZNAK = 'кард'
    FIXED_ZNAK = 'фикс'
    MUTABLE_ZNAK = 'мутаб'
    GENDER = 'пол'
    STIHIA = 'стихия'  # в знаке своего стихийного тригона (напр. огонь для Солнца/Марса/Юпитера)
    OWN_HOUSE = 'свой.дом'  # в своём поле (default доме, считая от равноденствия - напр. Марс в I доме = Овен (управ.Марс)
    DOMICILE = 'домицил'
    EXALTATION = 'экзальт'
    EXILE = 'эксиль'
    FALL = 'фалл'

    _ZNAK_BONUS_TYPES = (CARDINAL_ZNAK, MUTABLE_ZNAK, FIXED_ZNAK)
    _HOUSE_ROLES = (DOMICILE, EXALTATION, EXILE, FALL)


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

        self.bonuses = {}  # {BONUS.SPEED: +2}

    @staticmethod
    def get_znak_bonus_type(znak):
        if znak in ZNAK._CARDINAL:
            return BONUS.CARDINAL_ZNAK
        elif znak in ZNAK._FIXED:
            return BONUS.FIXED_ZNAK
        elif znak in ZNAK._MUTABLE:
            return BONUS.MUTABLE_ZNAK

    def set_bonus(self, bonus_type, bonus_value):
        self.bonuses[bonus_type] = bonus_value

    def get_bonus(self, bonus_type):
        return self.bonuses.get(bonus_type)

    def get_bonus_str(self, bonus_types=None):
        s = ''
        if bonus_types is None:
            bonus_types = self.bonuses.keys()
        for bonus in bonus_types:
            val = self.bonuses.get(bonus)
            if val:
                sign = "+" if val > 0 else ''
                s += '%s%s%d, ' % (bonus, sign, val)
        return s[:-2]  # cut trailing  ", "

    def sum_bonuses(self, bonus_types=None):
        s = 0
        if bonus_types is None:
            bonus_types = self.bonuses.keys()
        for bonus in bonus_types:
            s += self.bonuses.get(bonus)
        return s

    def orb(self, planet2):
        return orbz(self.znak, self.gradus, planet2.znak, planet2.gradus)

    def __str__(self):
        s = "Planet(%s, %s, %0.3f, abs=%0.3f" % (
            Config.PLANET_2_NAME.get(self.planet), Config.ZNAK_2_NAME.get(self.znak), self.gradus,
            absGradus(self.znak, self.gradus))
        if self.house is not None:
            s += ', %s дом' % toRoman(self.house)
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
