"""

1. Read several short samples from ADC (several wave periods each)

	- See example at https://iosoft.blog/2021/10/26/pico-adc-dma/

2. Band pass filter the sample using an IIR filter

	- See 4th-order filter design from MATLAB code

3. Find the maximum and minimum values in each sample

4. Average all the maximum values and all the minimum values from all the samples

5. Calculate the peak-to-peak voltage of the input at the excitation frequency

6. Use this peak-to-peak voltage to calculate impedance

"""

from adc_driver.adc_driver import ADC_Driver
from utime import sleep

adc = ADC_Driver(0)

while True:
	samples = adc.capture_samples(50, 100000)
	print(samples)
	sleep(0.5)