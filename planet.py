#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from const import *
from config import Config


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
