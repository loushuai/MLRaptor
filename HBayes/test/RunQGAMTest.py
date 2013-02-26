from ..data import ToyData
from ..obsModel.GaussWishDistr import GaussWishDistr
from ..admix.QGAM import QGAM
from ..learn.VBLearnAlg import VBLearnAlg

import numpy as np
import time

def demoQGMM():
  np.random.seed( hash(time.time()) % 10000 )
  seed = np.random.randint(100000)
  print 'SEED:', seed
  print '------------'

  gw = GaussWishDistr( D=5 )

  qgam = QGAM( K=3, alpha0=0.5, obsPrior=gw)

  vb = VBLearnAlg( qgam, printEvery=1, nIter=100, initname='random')
 
  Data =ToyData.get_data_by_groups(seed=seed)
  LP = vb.fit( Data, seed=seed )
  
  np.set_printoptions( linewidth=120, precision=3, suppress=True)
  print 'Learned W __ per group'
  print np.exp( LP['Elogw_perGroup'] )[-10:]
  print 'True W __ per group'
  print Data['TrueW_perGroup'][-10:]

if __name__ == '__main__':
  demoQGMM()
