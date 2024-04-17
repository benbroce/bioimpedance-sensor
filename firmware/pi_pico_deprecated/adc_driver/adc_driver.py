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
    # ADC Driver constructor
    def __init__(self, adc_channel: int):
        # set the GPIO pin on adc_channel to an analog input
        ADC_CHAN = adc_channel # adc channel (0 to 2)
        ADC_PIN = 26 + ADC_CHAN
        self._adc = devs.ADC_DEVICE
        pin = devs.GPIO_PINS[ADC_PIN]
        pad = devs.PAD_PINS[ADC_PIN]
        pin.GPIO_CTRL_REG = devs.GPIO_FUNC_NULL
        pad.PAD_REG = 0
        # clear the control & status registers (ADC, FIFO)
        self._adc.CS_REG = self._adc.FCS_REG = 0
        # enable ADC, select channel for conversion
        self._adc.CS.EN = 1
        self._adc.CS.AINSEL = ADC_CHAN

    def _convert_sample_to_voltage(self, sample: float) -> float:
        return (sample * 3.3 / 4096)

    def capture_sample(self) -> float:
        """
        return: a float voltage
        """
        self._adc.CS.START_ONCE = 1
        return self._adc.RESULT_REG
        
    def capture_samples(self, num_samples: int, sample_rate_hz: int) -> list[float]:
        """
        return: a list of float voltages captured at the given sample rate
        """
        # set parameters
        DMA_CHAN = 0
        NSAMPLES = num_samples
        RATE = sample_rate_hz
        dma_chan = devs.DMA_CHANS[DMA_CHAN]
        # enable ADC FIFO
        self._adc.FCS.EN = self._adc.FCS.DREQ_EN = 1
        # create a 16-bit buffer to hold the samples
        adc_buff = array.array('H', (0 for _ in range(NSAMPLES)))
        # set sample rate
        self._adc.DIV_REG = (48000000 // RATE - 1) << 8
        self._adc.FCS.THRESH = self._adc.FCS.OVER = self._adc.FCS.UNDER = 1
        # configure DMA controller (source and dest addresses, sample count)
        dma_chan.READ_ADDR_REG = devs.ADC_FIFO_ADDR
        dma_chan.WRITE_ADDR_REG = uctypes.addressof(adc_buff)
        dma_chan.TRANS_COUNT_REG = NSAMPLES
        # configure DMA destination to auto-increment
        dma_chan.CTRL_TRIG_REG = 0
        dma_chan.CTRL_TRIG.CHAIN_TO = DMA_CHAN
        dma_chan.CTRL_TRIG.INCR_WRITE = dma_chan.CTRL_TRIG.IRQ_QUIET = 1
        # set DMA to expect request for 16-bit data from ADC
        dma_chan.CTRL_TRIG.TREQ_SEL = devs.DREQ_ADC
        dma_chan.CTRL_TRIG.DATA_SIZE = 1
        # enable DMA
        dma_chan.CTRL_TRIG.EN = 1
        # clear ADC FIFO
        while self._adc.FCS.LEVEL:
            x = self._adc.FIFO_REG
        # start ADC sampling
        self._adc.CS.START_MANY = 1
        # continue sampling until RAM buffer is full (DMA transfer count reached, BUSY bit clear)
        while dma_chan.CTRL_TRIG.BUSY:
            time.sleep_ms(10)
        # stop ADC sampling
        self._adc.CS.START_MANY = 0
        # disable DMA
        dma_chan.CTRL_TRIG.EN = 0
        vals = [self._convert_sample_to_voltage(val) for val in adc_buff]
        return vals