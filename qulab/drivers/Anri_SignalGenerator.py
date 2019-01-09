# -*- coding: utf-8 -*-
import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['MG3692C']

    quants = [
        QReal('Frequency', unit='Hz',
          set_cmd=':SOUR:FREQ %(value).13e%(unit)s',
          get_cmd=':SOUR:FREQ?'),

        QReal('Power', unit='dBm',
          set_cmd=':POWER %(value).8e%(unit)s',
          get_cmd=':POWER?'),

        QOption('Output',
          set_cmd=':OUTP %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]
