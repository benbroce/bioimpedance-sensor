"""
Driver for high-frequency batch ADC sampling using DMA on the Pi Pico

This driver is a derivative work of the ADC test code found at:
https://github.com/jbentham/pico/blob/main/rp_adc_test.py

which is released under the following notice:

# Pico MicroPython: ADC test code
# See https://iosoft.blog/pico-adc-dma for description
#
# Copyright (c) 2021 Jeremy P Bentham
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

Modifications include packaging the essential ADC batch sampling code
into methods in a driver class. Modifications are released under the
base MIT license of this project.
"""

import time
import array
import uctypes
import rp_devices as devs

class ADC_Driver:
    def __init__(self):
        ADC_CHAN = 0
        ADC_PIN = 26 + ADC_CHAN

        self._adc = devs.ADC_DEVICE
        pin = devs.GPIO_PINS[ADC_PIN]
        pad = devs.PAD_PINS[ADC_PIN]
        pin.GPIO_CTRL_REG = devs.GPIO_FUNC_NULL
        pad.PAD_REG = 0

        self._adc.CS_REG = self._adc.FCS_REG = 0
        self._adc.CS.EN = 1
        self._adc.CS.AINSEL = ADC_CHAN

    def take_sample(self):
        # Multiple ADC samples using DMA
        DMA_CHAN = 0
        NSAMPLES = 10
        RATE = 100000
        dma_chan = devs.DMA_CHANS[DMA_CHAN]
        dma = devs.DMA_DEVICE

        self._adc.FCS.EN = self._adc.FCS.DREQ_EN = 1
        self._adc_buff = array.array('H', (0 for _ in range(NSAMPLES)))
        self._adc.DIV_REG = (48000000 // RATE - 1) << 8
        self._adc.FCS.THRESH = self._adc.FCS.OVER = self._adc.FCS.UNDER = 1

        dma_chan.READ_ADDR_REG = devs.ADC_FIFO_ADDR
        dma_chan.WRITE_ADDR_REG = uctypes.addressof(adc_buff)
        dma_chan.TRANS_COUNT_REG = NSAMPLES

        dma_chan.CTRL_TRIG_REG = 0
        dma_chan.CTRL_TRIG.CHAIN_TO = DMA_CHAN
        dma_chan.CTRL_TRIG.INCR_WRITE = dma_chan.CTRL_TRIG.IRQ_QUIET = 1
        dma_chan.CTRL_TRIG.TREQ_SEL = devs.DREQ_ADC
        dma_chan.CTRL_TRIG.DATA_SIZE = 1
        dma_chan.CTRL_TRIG.EN = 1

        while self._adc.FCS.LEVEL:
            x = self._adc.FIFO_REG
            
        self._adc.CS.START_MANY = 1
        while dma_chan.CTRL_TRIG.BUSY:
            time.sleep_ms(10)
        self._adc.CS.START_MANY = 0
        dma_chan.CTRL_TRIG.EN = 0
        vals = [("%1.3f" % (val*3.3/4096)) for val in adc_buff]
        print(vals)