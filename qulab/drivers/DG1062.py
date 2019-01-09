# -*- coding: utf-8 -*-
import time

import numpy as np

from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


class Driver(BaseDriver):
    error_command = '*ESR?'
    support_models = ['DG1062Z']

    quants = [
        QReal('Frequency', unit='Hz',
          set_cmd='FREQ %(value).11E %(unit)s',
          get_cmd='FREQ?'),
        QReal('Vpp', ch=1,
          set_cmd=':SOUR%(ch)d:VOLT:AMPL %(value)f',
          get_cmd='SOUR%(ch)d:VOLT:AMPL?'),
        QReal('Offset',ch = 1,
          set_cmd='SOUR%(ch)d:VOLT:OFFS %(value)f',
          get_cmd='SOUR%(ch)d:VOLT:OFFS?'),
        QVector('Waveform', unit='V'),
        QString('Trigger',
          set_cmd='TRIG:SOUR %(value)s',
          get_cmd='TRIG:SOUR?')
    ]


    def performGetValue(self, quant, **kw):
        get_Delays = ['T0 Length','AB Delay','AB Length','A Delay','B Delay',
            'CD Delay','CD Length','C Delay','D Delay',
            'EF Delay','EF Length','E Delay','F Delay',
            'GH Delay','GH Length','G Delay','H Delay'
        ]
        if quant.name in get_Delays and quant.get_cmd is not '':
            cmd = quant._formatGetCmd(**kw)
            res = self.query_ascii_values(cmd)
            quant.value= res[1]
            return res[0],quant.value*1e6 # res[0] is the chanel that related ; quant.value : 's' convert to 'us'
        else:
            return super(Driver, self).performGetValue(quant, **kw)

    def performSetValue(self, quant,value, **kw):
        set_Delays = ['T0 Length','AB Delay','AB Length','A Delay','B Delay',
            'CD Delay','CD Length','C Delay','D Delay',
            'EF Delay','EF Length','E Delay','F Delay',
            'GH Delay','GH Length','G Delay','H Delay'
        ]
        if quant.name in set_Delays and quant.set_cmd is not '':
            value=value/1e6  # 'us' convert to 's'
            quant.value = value
            cmd = quant._formatSetCmd(value,**kw)
            self.write(cmd)
        else:
            return super(Driver, self).performSetValue(quant,value, **kw)
