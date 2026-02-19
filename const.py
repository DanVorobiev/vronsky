#!/usr/bin/env python3
# -*- coding: utf-8 -*-

verbose = False
#verbose = True

PREV_TAG = "PREV"


class GENDER:
    NEUTRAL = -1
    MALE = 0
    FEMALE = 1


class STIHIA:
    NONE = -1
    FIRE = 0
    EARTH = 1
    AIR = 2
    WATER = 3


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

    @staticmethod
    def _gender(znak):
        return (znak % 2)  # 0: GENDER.MALE, 1: GENDER.FEMALE

    @staticmethod
    def _stihia(znak):
        return (znak % 4)  # 0: FIRE, 1: EARTH, 2: AIR, 3: WATER


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

    _MERCURIES = {MERCURY, MERCURY_RETRO}
    _ANY_EVIL = {MARS, MARS_RETRO, SATURN, SATURN_RETRO, URAN, URAN_RETRO, PLUTON, PLUTON_RETRO}

PLANET_ALL = [k for k in PLANET.__dict__.keys() if not k.startswith('_')]


class PLANET_MASK:
    MERCURIES = PLANET._MERCURIES
    ANY_EVIL = PLANET._ANY_EVIL
    ANY = {v for k, v in PLANET.__dict__.items() if not k.startswith('_')}
    ANY_GOOD = ANY - ANY_EVIL
    ANY_GOOD_EXCEPT_MERC = ANY_GOOD - MERCURIES


class ASPECT:
    CON = 0
    POLU_SEXT = 30
    SEXT = 60
    QUAD = 90
    TRIN = 120
    KVINK = 150
    OPP = 180

    _OCTIL = 45
    _SESQUIQ = 135

    _MINORS = [POLU_SEXT, KVINK, _OCTIL, _SESQUIQ]

ASPECT_ALL = [k for k in ASPECT.__dict__.keys() if not k.startswith('_')]
ASPECT_VALUES = [v for k,v in ASPECT.__dict__.items() if not k.startswith('_')]

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

ROLE_KEYS = {v:k for k, v in ROLE.__dict__.items() if not k.startswith('_')}


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


def newline():
    print('---')


def hasGradus(token):
    return token.find('*') > 0 or token.find('°') > 0


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
    YEAR_DOMINANT = 'дом.года'
    WEEKDAY_DOMINANT = 'дом.дня'
    ASC_DOMINANT = 'дом.ASC'
    MC_DOMINANT = 'дом.MC'
    RETRO = 'ретро'
    LEV_GRADUS = '25*30*Лев'
    VESY_GRADUS = '18*25*Весы'
    TELEC_GRADUS = '22*26*Тел'
    KOMBUSTA = 'комбуста'

    _ZNAK_BONUS_TYPES = (CARDINAL_ZNAK, MUTABLE_ZNAK, FIXED_ZNAK)
    _HOUSE_ROLES = (DOMICILE, EXALTATION, EXILE, FALL)


