import logging

import numpy as np
import os
import time
# need zhinst package
import zhinst.utils
import textwrap
from qulab import BaseDriver, QInteger, QOption, QReal, QString, QVector


logger = logging.getLogger('qulab.drivers.ZI')


class Driver(BaseDriver):
    support_models = ['HDAWG', ]
    quants = [
        QReal('Sample Rate', unit='S/s',
          set_cmd='SOUR:FREQ %(value)f',
          get_cmd='SOUR:FREQ?'),

        QOption('Run Mode', set_cmd='AWGC:RMOD %(option)s', get_cmd='AWGC:RMOD?',
            options = [
                ('Continuous', 'CONT'),
                ('Triggered',  'TRIG'),
                ('Gated',      'GAT'),
                ('Sequence',   'SEQ')]),

        QOption('Clock Source', set_cmd='AWGC:CLOC:SOUR %(option)s', get_cmd='AWGC:CLOC:SOUR?',
          options = [('Internal', 'INT'), ('External', 'EXT')]),

        QOption('Reference Source', set_cmd='SOUR:ROSC:SOUR %(option)s', get_cmd='SOUR:ROSC:SOUR?',
          options = [('Internal', 'INT'), ('External', 'EXT')]),

        QReal('Vpp', unit='V', ch=1,
          set_cmd='SOUR%(ch)d:VOLT %(value)f',
          get_cmd='SOUR%(ch)d:VOLT?'),

        QReal('Amplitude', unit='V', ch=1,),
          # set_cmd='SOUR%(ch)d:VOLT %(value)f',
          # get_cmd='SOUR%(ch)d:VOLT?'),

        QReal('Offset', unit='V', ch=0),
        #set_cmd='/dev8018/sigouts/%(ch)d/offset, %(value)f',
        #get_cmd='SOUR%(ch)d:VOLT?'),

        QReal('Volt Low', unit='V', ch=1,
          set_cmd='SOUR%(ch)d:VOLT:LOW %(value)f',
          get_cmd='SOUR%(ch)d:VOLT:LOW?'),

        QReal('Volt High', unit='V', ch=1,
          set_cmd='SOUR%(ch)d:VOLT:HIGH %(value)f',
          get_cmd='SOUR%(ch)d:VOLT:HIGH?'),
        # output delay in time
        QReal('timeDelay', unit='s', ch=1,
          set_cmd='SOUR%(ch)d:DEL:ADJ %(value)f%(unit)s',
          get_cmd='SOUR%(ch)d:DEL:ADJ?'),
        # output delay in point
        QReal('pointDelay', unit='point', ch=1,
          set_cmd='SOUR%(ch)d:DEL:POIN %(value)d',
          get_cmd='SOUR%(ch)d:DEL:POIN?'),
        QVector('waveform1',value=np.zeros(100),ch =1),
        QVector('waveform2',value=np.zeros(100),ch=2),
        QOption('Output', value = 'ch1',
            options = [('ch1', 0),
                ('ch2',  1),
                ('ch3',  2),
                ('ch4',  3),
                ('ch5',  4),
                ('ch6',  5),
                ('ch7',  6),
                ('ch8',  7)]),
        QOption('Off', value = 'ch1',
            options = [('ch1', 0),
                ('ch2',  1),
                ('ch3',  2),
                ('ch4',  3),
                ('ch5',  4),
                ('ch6',  5),
                ('ch7',  6),
                ('ch8',  7)]),
        # QOption('AWG1', value = 'enable',
        #     options = [('enable', 1),
        #         ('disable', 0)]),
        # QOption('AWG2', value = 'enable',
        #     options = [('enable', 1),
        #         ('disable', 0)]),
        # QOption('AWG3', value = 'enable',
        #     options = [('enable', 1),
        #         ('disable', 0)]),
        # QOption('AWG4', value = 'enable',
        #     options = [('enable', 1),
        #         ('disable', 0)]),
    ]
    def __init__(self, **kw):
        BaseDriver.__init__(self, **kw)
        self.deviceID=kw['deviceID']

    def performOpen(self):
        # self.daq = zhinst.utils.autoConnect()
        apilevel = 6  # The API level supported by this example.
        # Call a zhinst utility function that returns:
        # - an API session `daq` in order to communicate with devices via the data server.
        # - the device ID string that specifies the device branch in the server's node hierarchy.
        # - the device's discovery properties.
        (daq, device, props) = zhinst.utils.create_api_session(self.deviceID, apilevel)
        zhinst.utils.api_server_version_check(daq)
        self.daq = daq
        self.device = device
        self.props = props
        self.awgModule = self.daq.awgModule()
        # 'system/awg/channelgrouping' : Configure how many independent sequencers
        #   should run on the AWG and how the outputs are grouped by sequencer.
        #   0 : 4x2 with HDAWG8; 2x2 with HDAWG4.
        #   1 : 2x4 with HDAWG8; 1x4 with HDAWG4.
        #   2 : 1x8 with HDAWG8.
        # Configure the HDAWG to use one sequencer with the same waveform on all output channels.
        self.daq.setInt('/{}/system/awg/channelgrouping'.format(self.device), 0)
        self.awgs = {'1':_subAwg(1),'2':_subAwg(2),'3':_subAwg(3),'4':_subAwg(4)}
        #self.awg1 = _subAwg(1)
        self.configTrig()

    def outputSequence(self,ch=1,ch2=0,**kw):
        if ch ==1 or ch == 2:
            awg = self.awgs['1']
            #self.setValue('AWGseq','seq1')
        elif ch == 3 or ch == 4:
            awg = self.awgs['2']
        elif ch == 5 or ch == 6:
            awg = self.awgs['3']
        elif ch == 7 or ch == 8:
            awg = self.awgs['4']
        else:
            errors('Channel is not correct.')
        # awg_program = textwrap.dedent("""\
        #     const marker_pos = 50;
        #     wave w_wave = vect(_wave_);
        #     wave w_left = marker(marker_pos, 0);
        #     wave w_right = marker(8000-marker_pos, 1);
        #     wave w_marker = join(w_left, w_right);
        #     wave w_gauss_marker = w_wave + w_marker;
        #     const amplitude = 1;
        #     while(1){
        #         waitDigTrigger(1);
        #     playWave(_ch_,amplitude* w_gauss_marker);}
        #     """)
        # #print(awg_program)
        # awg_program = awg_program.replace('_wave_', ','.join([str(x) for x in waveVector]))
        # #awg_program = awg_program.replace('_ch_', str(ch))
        #awg_program = self.outputWave()
        awg_program = textwrap.dedent("""\
            const marker_pos = 00;
            wave w_wave = vect(_wave_);
            wave w_wave2 = vect(_wave2_);
            //wave w_left = marker(marker_pos, 0);
            //wave w_right = marker(8000-marker_pos, 1);
            //wave w_marker = join(w_left, w_right);
            //wave w_gauss1_marker = w_wave1 + w_marker;
            //wave w_gauss2_marker = w_wave2 + w_marker;
            const amplitude = 1;
            while(1){
                waitDigTrigger(1);
                waitWave();
                playWave(1,amplitude* w_wave,2,amplitude* w_wave2);}
            """)
        awg_program = awg_program.replace('_wave_', ','.join([str(x) for x in self.getValue('waveform1')]))
        awg_program = awg_program.replace('_wave2_', ','.join([str(x) for x in self.getValue('waveform2')]))
        #
        awgModule = self.daq.awgModule()
        awgModule.set('awgModule/device', self.device)
        awgModule.execute()
        self.daq.sync()
        #The AWG that the sequence program will be uploaded to.
        awgModule.set('awgModule/index', int(awg.SeqIndex))
        #self.enableSeq(awg)
        # Transfer the AWG sequence program. Compilation starts automatically.
        awgModule.set('awgModule/compiler/sourcestring', awg_program)
        # Note: when using an AWG program from a source file (and only the
        #print(awg_program)
        while awgModule.getInt('awgModule/compiler/status') == -1:
            time.sleep(0.1)
        if awgModule.getInt('awgModule/compiler/status') == 1:
        # compilation failed, raise an exception
            raise Exception(awgModule.getString('awgModule/compiler/statusstring'))
        else:
            if awgModule.getInt('awgModule/compiler/status') == 0:
                print("Compilation successful with no warnings, will upload the program to the instrument.")
            if awgModule.getInt('awgModule/compiler/status') == 2:
                print("Compilation successful with warnings, will upload the program to the instrument.")
                print("Compiler warning: ", awgModule.getString('awgModule/compiler/statusstring'))
    # wait for waveform upload to finish
            i = 0
            while awgModule.getDouble('awgModule/progress') < 1.0:
                print("{} awgModule/progress: {}".format(i, awgModule.getDouble('awgModule/progress')))
                time.sleep(0.1)
                i += 1
            print("{} awgModule/progress: {}".format(i, awgModule.getDouble('awgModule/progress')))
        print("Finished.")
        #self.daq.setInt('/'+self.device+'/awgs/'+str(seqNum)+'/enable', 1)
        self.enableAwg(awg)
        self.daq.sync()
        self.daq.setInt('/'+self.device+'/sigouts/'+str(ch-1)+'/on', 1)
        if ch2 == 0:
            pass
        else:
            self.daq.setInt('/'+self.device+'/sigouts/'+str(ch2-1)+'/on', 1)

    def performSetValue(self, quant, value, ch=1,**kw):
        _cfg={}
        if quant.name == 'Offset':
            cmd = [['/%s/sigouts/%d/offset' %(self.deviceID,ch),value],]
            self.daq.set(cmd)
        elif quant.name == 'Amplitude':
            awg = int((ch+1)/2-1)
            awgch = int(ch-2*awg-1)
            cmd = '/%s/awgs/%d/outputs/%d/amplitude' %(self.deviceID,awg,awgch)
            #cmd = '/%s/awgs/0/outputs/%d/amplitude' %(self.deviceID,ch-1)
            self.daq.setDouble(cmd,value)
        elif quant.name == 'waveform1':
            BaseDriver.performSetValue(self, quant, value, **kw)
        elif quant.name == 'waveform2':
            quant.value = value
        elif quant.name == 'Output':
            quant.setValue(quant,value)
            options=dict(quant.options)
            self.daq.setInt('/'+self.device+'/sigouts/'+str(options[value])+'/on', 1)
        elif quant.name == 'Off':
            quant.setValue(quant,value)
            options=dict(quant.options)
            self.daq.setInt('/'+self.device+'/sigouts/'+str(options[value])+'/on', 0)
        elif quant.name == 'AWGseq':
            quant.setValue(quant,value)
            options=dict(quant.options)
            #self.daq.setInt('/'+self.device+'/awgs/'+str(options[value])+'/auxtriggers/0/slope', 1)
            #self.awgModule.set('awgModule/index', options[value])
        elif quant.name in ['AWG1','AWG2','AWG3','AWG4']:
            quant.setValue(quant,value)
            options=dict(quant.options)
            self.daq.setInt('/'+self.device+'/awgs/'+str(self.awgs[awg])+'/enable', 1)
            self.daq.setInt('/'+self.device+'/sigouts/'+str(options[value])+'/on', 1)

    def enableAwg(self,awg):
        self.daq.setInt('/'+self.device+'/awgs/'+str(awg.SeqIndex)+'/enable', 1)

    def disableAwg(self,awg):
        self.daq.setInt('/'+self.device+'/awgs/'+str(awg.SeqIndex)+'/enable', 0)

    def triggerAwgs(self,awg,slope=1,**kw):
        self.daq.setInt('/'+self.device+'/awgs/'+str(self.awgs[str(awg)].SeqIndex)+'/auxtriggers/'+str(self.awgs[str(awg)].DigTrigger1)+'/slope', slope)
        self.daq.setInt('/'+self.device+'/awgs/'+str(self.awgs[str(awg)].SeqIndex)+'/auxtriggers/'+str(self.awgs[str(awg)].DigTrigger2)+'/slope', slope)

    def triggerSource(self,awg,sourCh=0):
        self.daq.setInt('/'+self.device+'/awgs/'+str(self.awgs[str(awg)].SeqIndex)+'/auxtriggers/'+str(self.awgs[str(awg)].DigTrigger1)+'/channel', sourCh)
        self.daq.setInt('/'+self.device+'/awgs/'+str(self.awgs[str(awg)].SeqIndex)+'/auxtriggers/'+str(self.awgs[str(awg)].DigTrigger2)+'/channel', sourCh)

    def configTrig(self):
        for awg in [1,2,3,4]:
            self.triggerAwgs(awg,slope = 1)
            self.triggerSource(awg,0)

    def performGetValue(self, quant, **kw):
        # return quant.getValue(**kw)
        if quant.name == 'waveform1':
            return quant.getValue(quant)
        elif quant.name == 'waveform2':
            return quant.getValue(quant)

    def load_settings(self, filename):
        if os.path.isabs(filename):
            zhinst.utils.load_settings(self.daq, self.device, filename)
        else:
            path_default=zhinst.utils.get_default_settings_path(self.daq)
            filename=os.path.normpath(os.path.join(path_default,filename))
            zhinst.utils.load_settings(self.daq, self.device, filename)
        time.sleeo(0.5)
        self.daq.sync()

    def save_settings(self, filename):
        if os.path.isabs(filename):
            zhinst.utils.save_settings(self.daq, self.device, filename)
        else:
            path_default=zhinst.utils.get_default_settings_path(self.daq)
            filename=os.path.normpath(os.path.join(path_default,filename))
            dir=os.path.dirname(filename)
            if not os.path.exists(dir):
                os.makedirs(dir)
            zhinst.utils.save_settings(self.daq, self.device, filename)

    def disable_everything(self):
        zhinst.utils.disable_everything(self.daq, self.device)

    def config_sequence(self):
        # 'system/awg/channelgrouping' : Configure how many independent sequencers
        #   should run on the AWG and how the outputs are grouped by sequencer.
        #   0 : 4x2 with HDAWG8; 2x2 with HDAWG4.
        #   1 : 2x4 with HDAWG8; 1x4 with HDAWG4.
        #   2 : 1x8 with HDAWG8.
        # Configure the HDAWG to use one sequencer with the same waveform on all output channels.
        self.daq.setInt('/{}/system/awg/channelgrouping'.format(self.device), 1)

    def dataaq(self):
        pass
class _subAwg():
    def __init__(self,ID,**kw):
        #BaseDriver.__init__(self, **kw)
        #self.deviceID = deviceID
        self.awgID= int(ID)
        self.waveform1 = np.zeros(100)
        self.waveform2 = np.zeros(100)
        self.SeqIndex = int(ID-1)
        self.DigTrigger1 = 0
        self.DigTrigger2 = 1
