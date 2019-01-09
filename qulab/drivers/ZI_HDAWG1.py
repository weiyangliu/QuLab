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
        QVector('waveform1',value=np.zeros(100),ch=1),
        QVector('waveform2',value=np.zeros(100),ch=2),
        QVector('waveform3',value=np.zeros(100),ch=3),
        QVector('waveform4',value=np.zeros(100),ch=4),
        QVector('waveform5',value=np.zeros(100),ch=5),
        QVector('waveform6',value=np.zeros(100),ch=6),
        QVector('waveform7',value=np.zeros(100),ch=7),
        QVector('waveform8',value=np.zeros(100),ch=8),
        QOption('Output', value = 'ch1',
            options = [('ch1', 0),
                ('ch2',  1),
                ('ch3',  2),
                ('ch4',  3),
                ('ch5',  4),
                ('ch6',  5),
                ('ch6',  6),
                ('ch7',  7)]),
        QOption('Off', value = 'ch1',
            options = [('ch1', 0),
                ('ch2',  1),
                ('ch3',  2),
                ('ch4',  3),
                ('ch5',  4),
                ('ch6',  5),
                ('ch6',  6),
                ('ch7',  7)]),
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
        self.awgModule.set('awgModule/device', self.device)
        self.awgModule.execute()
        # 'system/awg/channelgrouping' : Configure how many independent sequencers
        #   should run on the AWG and how the outputs are grouped by sequencer.
        #   0 : 4x2 with HDAWG8; 2x2 with HDAWG4.
        #   1 : 2x4 with HDAWG8; 1x4 with HDAWG4.
        #   2 : 1x8 with HDAWG8.
        # Configure the HDAWG to use one sequencer with the same waveform on all output channels.
        self.daq.setInt('/{}/system/awg/channelgrouping'.format(self.device), 2)

    def performSetValue(self, quant, value, ch=0,**kw):
        _cfg={}
        if quant.name == 'Offset':
            cmd = [['/%s/sigouts/%d/offset' %(self.deviceID,ch),value],]
            self.daq.set(cmd)
        elif quant.name == 'Amplitude':
            cmd = '/%s/awgs/0/outputs/%d/amplitude' %(self.deviceID,ch)
            self.daq.setDouble(cmd,value)
        elif quant.name == 'waveform1':
            BaseDriver.performSetValue(self, quant, value, **kw)
        elif quant.name == 'waveform2':
            quant.value = value
        elif quant.name == 'waveform3':
            quant.value = value
        elif quant.name == 'waveform4':
            quant.value = value
        elif quant.name == 'waveform5':
            quant.value = value
        elif quant.name == 'waveform6':
            quant.value = value
        elif quant.name == 'waveform7':
            quant.value = value
        elif quant.name == 'waveform8':
            quant.value = value
        elif quant.name == 'Output':
            quant.setValue(quant,value)
            options=dict(quant.options)
            self.daq.setInt('/'+self.device+'/sigouts/'+str(options[value])+'/on', 1)
        elif quant.name == 'Off':
            quant.setValue(quant,value)
            options=dict(quant.options)
            self.daq.setInt('/'+self.device+'/sigouts/'+str(options[value])+'/on', 0)


    def performGetValue(self, quant, **kw):
        # return quant.getValue(**kw)
        if quant.name == 'waveform1':
            return quant.getValue(quant)
        elif quant.name == 'waveform2':
            return quant.getValue(quant)
        elif quant.name == 'waveform3':
            return quant.getValue(quant)
        elif quant.name == 'waveform4':
            return quant.getValue(quant)
        elif quant.name == 'waveform5':
            return quant.getValue(quant)
        elif quant.name == 'waveform6':
            return quant.getValue(quant)
        elif quant.name == 'waveform7':
            return quant.getValue(quant)
        elif quant.name == 'waveform8':
            return quant.getValue(quant)
        return value

    def uploadSequence(self):
        seqNum = 0
        self.daq.setInt('/'+self.device+'/awgs/'+str(seqNum)+'/enable', 0)
        #self.openSequence()
        awg_program = textwrap.dedent("""\
            const marker_pos = 50;
            wave w_wave1 = vect(_wave1_);
            wave w_wave2 = vect(_wave2_);
            wave w_wave3 = vect(_wave3_);
            wave w_wave4 = vect(_wave4_);
            wave w_wave5 = vect(_wave5_);
            wave w_wave6 = vect(_wave6_);
            wave w_wave7 = vect(_wave7_);
            wave w_wave8 = vect(_wave8_);
            //wave w_left = marker(marker_pos, 0);
            //wave w_right = marker(8000-marker_pos, 1);
            //wave w_marker = join(w_left, w_right);
            //wave w_gauss_marker = w_wave + w_marker;
            const amplitude = 1;
            while(1){
                waitDigTrigger(1);
            playWave(1,amplitude* w_wave1,2,amplitude* w_wave2,3,amplitude* w_wave3,4,amplitude* w_wave4,5,amplitude* w_wave5,6,amplitude* w_wave6,7,amplitude* w_wave7,8,amplitude* w_wave8);
                //waitWave();
            }
            """)
        awg_program = awg_program.replace('_wave1_', ','.join([str(x) for x in self.getValue('waveform1')]))
        awg_program = awg_program.replace('_wave2_', ','.join([str(x) for x in self.getValue('waveform2')]))
        awg_program = awg_program.replace('_wave3_', ','.join([str(x) for x in self.getValue('waveform3')]))
        awg_program = awg_program.replace('_wave4_', ','.join([str(x) for x in self.getValue('waveform4')]))
        awg_program = awg_program.replace('_wave5_', ','.join([str(x) for x in self.getValue('waveform5')]))
        awg_program = awg_program.replace('_wave6_', ','.join([str(x) for x in self.getValue('waveform6')]))
        awg_program = awg_program.replace('_wave7_', ','.join([str(x) for x in self.getValue('waveform7')]))
        awg_program = awg_program.replace('_wave8_', ','.join([str(x) for x in self.getValue('waveform8')]))
        #awg_program = awg_program.replace('_ch_', str(ch))
        # if (ch % 2) == 0:
        #     seqCh = 2
        # else:
        #     seqCh = 1
        #awg_program = awg_program.replace('_ch_', str(ch))
        #print(awg_program)
        #    # Create an instance of the AWG Module
        # awgModule = self.daq.awgModule()
        # awgModule.set('awgModule/device', self.device)
        # awgModule.execute()
        #self.daq.sync()
        # Transfer the AWG sequence program. Compilation starts automatically.
        self.awgModule.set('awgModule/compiler/sourcestring', awg_program)
        # Note: when using an AWG program from a source file (and only the
        #print(awg_program)
        while self.awgModule.getInt('awgModule/compiler/status') == -1:
            time.sleep(0.1)
        if self.awgModule.getInt('awgModule/compiler/status') == 1:
        # compilation failed, raise an exception
            raise Exception(self.awgModule.getString('awgModule/compiler/statusstring'))
            #self.openSequence()
        else:
            if self.awgModule.getInt('awgModule/compiler/status') == 0:
                print("Compilation successful with no warnings, will upload the program to the instrument.")
            if self.awgModule.getInt('awgModule/compiler/status') == 2:
                print("Compilation successful with warnings, will upload the program to the instrument.")
                print("Compiler warning: ", self.awgModule.getString('awgModule/compiler/statusstring'))
    # wait for waveform upload to finish
            i = 0
            while self.awgModule.getDouble('awgModule/progress') < 1.0:
                print("{} awgModule/progress: {}".format(i, self.awgModule.getDouble('awgModule/progress')))
                time.sleep(0.1)
                i += 1
            print("{} awgModule/progress: {}".format(i, self.awgModule.getDouble('awgModule/progress')))
            #self.openSequence()
        print("Finished.")
        #self.daq.setInt('/'+self.device+'/awgs/'+str(seqNum)+'/enable',1)
        #self.openSequence()
        #self.daq.sync()
        self.daq.setInt('/' + self.device + '/awgs/0/single', 1)
        self.openSequence()

    def openSequence(self):
        #seqMode = self.daq.getInt('/{}/system/awg/channelgrouping'.format(self.device))
        #if seqMode == 1 or seqMode ==0:
        self.daq.setInt('/{}/system/awg/channelgrouping'.format(self.device), 2)
            #seqNum = 0
        self.daq.setInt('/'+self.device+'/awgs/0/enable',1)
        #else:
        #    print('The sequence mode is not corrent.')
        while self.daq.getInt('/'+self.device+'/awgs/0/enable') == 0:
            print(self.daq.getInt('/'+self.device+'/awgs/0/enable'))
            self.daq.setInt('/'+self.device+'/awgs/0/enable',1)
        self.daq.sync()

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
