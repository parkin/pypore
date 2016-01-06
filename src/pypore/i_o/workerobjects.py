# -*- coding: utf-8 -*-
import os
from PyQt4 import QtCore, QtGui
import numpy, scipy.signal
import time, datetime
import copy
import pywt, pyqtgraph
import Queue

class PSDWorker(QtCore.QObject):
    # finished = QtCore.pyqtSignal(numpy.float64, numpy.float64)
    finished = QtCore.pyqtSignal()
    # PSDReady = QtCore.pyqtSignal(numpy.ndarray, numpy.ndarray)
    PSDReady = QtCore.pyqtSignal()
    histogramReady = QtCore.pyqtSignal()
    #Signal for progress bar
    progress = QtCore.pyqtSignal(int, str)

    def __init__(self, parentWindow, dictOfConstants):
        super(PSDWorker, self).__init__()
        # self.ADCData = numpy.zeros(dictOfConstants['FRAMELENGTH']/4)
        self.parentWindow = parentWindow
        self.dictOfConstants = dictOfConstants

    def calculatePSD(self):
        self.start = time.clock()
        # self.ADCData = window.ADCData
        self.ADCData[self.ADCData >= 2**(self.dictOfConstants['ADCBITS']-1)] -= 2**(self.dictOfConstants['ADCBITS'])
        self.ADCData /= 2**(self.dictOfConstants['ADCBITS']-1)
        self.ADCData -= numpy.mean(self.ADCData)
        # if (True == self.parentWindow.ui.checkBox_enableSquareWave.isChecked()):
            # self.calculateDCResistance()
        # if (window.columnSelect in [0, 3]):
            # self.ADCData *= 16.0/5
        self.parentWindow.histogramView, self.parentWindow.bins = numpy.histogram(self.ADCData, bins=64)
        self.parentWindow.bins /= (self.dictOfConstants['AAFILTERGAIN']*self.parentWindow.RDCFB)
        self.histogramReady.emit()
        self.progress.emit(2, 'Calculating PSD')
        #### Begin PSD calculation
        # f, Pxx = scipy.signal.periodogram(self.ADCData, dictOfConstants['ADCSAMPLINGRATE'], nfft=2**19)
        f, Pxx = scipy.signal.welch(self.ADCData, self.dictOfConstants['ADCSAMPLINGRATE'], nperseg=2**19)
        #### End PSD calculation

        #### Begin FFT calculation
        # NFFT = 2**22
        # ADCDataFFT = numpy.fft.fft(self.ADCData, NFFT)
        # ADCDataFFT = ADCDataFFT[1:NFFT/2]
        # f = ADCSAMPLINGRATE/2*numpy.linspace(0, 1, NFFT/2)
        # f = f[1:len(f)]
        # Pxx = 2.0/(ADCSAMPLINGRATE*NFFT)*numpy.abs(numpy.square(ADCDataFFT))
        #### End FFT calculation

        # f_100Hz = numpy.argmin(numpy.abs(f - 1e2))
        Pxx = Pxx[f > 1e2]
        f = f[f>1e2]
        # PxxFitCoefficients = numpy.polynomial.polynomial.polyfit(f[f<6e6], Pxx[f<6e6]*f[f<6e6], 3)
        # f, Pxx = f[f_100Hz:len(f)], Pxx[f_100Hz:len(Pxx)]
        self.progress.emit(2, 'Preparing PSD data for plotting')
        f_100kHz = numpy.argmin(numpy.abs(f - 1e5))
        f_1MHz = numpy.argmin(numpy.abs(f - 1e6))
        f_10MHz = numpy.argmin(numpy.abs(f - 10e6))
        logIndices = numpy.unique(numpy.asarray(numpy.logspace(0, numpy.log10(f_10MHz), f_10MHz/self.dictOfConstants['SUBSAMPLINGFACTOR']), dtype=numpy.int32))
        # fToDisplay = f[logIndices-1]
        # PxxToDisplay = Pxx[logIndices-1]
        self.parentWindow.f = f[logIndices-1]
        # print len(PxxFitCoefficients)
        # self.parentWindow.PSDFit = numpy.divide(numpy.polynomial.polynomial.polyval(f[logIndices-1], PxxFitCoefficients), f[logIndices-1])
        # print PxxFitCoefficients[2]/(4*3.14**2*3e-9*3e-9)
        if (hasattr(self.parentWindow.ui, 'checkBox_frequencyResponse') and self.parentWindow.ui.checkBox_frequencyResponse.isChecked() == True):
            self.parentWindow.PSD = numpy.divide(Pxx[logIndices-1], f[logIndices-1]**2)
        else:
            self.parentWindow.PSD = Pxx[logIndices-1]
        # PxxFitCoefficients = numpy.polynomial.polynomial.polyfit(self.parentWindow.f[self.parentWindow.f < 6e6], self.parentWindow.PSD[self.parentWindow.f < 6e6] * self.parentWindow.f[self.parentWindow.f < 6e6], 3, w = 1/(self.parentWindow.f[self.parentWindow.f < 6e6] * self.parentWindow.PSD[self.parentWindow.f < 6e6]))
        # self.parentWindow.PSDFit = numpy.divide(numpy.polynomial.polynomial.polyval(self.parentWindow.f, PxxFitCoefficients), self.parentWindow.f)
        if (self.parentWindow.ui.action_addNoiseFit.isChecked() == True):
            self.parentWindow.PSDFit = self.createFit(self.parentWindow.f, self.parentWindow.PSD, 1e6)
        # self.PSDReady.emit(fToDisplay, PxxToDisplay)
        self.PSDReady.emit()
        self.progress.emit(1, 'Finishing up')

        self.RMSNoise = numpy.sqrt(scipy.integrate.cumtrapz(Pxx, f, initial=0))/self.dictOfConstants['AAFILTERGAIN']/self.parentWindow.RDCFB
        self.parentWindow.RMSNoise = self.RMSNoise[logIndices-1]
        
        self.parentWindow.RMSNoise_100kHz = numpy.round(self.RMSNoise[f_100kHz] * 10**12, 1)
        self.parentWindow.RMSNoise_1MHz = numpy.round(self.RMSNoise[f_1MHz] * 10**12, 1)
        self.parentWindow.RMSNoise_10MHz = numpy.round(self.RMSNoise[f_10MHz-1] * 10**12, 1)
        self.stop = time.clock()
        # print "Calculate PSD thread took", self.stop-self.start, "s"
        # self.finished.emit(numpy.round(RMSNoise_100kHz * 10**12, 1), numpy.round(RMSNoise_1MHz * 10**12, 1))
        self.finished.emit()

    def calculateDCResistance(self):
        self.ADCDataRMS = numpy.sqrt(numpy.mean(numpy.power(self.ADCData, 2)))
        self.poreResistance = self.dictOfConstants['SQUAREWAVEAMPLITUDE']/self.ADCDataRMS*self.dictOfConstants['AAFILTERGAIN']*self.parentWindow.RDCFB
        self.parentWindow.ui.label_poreResistance.setText(str(numpy.round(self.poreResistance/1e6, 1)) + u"MΩ")
        
    def createFit(self, fFit, PSDFit, maxFitFrequency = 6e6):
        fFitNew = fFit[fFit < maxFitFrequency]
        PSDFitNew = PSDFit[fFit < maxFitFrequency]
        fitCoefficients = numpy.polynomial.polynomial.polyfit(fFitNew, PSDFitNew * fFitNew, 3, w = 1/(fFitNew * PSDFitNew)) #Fit PSD*f to 3rd order and then divide by f to get the 1/f term also
        print numpy.sqrt(fitCoefficients[3])/(2*3.14*3e-9*self.parentWindow.RDCFB)
        return numpy.divide(numpy.polynomial.polynomial.polyval(fFit, fitCoefficients), fFit)

class GetDataFromFPGAWorker(QtCore.QObject):
    """Worker module that inherits from QObject. Eventually, this gets moved on to a thread that inherits from QThread."""
    finished = QtCore.pyqtSignal()
    dataReady = QtCore.pyqtSignal()

    def __init__(self, parentWindow, dictOfConstants, FPGAInstance):
        super(GetDataFromFPGAWorker, self).__init__()
        self.parentWindow = parentWindow
        self.FPGAInstance = FPGAInstance
        if self.FPGAInstance is not None:
            self.FPGAType = self.FPGAInstance.type
            self.validColumns = self.FPGAInstance.validColumns
            self.processRawDataThreadOptions = {'Master': self.parentWindow.processRawDataMasterThread, 'Slave': self.parentWindow.processRawDataSlaveThread}
            self.processRawDataThread = self.processRawDataThreadOptions[self.FPGAType]
            self.processRawDataWorkerInstanceOptions = {'Master': self.parentWindow.processRawDataMasterWorkerInstance, 'Slave': self.parentWindow.processRawDataSlaveWorkerInstance}
            self.processRawDataWorkerInstance = self.processRawDataWorkerInstanceOptions[self.FPGAType]
        self.dictOfConstants = dictOfConstants

    def getDataFromFPGA(self):
        """Gets data from the FPGA and logs it if the corresponding option has been enabled. Calls processRawData once a chunk of data has been obtained. Loops infinitely."""
        while (self.FPGAInstance.configured):
            # rawData = bytearray(self.dictOfConstants['FRAMELENGTH'])
            if ('Master' == self.FPGAType):
                rawData = bytearray(self.dictOfConstants['FRAMELENGTH_MASTER'])
            elif ('Slave' == self.FPGAType):
                rawData = bytearray(self.dictOfConstants['FRAMELENGTH_SLAVE'])
            self.start = time.clock()
            errorReturn = self.FPGAInstance.xem.ReadFromBlockPipeOut(0xA0, self.dictOfConstants['BLOCKLENGTH'], rawData)
            # errorReturn = self.FPGAInstance.xem.ReadFromPipeOut(0xA0, rawData)
            if (self.FPGAInstance.xem.Timeout == errorReturn):
                print "Transaction timed out on", self.FPGAType, "FPGA"
            if (self.FPGAInstance.xem.Failed == errorReturn):
                print "Transaction failed on", self.FPGAType, "FPGA"
                self.FPGAInstance.powered = False #Change power status to off if code breaks out of the while loop
                self.FPGAInstance.configured= False #Change configuration status to unconfigured if code breaks out of the while loop
            if (self.parentWindow.columnSelect in self.validColumns):
                if (self.parentWindow.ui.action_enableLogging.isChecked()):
                    self.parentWindow.writeToLogFileWorkerInstance.rawData.put(rawData)
                    # self.parentWindow.writeToLogFileThread.start()
            self.dataReady.emit()
            # rawDataUnpacked = numpy.frombuffer(rawData, dtype='uint32')
            if (self.parentWindow.columnSelect in self.validColumns):
                if not (self.processRawDataThread.isRunning()):
                    self.processRawDataWorkerInstance.rawData = rawData
                    self.processRawDataThread.start()
                # if (False == window.processRawDataThread.isRunning()):
                    # window.processRawDataWorkerInstance.rawData = rawData
                    # window.processRawDataThread.start()
                self.updateWireOuts()
            self.stop = time.clock()
            # if ('Slave' == self.FPGAType):
                # print "Get data from FPGA thread took", self.stop-self.start, "s"
            # self.dataReady.emit()
            # self.processRawData(rawDataUnpacked)
        self.finished.emit()

    def updateWireOuts(self):
        self.FPGAInstance.xem.UpdateWireOuts()
        RAMMemoryUsage = self.FPGAInstance.xem.GetWireOutValue(0x20)
        RAMMemoryUsage = numpy.round(RAMMemoryUsage*1.0/2**20, 1);
        self.parentWindow.RAMMemoryUsage = RAMMemoryUsage
        return

class ProcessRawDataWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    # dataReady = QtCore.pyqtSignal(numpy.ndarray)
    dataReady = QtCore.pyqtSignal()
    startPSDThread = QtCore.pyqtSignal()
    #Signals for the progress bar
    progress = QtCore.pyqtSignal(int, str)

    def __init__(self, parentWindow, dictOfConstants, FPGAInstance):
        super(ProcessRawDataWorker, self).__init__()
        self.dictOfConstants = dictOfConstants
        self.createFilter(100e3)
        self.parentWindow = parentWindow
        self.FPGAInstance = FPGAInstance
        if self.FPGAInstance is not None:
            self.FPGAType = self.FPGAInstance.type
            self.validColumns = self.FPGAInstance.validColumns
        else:
            self.FPGAType = 'Generic'
            self.validColumns = [0, 1, 2, 3, 4]
        # self.rawData = bytearray(self.dictOfConstants['FRAMELENGTH'])
        self.rawDataUnpacked = 0

    def processRawData(self):
        """Processes the raw data. The raw data is a 32 bit number that contains {8'h00, 12'hADC1Data, 12'hADC0DATA}. This method unpacks the data and then subsamples it and corrects for the boosting and anti-aliasing filter gain and DC offset."""
        self.start = time.clock()
        # self.rawDataUnpacked = numpy.frombuffer(self.rawData, dtype='uint32')
        # ADCData = {0: numpy.bitwise_and(self.rawDataUnpacked, 0xfff),\
                # 1: (numpy.bitwise_and(self.rawDataUnpacked, 0xfff000))>>12,\
                # 3: numpy.bitwise_and(self.rawDataUnpacked, 0xfff)}
        # Switched from dictionary to if else implementation because of timing issues while displaying data
        ADCData = self.unpackData()
        if (self.parentWindow.ui.checkBox_enableLivePreviewFilter.isChecked()):
            # ADCData2 = copy.deepcopy(ADCData)
            ADCData2 = ADCData.astype(numpy.float64)
            ADCData2[ADCData2 >= 2**(self.dictOfConstants['ADCBITS']-1)] -= 2**(self.dictOfConstants['ADCBITS'])
            # ADCData2 = ADCData2.astype(numpy.float64, copy=False)
            ADCData2 /= 2**(self.dictOfConstants['ADCBITS']-1)
            # self.parentWindow.IDCRelative = numpy.mean(ADCData2) - self.parentWindow.IDCOffset
            # self.parentWindow.updateIDCLabels()
            ADCData2 = scipy.signal.lfilter(self.b, self.a, ADCData2)
            # ADCData = ADCData2
            # if (self.parentWindow.ui.checkBox_enableWaveletDenoising.isChecked()):
                # # threshold = 0.005# numpy.sqrt(2*numpy.log2(len(ADCData2)))
                # threshold = numpy.std(ADCData2)*numpy.sqrt(2*numpy.log10(len(ADCData2)))
                # self.motherWavelet = str(self.parentWindow.ui.lineEdit_motherWavelet.text())
                # waveletCoefficients = pywt.wavedec(ADCData2, self.motherWavelet, level=3)# level=int(numpy.floor(numpy.log2(len(ADCData2)))))
                # newWaveletCoefficients = map(lambda x: pywt.thresholding.soft(x, 0.5*threshold), waveletCoefficients)
                # ADCData2 = pywt.waverec(newWaveletCoefficients, self.motherWavelet)
            # totalNoise = numpy.std(ADCData2)
            # tags = ADCData2 < -5*totalNoise
            # print totalNoise/self.parentWindow.RDCFB, numpy.sum(numpy.bitwise_and(numpy.bitwise_and(tags[:-3], tags[1:-2]), numpy.bitwise_and(tags[2:-1], tags[3:])))

            # Skip first few points of filtered data to avoid edge effects due to filtering
            self.skipPoints = numpy.ceil(self.dictOfConstants['ADCSAMPLINGRATE']/self.livePreviewFilterBandwidth)
            dataToDisplay = (ADCData2)[self.skipPoints::self.dictOfConstants['SUBSAMPLINGFACTOR']]*1 #Multiplying by 1 is necessary to ensure dataToDisplay does not modify ADCData2
            if (hasattr(self.parentWindow, 'analyzeDataWorkerInstance')):
                self.parentWindow.analyzeDataWorkerInstance.rawData = ADCData2[self.skipPoints:]/self.parentWindow.RDCFB/self.dictOfConstants['AAFILTERGAIN'] - self.parentWindow.IDCOffset
                self.parentWindow.analyzeDataWorkerInstance.skipPoints = self.skipPoints
        else:
            dataToDisplay = (ADCData)[0::self.dictOfConstants['SUBSAMPLINGFACTOR']]*1.0
            dataToDisplay[dataToDisplay >= 2**(self.dictOfConstants['ADCBITS']-1)] -= 2**(self.dictOfConstants['ADCBITS'])
            dataToDisplay /= 2**(self.dictOfConstants['ADCBITS']-1)
            # self.parentWindow.IDCRelative = numpy.mean(dataToDisplay) - self.parentWindow.IDCOffset
            # self.parentWindow.updateIDCLabels()
            # dataToDisplay -= numpy.mean(dataToDisplay)
        # if (window.columnSelect in [0, 3]):
            # dataToDisplay *= 16.0/5
        dataToDisplay *= 1.0/self.parentWindow.RDCFB/self.dictOfConstants['AAFILTERGAIN'] #Prefixes (like nano or pico) are handled automatically by PyQtGraph
        self.parentWindow.IDCRelative = numpy.mean(dataToDisplay) - self.parentWindow.IDCOffset
        dataToDisplay -= self.parentWindow.IDCOffset
        self.parentWindow.updateIDCLabels()
        # if (self.parentWindow.ui.checkBox_enableLivePreviewFilter.isChecked()):
            # dataToDisplay = scipy.signal.lfilter(self.b, self.a, dataToDisplay)
        self.progress.emit(1, 'Finished calculating data to display')
        if (hasattr(self.parentWindow.ui, 'action_enableLivePreview') and self.parentWindow.ui.action_enableLivePreview.isChecked() == False):
            pass
        else:
            self.parentWindow.dataToDisplay = dataToDisplay
        # self.dataReady.emit(dataToDisplay)
        if not (self.parentWindow.PSDThread.isRunning()):
            # window.PSDWorkerInstance.ADCData = ADCData[window.columnSelect]*1.0
            self.parentWindow.PSDWorkerInstance.ADCData = ADCData.astype(numpy.float64) #ADCData is sent as float64
            self.parentWindow.PSDThread.start()
            self.progress.emit(1, 'Calculating histogram')
            # self.startPSDThread.emit()
        self.stop = time.clock()
        # print "Processing the data took", self.stop-self.start, "s"
        self.dataReady.emit()
        self.finished.emit()

    def createFilter(self, livePreviewFilterBandwidth):
        """Given that SUBSAMPLINGFACTOR reduces the raw data to a lower data rate, the filter cutoff frequency below needs to be adjusted accordingly
        For example, for ADCSAMPLINGRATE = 156.25e6/4, SUBSAMPLINGFACTOR of 40 produces samples roughly every 1us. Therefore, effective signal
        bandwidth reduces to 500kHz. To sample down to 100kHz then requires a cutoff frequency of 0.2 (= 100kHz/500kHz)."""
        self.livePreviewFilterBandwidth = livePreviewFilterBandwidth
        self.b, self.a = scipy.signal.bessel(4, livePreviewFilterBandwidth/self.dictOfConstants['ADCSAMPLINGRATE']*2, 'low')

    def unpackData(self):
        """Returns unpacked ADCData for the selected column"""
        if ('Master' == self.FPGAType):
            self.rawDataUnpacked = numpy.frombuffer(self.rawData, dtype='uint32')
            self.progress.emit(1, 'Unpacking data')
            if (0 == self.parentWindow.columnSelect):
                ADCData = numpy.bitwise_and(self.rawDataUnpacked, 0xfff)
            elif (1 == self.parentWindow.columnSelect):
                ADCData = numpy.bitwise_and(self.rawDataUnpacked, 0xfff000) >> 12
            self.progress.emit(1, 'Processing data for plotting')
            return ADCData
        if ('Slave' == self.FPGAType):
            self.rawData64Bit = numpy.frombuffer(self.rawData, dtype='uint64')
            self.progress.emit(1, 'Unpacking data')
            if (2 == self.parentWindow.columnSelect):
                ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[0::2], 0xfffffffff)
                ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                ADCData[2::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000000) >> 24
            elif (3 == self.parentWindow.columnSelect):
                ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[0::2], 0xfffffff000000000) >> 36
                ADCDataCompressedMSB = numpy.bitwise_and(self.rawData64Bit[1::2], 0xff)
                ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                ADCData[2::3] = (numpy.bitwise_and(ADCDataCompressed, 0xf000000) >> 24) + ADCDataCompressedMSB*16
            elif (4 == self.parentWindow.columnSelect):
                ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[1::2], 0x00000fffffffff00) >> 8
                ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                ADCData[2::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000000) >> 24
            self.progress.emit(1, 'Processing data for plotting')
            return ADCData
        elif ('Generic' == self.FPGAType):
            if (self.parentWindow.columnSelect in [0, 1]):
                self.rawDataUnpacked = numpy.frombuffer(self.rawData, dtype='uint32')
                self.progress.emit(1, 'Unpacking data')
                if (0 == self.parentWindow.columnSelect):
                    ADCData = numpy.bitwise_and(self.rawDataUnpacked, 0xfff)
                elif (1 == self.parentWindow.columnSelect):
                    ADCData = numpy.bitwise_and(self.rawDataUnpacked, 0xfff000) >> 12
                self.progress.emit(1, 'Processing data for plotting')
                return ADCData
            elif (self.parentWindow.columnSelect in [2, 3, 4]):
                self.rawData64Bit = numpy.frombuffer(self.rawData, dtype='uint64')
                self.progress.emit(1, 'Unpacking data')
                if (2 == self.parentWindow.columnSelect):
                    ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[0::2], 0xfffffffff)
                    ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                    ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                    ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                    ADCData[2::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000000) >> 24
                elif (3 == self.parentWindow.columnSelect):
                    ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[0::2], 0xfffffff000000000) >> 36
                    ADCDataCompressedMSB = numpy.bitwise_and(self.rawData64Bit[1::2], 0xff)
                    ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                    ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                    ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                    ADCData[2::3] = (numpy.bitwise_and(ADCDataCompressed, 0xf000000) >> 24) + ADCDataCompressedMSB*16
                elif (4 == self.parentWindow.columnSelect):
                    ADCDataCompressed = numpy.bitwise_and(self.rawData64Bit[1::2], 0x00000fffffffff00) >> 8
                    ADCData = numpy.zeros((3*numpy.size(ADCDataCompressed),))
                    ADCData[0::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff)
                    ADCData[1::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000) >> 12
                    ADCData[2::3] = numpy.bitwise_and(ADCDataCompressed, 0xfff000000) >> 24
                self.progress.emit(1, 'Processing data for plotting')
                return ADCData

class WriteToLogFileWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, parentWindow, dictOfConstants):
        super(WriteToLogFileWorker, self).__init__()
        self.rawData = Queue.Queue()
        self.f = 0
        self.parentWindow = parentWindow
        self.dictOfConstants = dictOfConstants
        self.defaultDirectory = "./Logfiles" + "/" + datetime.date.today().strftime("%Y%m%d") + "/"

    def writeToLogFile(self):
        start = time.clock()
        if not os.path.exists(self.defaultDirectory):
            os.makedirs(self.defaultDirectory)
        # print len(self.rawData[0])
        self.fileName = self.defaultDirectory + self.parentWindow.dataFileSelected + "_" + datetime.date.today().strftime("%Y%m%d") + "_" + time.strftime("%H%M%S") + ".hex"
        self.f = open(self.fileName, 'a+b')
        # While logging is enabled, write in 1 second bursts. Finish writing everything that is in memory when logging is disabled
        if (self.parentWindow.ui.action_enableLogging.isChecked()):
            for i in range(self.dictOfConstants['REFRESHRATE']):
                self.f.write(self.rawData.get())
        # self.rawData = []
        else:
            for i in range(self.rawData.qsize()):
                self.f.write(self.rawData.get())
        self.f.close()
        self.configFileName = self.fileName[0:len(self.fileName) - 3] + "cfg"
        self.parentWindow.action_saveState_triggered(self.configFileName)
        stop = time.clock()
        print "Writing data to disk took", stop-start, "s"
        if ((stop - start)*1000 > self.dictOfConstants['FRAMEDURATION']):
            print "Probably missed writing some data because it took too long to write the last frame"
        self.finished.emit()
      
class AnalyzeDataWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    
    def __init__(self, parentWindow, dictOfConstants):
        super(AnalyzeDataWorker, self).__init__()
        self.parentWindow = parentWindow
        self.dictOfConstants = dictOfConstants
        self.rawData = 0
        
    def analyzeData(self, detectEdges=True):
        # self.rawData = self.parentWindow.processRawDataWorkerInstance.ADCData2/self.parentWindow.RDCFB/self.dictOfConstants['AAFILTERGAIN'] - self.parentWindow.IDCOffset
        self.baseline = numpy.mean(self.rawData)
        self.parentWindow.baseline = self.baseline
        if (self.parentWindow.threshold is not None):
            self.threshold = self.parentWindow.threshold
        else:
            self.threshold = self.baseline - 5*numpy.std(self.rawData)
            self.parentWindow.threshold = self.threshold
        try:
            self.minimumEventDuration = eval(str(self.parentWindow.ui.lineEdit_minimumEventDuration.text()))*1e-6
            self.minimumEventSamples = self.dictOfConstants['ADCSAMPLINGRATE']*self.minimumEventDuration
        except:
            self.minimumEventDuration = 1e-6
            self.minimumEventSamples = self.dictOfConstants['ADCSAMPLINGRATE']*self.minimumEventDuration
        try:
            self.maximumEventDuration = eval(str(self.parentWindow.ui.lineEdit_maximumEventDuration.text()))*1e-6
            self.maximumEventSamples = self.dictOfConstants['ADCSAMPLINGRATE']*self.maximumEventDuration
        except:
            self.maximumEventDuration = 1e-3
            self.maximumEventSamples = self.dictOfConstants['ADCSAMPLINGRATE']*self.maximumEventDuration
        if (detectEdges == True):
            self.detectEdges()
            
    def detectEdges(self):
        self.eventIndex = (numpy.where(self.rawData < self.threshold)[0]).astype(numpy.int32)
        self.transitions = numpy.diff(self.eventIndex)
        self.edgeBeginIndex = numpy.insert(self.transitions, 0, 2)
        self.edgeEndIndex = numpy.insert(self.transitions, -1, 2)
        self.edgeBegin = self.eventIndex[numpy.where(self.edgeBeginIndex > 1)]
        self.edgeEnd = self.eventIndex[numpy.where(self.edgeEndIndex > 1)]
        
        self.numberOfEvents = len(self.edgeBegin)
        self.limit = self.baseline - 0.9*numpy.std(self.rawData) #Set the upper limit to 5 sigma away from the mean
        for i in range(self.numberOfEvents):
            eb = self.edgeBegin[i]
            while self.rawData[eb] < self.limit and eb > 0:
                eb -= 1
            self.edgeBegin[i] = eb
            
            ee = self.edgeEnd[i]
            while self.rawData[ee] < self.limit:
                ee += 1
                if i == self.numberOfEvents - 1:
                    if ee == len(self.rawData) - 1:
                        self.edgeEnd[i] = 0
                        self.edgeBegin[i] = 0
                        ee = 0
                        break
                elif ee > self.edgeBegin[i + 1]:
                    self.edgeBegin[i+1] = 0
                    self.edgeEnd[i] = 0
                    ee = 0
                    break
            self.edgeEnd[i] = ee
            
        self.edgeBegin = self.edgeBegin[self.edgeBegin != 0]
        self.edgeEnd = self.edgeEnd[self.edgeEnd != 0]
        self.numberOfEvents = len(self.edgeBegin)
        
        # Remove events shorter than duration specified in the GUI
        for i in range(self.numberOfEvents):
            if ((self.edgeEnd[i] - self.edgeBegin[i]) < self.minimumEventSamples) or ((self.edgeEnd[i] - self.edgeBegin[i]) > self.maximumEventSamples):
                self.edgeBegin[i] = 0
                self.edgeEnd[i] = 0
        
        self.edgeBegin = self.edgeBegin[self.edgeBegin != 0]
        self.edgeEnd = self.edgeEnd[self.edgeEnd != 0]
        self.numberOfEvents = len(self.edgeBegin)
        
        self.eventIndex = numpy.empty_like(self.edgeBegin, dtype='object') #Overwrites previous self.eventIndex
        self.eventValue = numpy.empty_like(self.edgeBegin, dtype='object') 
        self.deltaI = numpy.empty_like(self.edgeBegin, dtype='object') 
        self.meanDeltaI = numpy.empty_like(self.edgeBegin, dtype=numpy.float64)
        self.dwellTime = numpy.empty_like(self.edgeBegin, dtype=numpy.float64)
        
        for i in range(self.numberOfEvents):
            self.eventIndex[i] = numpy.arange(self.edgeBegin[i], self.edgeEnd[i]+1)
            self.eventValue[i] = self.rawData[self.eventIndex[i]]
            self.deltaI[i] = self.baseline - self.rawData[self.eventIndex[i]]
            self.meanDeltaI[i] = numpy.mean(self.deltaI[i], dtype=numpy.float64)
            self.dwellTime[i] = (self.edgeEnd[i] - self.edgeBegin[i]).astype(numpy.float64)/self.dictOfConstants['ADCSAMPLINGRATE']
            
        # print self.edgeBegin, self.edgeEnd, self.eventIndex
        self.parentWindow.edgeBegin = self.edgeBegin
        self.parentWindow.edgeEnd = self.edgeEnd
        self.parentWindow.numberOfEvents = self.numberOfEvents
        self.parentWindow.eventIndex = self.eventIndex
        self.parentWindow.eventValue = self.eventValue
        self.parentWindow.deltaI = self.deltaI
        self.parentWindow.meanDeltaI = self.meanDeltaI
        self.parentWindow.dwellTime = self.dwellTime
        
        self.finished.emit()
        #self.analyze_cusum_modified()
        
    def analyze_cusum(self):
        '''Analyzes the waveform using the CUSUM algorithm. Adapted from PyPore implementation but only handles downward spikes'''
        
        #Initializations
        i = 0
        eventNumber = 0
        dataPoint = self.rawData[i]
        nData = len(self.rawData)
        baseline = dataPoint
        variance = numpy.var(self.rawData[0:100])
        variance_baseline = baseline
        isEvent = False
        
        maxNumberOfEvents = 1000
        
        self.edgeBegin = numpy.empty(maxNumberOfEvents)
        self.edgeEnd = numpy.empty(maxNumberOfEvents)
        self.eventValue = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        self.meanEventValue = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        self.dwellTime = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        
        threshold_start = 5 * numpy.sqrt(variance)
        threshold_end = 1 * numpy.sqrt(variance)
        
        while i < nData:
            dataPoint = self.rawData[i]
            
            if (dataPoint < baseline - threshold_start):
                isEvent = True
                self.edgeBegin[eventNumber] = i
            
            if isEvent:
                isEvent = False
                done = False
                meanEstimate = dataPoint
                nLevels = 0
                sn = sp = Sn = Sp = Gn = Gp = 0
                varianceEstimate = variance
                threshold_end = 1 * numpy.sqrt(variance)
                
                delta = numpy.abs(meanEstimate - baseline)/2.
                minIndexP = minIndexN = i
                
                eventArea = dataPoint
                event_i = i
                ko = i
                
                levelSum = dataPoint
                levelSumMinP = dataPoint
                levelSumMinN = dataPoint
                previousLevelStart = event_i
                
                while not done and event_i - self.edgeBegin[eventNumber] < self.maximumEventSamples:
                    event_i += 1
                    dataPoint = self.rawData[event_i]
                    
                    if dataPoint >= baseline - threshold_end:
                        done = True
                        self.edgeEnd[eventNumber] = event_i
                        break
                        
                    newMean = meanEstimate + (dataPoint - meanEstimate)/(1 + event_i - ko)
                    varianceEstimate = ((event_i - ko) * varianceEstimate + (dataPoint - meanEstimate) * (dataPoint - newMean))/(1 + event_i - ko)
                    meanEstimate = newMean
                    if varianceEstimate > 0:
                        sp = (delta/varianceEstimate) * (dataPoint - meanEstimate - delta/2.)
                        sn = -(delta/varianceEstimate) * (dataPoint - meanEstimate + delta/2.)
                    elif delta == 0:
                        sp = 0
                        sn = 0
                    Sp += sp
                    Sn += sn
                    Gp = numpy.maximum(0., Gp + sp)
                    Gn = numpy.maximum(0., Gn + sn)
                    levelSum += dataPoint
                    
                    if Sp <= 0:
                        Sp = 0
                        minIndexP = event_i
                        levelSumMinP = levelSum
                    if Sn <= 0:
                        Sn = 0
                        minIndexN = event_i
                        levelSumMinN = levelSum
                    h = delta/numpy.sqrt(varianceEstimate)

                    if Gp > h or Gn > h:
                        if Gp > h:
                            minIndex = minIndexP
                            levelSum = levelSumMinP
                        else:
                            minIndex = minIndexN
                            levelSum = levelSumMinN
                        self.dwellTime[eventNumber][nLevels] = (minIndex + 1 - ko)*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                        self.meanEventValue[eventNumber][nLevels] = levelSum/self.dwellTime[eventNumber][nLevels]*self.dictOfConstants['ADCSAMPLINGRATE']
                        nLevels += 1
                        sn = sp = Sn = Sp = Gn = Gp = 0
                        ko = event_i = minIndex + 1
                        minIndexP = minIndexN = event_i
                        previousLevelStart = event_i
                        meanEstimate = self.rawData[event_i]
                        levelSum = levelSumMinP = levelSumMinN = meanEstimate
                        
                i = self.edgeEnd[eventNumber].astype(int)
                if self.edgeEnd[eventNumber] > previousLevelStart:
                    self.dwellTime[eventNumber][nLevels] = (self.edgeEnd[eventNumber] - previousLevelStart)*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                    self.meanEventValue[eventNumber][nLevels] = levelSum/self.dwellTime[eventNumber][nLevels]*self.dictOfConstants['ADCSAMPLINGRATE']
                    nLevels += 1
                    
                if done and self.edgeEnd[eventNumber] - self.edgeBegin[eventNumber] > self.minimumEventSamples:
                    if self.edgeEnd[eventNumber] - self.edgeBegin[eventNumber] < 2*self.minimumEventSamples:
                        nLevels = 0
                        self.meanEventValue[eventNumber][nLevels] = numpy.min(self.rawData[self.edgeBegin[eventNumber]:self.edgeEnd[eventNumber]+1])
                        self.dwellTime[eventNumber][nLevels] = (self.edgeEnd[eventNumber]-self.edgeBegin[eventNumber])*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                        
                eventNumber += 1
                        
            baseline = baseline * 0.93 + (1 - 0.93) * dataPoint #Adaptive basline
            variance_baseline = 0.99 * variance_baseline + (1 - 0.99) * dataPoint
            variance = 0.99 * variance + (1 - 0.99) * numpy.power(dataPoint - variance_baseline, 2) #Adaptive baseline
            i += 1
            
            if i % 100000 == 0:
                print i, eventNumber
                
        self.eventIndex = numpy.empty_like(self.edgeBegin, dtype='object')
        for i in range(eventNumber):
            self.eventIndex[i] = numpy.arange(self.edgeBegin[i], self.edgeEnd[i]+1)
        
        self.parentWindow.edgeBegin = self.edgeBegin[:eventNumber].astype(int)
        self.parentWindow.edgeEnd = self.edgeEnd[:eventNumber].astype(int)
        self.numberOfEvents = int(eventNumber)
        self.parentWindow.numberOfEvents = self.numberOfEvents
        self.parentWindow.eventIndex = self.eventIndex
        
        self.finished.emit()
        
    def analyze_cusum_modified(self):
        #Initializations
        i = 0
        j = 0
        eventNumber = 0
        dataPoint = self.rawData[i]
        nData = len(self.rawData)
        baseline = dataPoint
        variance = numpy.var(self.rawData[0:100])
        variance_baseline = baseline
        isEvent = False
        localEventIndex = numpy.hstack(self.eventIndex)
        
        maxNumberOfEvents = 1000
        
        # self.edgeBegin = numpy.empty(maxNumberOfEvents)
        # self.edgeEnd = numpy.empty(maxNumberOfEvents)
        self.eventValue = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        self.meanEventValue = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        self.dwellTime = numpy.empty([maxNumberOfEvents, self.maximumEventSamples], dtype='object')
        
        threshold_start = 5 * numpy.sqrt(variance)
        threshold_end = 1 * numpy.sqrt(variance)
        
        while j < (len(localEventIndex)):
            i = localEventIndex[j]
            dataPoint = self.rawData[i]
                        
            if True:
                done = False
                meanEstimate = dataPoint
                nLevels = 0
                sn = sp = Sn = Sp = Gn = Gp = 0
                varianceEstimate = variance
                threshold_end = 1 * numpy.sqrt(variance)
                
                delta = numpy.abs(meanEstimate - baseline)/2.
                minIndexP = minIndexN = i
                
                eventArea = dataPoint
                event_i = i
                ko = i
                
                levelSum = dataPoint
                levelSumMinP = dataPoint
                levelSumMinN = dataPoint
                previousLevelStart = event_i
                
                while not done:
                    event_i += 1
                    dataPoint = self.rawData[event_i]
                    
                    if dataPoint >= baseline - threshold_end:
                        done = True
                        break
                        
                    newMean = meanEstimate + (dataPoint - meanEstimate)/(1 + event_i - ko)
                    varianceEstimate = ((event_i - ko) * varianceEstimate + (dataPoint - meanEstimate) * (dataPoint - newMean))/(1 + event_i - ko)
                    meanEstimate = newMean
                    if varianceEstimate > 0:
                        sp = (delta/varianceEstimate) * (dataPoint - meanEstimate - delta/2.)
                        sn = -(delta/varianceEstimate) * (dataPoint - meanEstimate + delta/2.)
                    elif delta == 0:
                        sp = 0
                        sn = 0
                    Sp += sp
                    Sn += sn
                    Gp = numpy.maximum(0., Gp + sp)
                    Gn = numpy.maximum(0., Gn + sn)
                    levelSum += dataPoint
                    
                    if Sp <= 0:
                        Sp = 0
                        minIndexP = event_i
                        levelSumMinP = levelSum
                    if Sn <= 0:
                        Sn = 0
                        minIndexN = event_i
                        levelSumMinN = levelSum
                    h = delta/numpy.sqrt(varianceEstimate)

                    if Gp > h or Gn > h:
                        if Gp > h:
                            minIndex = minIndexP
                            levelSum = levelSumMinP
                        else:
                            minIndex = minIndexN
                            levelSum = levelSumMinN
                        self.dwellTime[eventNumber][nLevels] = (minIndex + 1 - ko)*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                        self.meanEventValue[eventNumber][nLevels] = levelSum/self.dwellTime[eventNumber][nLevels]*self.dictOfConstants['ADCSAMPLINGRATE']
                        nLevels += 1
                        sn = sp = Sn = Sp = Gn = Gp = 0
                        ko = event_i = minIndex + 1
                        minIndexP = minIndexN = event_i
                        previousLevelStart = event_i
                        meanEstimate = self.rawData[event_i]
                        levelSum = levelSumMinP = levelSumMinN = meanEstimate
                        
                # i = self.edgeEnd[eventNumber].astype(int)
                if self.edgeEnd[eventNumber] > previousLevelStart:
                    self.dwellTime[eventNumber][nLevels] = (self.edgeEnd[eventNumber] - previousLevelStart)*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                    self.meanEventValue[eventNumber][nLevels] = levelSum/self.dwellTime[eventNumber][nLevels]*self.dictOfConstants['ADCSAMPLINGRATE']
                    nLevels += 1
                    
                if done and self.edgeEnd[eventNumber] - self.edgeBegin[eventNumber] > self.minimumEventSamples:
                    if self.edgeEnd[eventNumber] - self.edgeBegin[eventNumber] < 2*self.minimumEventSamples:
                        nLevels = 0
                        self.meanEventValue[eventNumber][nLevels] = numpy.min(self.rawData[self.edgeBegin[eventNumber]:self.edgeEnd[eventNumber]+1])
                        self.dwellTime[eventNumber][nLevels] = (self.edgeEnd[eventNumber]-self.edgeBegin[eventNumber])*1.0/self.dictOfConstants['ADCSAMPLINGRATE']
                        
                eventNumber += 1
                        
            # baseline = baseline * 0.93 + (1 - 0.93) * dataPoint #Adaptive basline
            # variance_baseline = 0.99 * variance_baseline + (1 - 0.99) * dataPoint
            # variance = 0.99 * variance + (1 - 0.99) * numpy.power(dataPoint - variance_baseline, 2) #Adaptive baseline
            j = numpy.where(localEventIndex == event_i)[0] + 1
            # print eventNumber, i, j, len(localEventIndex), baseline, threshold_end
                
        # self.eventIndex = numpy.empty_like(self.edgeBegin, dtype='object')
        # for i in range(eventNumber):
            # self.eventIndex[i] = numpy.arange(self.edgeBegin[i], self.edgeEnd[i]+1)
        
        print "Finishing"
        
        self.finished.emit()
                    