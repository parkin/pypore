'''
Created on May 21, 2013

@author: parkin
'''
import scipy.io as sio
from array import array
import numpy as np
from ROOT import gROOT, TCanvas, TGraph, TH1D, TVirtualFFT  # @UnresolvedImport
 
gROOT.Reset()
c1 = TCanvas( 'c1', 'Example with Formula', 200, 10, 700, 500 )

'''
Do everything for the first dataset
'''
# load the matlab file with parameters for the runs
specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/params.mat')

print specsfile

ADCSAMPLERATE = specsfile['SETUP_ADCSAMPLERATE'][0][0]
TIAGAIN = specsfile['SETUP_TIAgain'][0][0]
PRE_ADC_GAIN = specsfile['SETUP_preADCgain'][0][0]
PA_OFFSET = specsfile['SETUP_pAoffset'][0][0]
ADCBITS = specsfile['SETUP_ADCBITS'][0][0]
ADCvref = specsfile['SETUP_ADCVREF'][0][0]

datafile = open('/home/parkin/Documents/DrndicLab/data/sample/data.log')
datatype = 'uint16'

bitmask = (2**16) - 1 - (2**(16-ADCBITS) - 1);
rawvalues = np.fromfile(datafile,datatype)
readvalues = rawvalues & bitmask

logdata = -ADCvref + (2*ADCvref) * readvalues / (2**16);



n=1000
if n > len(logdata):
    n = len(logdata)
timestep = 1/ADCSAMPLERATE
x=np.zeros(n)
for i in range(0,n-1):
    x[i]=timestep*i

gr = TGraph(n,x,logdata)
gr.GetXaxis().SetTitle("Time (s)")
gr.GetYaxis().SetTitle("Current")
gr.Draw("AL")
c1.Update();

# Need this, because nn is passed as a pointer
nn = array('i', [n])
fft = TVirtualFFT.FFT(1,nn,"R2C")
fft.SetPoints(logdata)
fft.Transform()

real = array('d',[0]*n)
imag = array('d',[0]*n)
fft.GetPointsComplex(real,imag)

mag = np.zeros(n)
for i in range(0,n-1):
    mag[i]=real[i]**2 + imag[i]**2
    
c2 = TCanvas( 'c2', 'Example with Formula', 200, 10, 700, 500 )
gr = TGraph(n-10,x,mag)
gr.GetXaxis().SetTitle("Time (s)")
gr.GetYaxis().SetTitle("Current")
gr.Draw("AL")
c2.Update();


# fftback = TVirtualFFT.FFT(1,nn,"C2R")
# fftback.SetPointsComplex(real,imag)
# fftback.Transform()
# rewind = fftback.GetPointsReal()

    

raw_input('Press [Enter] to exit.')

