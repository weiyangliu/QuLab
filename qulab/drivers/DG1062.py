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
        # QString('Trigger',
        #   set_cmd='TRIG:SOUR %(value)s',
        #   get_cmd='TRIG:SOUR?'),
        QReal('DCoffset',ch = 1, unit='V',
          set_cmd=':SOUR%(ch)d:APPL:DC 1,1, %(value).8e%(unit)s',
          get_cmd=':VOLT?'),
        QString('BurstTrigger',ch = 1, value = 'TRIG',
          set_cmd=':SOUR%(ch)d:BURS:MODE %(value)s',
          get_cmd=':SOUR%(ch)d:BURS:MODE?'),
        QString('BurstTriggerSour',ch = 1, value = 'EXT',
          set_cmd=':SOUR%(ch)d:BURS:TRIG:SOUR %(value)s',
          get_cmd=':SOUR%(ch)d:BURS:TRIG:SOUR?'),
        QString('BurstTriggerSlop',ch = 1, value = 'POS',
          set_cmd=':SOUR%(ch)d:BURS:TRIG:SLOP %(value)s',
          get_cmd=':SOUR%(ch)d:BURS:TRIG:SLOP?'),
        QReal('BurstN',ch = 1, value = 1,
          set_cmd=':SOUR%(ch)d:BURS:NCYC %(value)d',
          get_cmd=':SOUR%(ch)d:BURS:NCYC?'),
        QString('Burst',ch = 1, value = 'ON',
          set_cmd = ':SOUR%(ch)d:BURS %(value)s',
          get_cmd = ':SOUR%(ch)d:BURS?'),
        QString('Trigger',
          set_cmd='TRIG:SOUR %(value)s',
          get_cmd='TRIG:SOUR?'),
        QString('ArbMode',ch = 1, value='FREQ',
          set_cmd=':SOUR%(ch)d:FUNC:ARB:MODE %(value)s',
          get_cmd=':SOUR%(ch)d:FUNC:ARB:MODE?'),
        QReal('SRATE',ch = 1, value=20e6,
          set_cmd=':SOUR%(ch)d:FUNC:ARB:SRATE %(value)d',
          get_cmd=':SOUR%(ch)d:FUNC:ARB:SRATE?'),
    ]

    def performOpen(self):
        self.write('FORM:BORD NORM')
        self.waveform_list = self.query(':SOUR1:TRAC:DATA:CAT?')[1:-1].split('","')
        self.current_waveform = self.query(':SOUR1FUNC:SHAP?')
        if self.current_waveform == 'USER':
            self.current_waveform = self.query('FUNC:USER?')
        self.arb_waveforms = self.query('DATA:NVOL:CAT?')[1:-1].split('","')
        self.trigger_source = self.query('TRIG:SOUR?')
        self.inner_waveform = ["SINC","NEG_RAMP","EXP_RISE","EXP_FALL","CARDIAC"]

        if self.model == '33120A':
            self.max_waveform_size = 16000
            self.trigger_count  = int(float(self.query('BM:NCYC?')))
        elif self.model == '33220A':
            self.max_waveform_size = 16384
            self.trigger_count  = int(float(self.query("BURS:NCYC?")))
        if self.model == 'DG1062Z':
            self.max_waveform_size = 50000
            self.trigger_count  = int(float(self.query(':SOUR1:BURS:NCYC?')))

    def performConfig(self,ch):
        #Set trigger.
        self.setValue('BurstTrigger','TRIG',ch = ch)
        self.setValue('BurstTriggerSour','EXT',ch = ch)
        self.setValue('BurstTriggerSlop','POS',ch = ch)
        self.setValue('Burst','ON',ch=ch)

    def performArbConfig(self,ch = 1,ArbMode = 'SRAT',SRATE=50e6):
        #Set samplerate.
        self.setValue('ArbMode',Arbmode,ch)
        self.setValue('SRATE',SRATE,ch)


    def performSetValue(self, quant, value, **kw):
        if quant.name == 'Waveform':
            if len(value) > self.max_waveform_size:
                value = value[:self.max_waveform_size]
            value = np.array(value)
            vpp  = value.max() - value.min()
            offs = (value.max() + value.min())/2.0
            if vpp == 0:
                self.DC(offs)
                return
            name = kw['name'] if 'name' in kw.keys() else 'ABS'
            freq = kw['freq'] if 'freq' in kw.keys() else None
            self.update_waveform(2*(value-offs)/vpp, name=name)
            # self.use_waveform(name, vpp=vpp, offs=offs, freq=freq)
            self.use_waveform(name, vpp=vpp, offs=offs, srate=50e6)
        else:
            BaseDriver.performSetValue(self, quant, value, **kw)

    def __del_func(self, name):
        if name in self.arb_waveforms:
            if name == self.current_waveform:
                self.DC(0)
            self.write('DATA:DEL %s' % name)
            self.arb_waveforms.remove(name)
            self.waveform_list.remove(name)

    def update_waveform(self, values, name='ABS',ch=1):
        MAX_PTS=8192
        clip = lambda x: (8192*x).clip(-8192,8192).astype(int)+8192
        values = clip(values)
        for i in range(len(values)//MAX_PTS):
            message = ':SOUR%d:DATA:DAC16 VOLATILE,CON,' % (ch)
            self.write_binary_values(message,values[MAX_PTS*i:MAX_PTS*(i+1)],datatype='h' )
        message2 = ':SOUR%d:DATA:DAC16 VOLATILE,END,' % (ch)
        self.write_binary_values(message2,values[MAX_PTS*(len(values)//MAX_PTS):],datatype='h' )
        # if len(name) > 8:
        #     name = name[:8]
        # name = name.upper()
        #
        # if len(self.arb_waveforms) >= 4:
        #     for wf in self.arb_waveforms:
        #         if wf != self.current_waveform:
        #             self.__del_func(wf)
        #
        # self.write('DATA:COPY %s,VOLATILE' % name)

    def use_waveform(self, name, vpp=None, offs=None, ch=1,srate=50e6):
        # freq_s = ("%.11E" % freq) if freq != None else "DEF"
        vpp_s  = ("%.5E"  % vpp)  if vpp  != None else "DEF"
        offs_s = ("%.5E"  % offs) if offs != None else "DEF"
        name = name.upper()
        if name in self.inner_waveform:
            self.write('APPL:%s %s,%s,%s' % (name, freq_s, vpp_s, offs_s))
        else:
            self.write('FUNC:USER %s' % name)
            self.write(':SOUR%d:APPLy:ARBitrary %s,%s,%s' % (ch, srate, vpp_s, offs_s))
        # if self.trigger_source != 'IMM':
        #     self.set_trigger(source = self.trigger_source,
        #                      count  = self.trigger_count)
        self.current_waveform = name
        time.sleep(1)
