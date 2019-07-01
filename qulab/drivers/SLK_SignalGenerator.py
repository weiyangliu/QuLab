# -*- coding: utf-8 -*-
import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    support_models = ['SLKS0218F']


    quants = [
        QReal('Frequency', unit='Hz',
          set_cmd='FREQ %(value).13e%(unit)s',
          get_cmd='FREQ?'),

        QReal('Power', unit='dBm',
          set_cmd='LEVEL %(value).8e%(unit)s',
          get_cmd='LEVEL?'),

        QOption('Output',
          set_cmd='LEVEL:STATE %(option)s', options=[('OFF', 'OFF'), ('ON', 'ON')]),
    ]

    def performOpen(self):
        addr = self.addr
        self.instr = open_resource('TCPIP0::192.168.1.'+addr+'::2000::SOCKET')

    def performSetValue(self, quant, value, ch=1,**kw):
        if quant.name == 'Frequency':
            self.instr.write('FREQ %(value) GHz')
        elif quant.name == 'Power':
            self.instr.write('LEVEL %(value) dBm')
        elif quant.name == 'Output':
            self.instr.write('LEVEL:STATE %(value)')
