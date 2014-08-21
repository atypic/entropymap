import sys
sys.path.append('/home/evo/mecobo/Thrift interface/gen-py/NascenseAPI_v01e')

import emEvolvableMotherboard
from ttypes import *
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from itertools import *
from zlib import *

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def int2base(x,b,alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    'convert an integer to its string representation in a given base'
    if b<2 or b>len(alphabet):
        if b==64: # assume base64 rather than raise error
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        else:
            raise AssertionError("int2base base out of range")
    if type(x) == complex: # return a tuple
        return ( int2base(x.real,b,alphabet) , int2base(x.imag,b,alphabet) )
    if x<=0:
        if x==0:
            return alphabet[0]
        else:
            return  '-' + int2base(-x,b,alphabet)
    # else x is non-negative real
    rets=''
    while x>0:
        x,idx = divmod(x,b)
        rets = alphabet[idx] + rets
    return rets


#transport = TSocket.TSocket('localhost', 9090)
transport = TSocket.TSocket('129.241.102.247', 9090)
transport = TTransport.TBufferedTransport(transport)
prot = TBinaryProtocol.TBinaryProtocol(transport)
cli = emEvolvableMotherboard.Client(prot)
transport.open()
cli.ping()


#pins = [20,21,22,24,25,26,27,28,29]
pins = range(2,14)
recpin = 9
pins.remove(recpin)

npins = len(pins)

freqs = [1000, 100000, 10000000]
configs = [int2base(i,3).zfill(npins) for i in xrange(0,3**npins)]
print "Running ", len(configs), " configurations."
#run each config.
compressings = []
xvals = []
counter = 0
resps = []
for conf in configs:

    cli.reset()
    cli.clearSequences()

    rit = emSequenceItem()
    rit.pin = [recpin]
    rit.startTime = 0
    rit.frequency = 44000
    rit.endTime = 100
    rit.waveFormType = emWaveFormType().PWM
    rit.operationType = emSequenceOperationType().RECORD
    cli.appendSequenceAction(rit)
    
    pidx = 0
    for i in conf:
        it = emSequenceItem()
        it.pin = [pins[pidx]]
        pidx += 1
        it.startTime = 0
        it.endTime = 100
        it.operationType = emSequenceOperationType().DIGITAL
        it.frequency = freqs[int(i)]
        it.cycle = 50
        cli.appendSequenceAction(it)
    #    print it
    cli.runSequences()
    cli.joinSequences()
    #get recordinnnnng
    resp = cli.getRecording(recpin).Samples
    comp = len(compress(''.join(imap(str, resp))))-12  #-12 for constant length zlib string
    print  conf,comp,resp
    compressings.append(comp)
    xvals.append(counter)
    resps.append(resp)
    counter += 1

plt.scatter(xvals, compressings)
plt.savefig("plot.pdf")
plt.savefig("plot.png")

transport.close()
