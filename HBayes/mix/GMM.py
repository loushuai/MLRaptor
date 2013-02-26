'''
  Represents classic Bayesian Gaussian mixture model
    with a finite number of components K

 Author: Mike Hughes (mike@michaelchughes.com)

 Parameters
 -------
   alpha0   : scalar hyperparameter of symmetric Dirichlet prior on mix. weights
   obsPrior : Python object that represents prior on emission params
                  conventionally, obsPrior = Gaussian-Wishart distribution 
                    see GaussWishDistr.py
   
 Usage
 -------
   gw   = GaussWishDistr( dF=3, invW=np.eye(2)  )
   qgmm = MixModel( K=10, alpha0=0.1, obsPrior=gw )

 Inference
 -------
   See VBLearner.py  or EMLearner.py

 References
 -------
   Pattern Recognition and Machine Learning, by C. Bishop.
'''
import MixModel
import numpy as np

from ..obsModel.GaussDistr import GaussDistr

class GMM( MixModel.MixModel ):

  def __init__( self, K, alpha0 ):
    super(GMM, self).__init__( K, alpha0 )
    self.obsDistr = [ None for k in xrange(self.K)]
    self.min_covar = 1e-8

  def update_obs_params( self, SS, rho=None):
    ''' M-step update
    '''
    if rho is None:
      for k in xrange( self.K ):
        self.obsDistr[k] = GaussDistr( SS['mean'][k], SS['covar'][k]+self.min_covar )
        				 
    else:
		  for k in xrange( self.K ):
				self.obsDistr[k].mu = rho* SS['mean'][k] + (1-rho)*self.obsDistr[k].mu
				self.obsDistr[k].Sigma = rho* SS['covar'][k] + (1-rho)*self.obsDistr[k].Sigma
				self.obsDistr[k].Sigma += self.min_covar

  def calc_soft_evidence_mat( self, X ):
    N,D = X.shape
    lpr = np.empty( (X.shape[0], self.K) )
    for k in xrange( self.K ):
      lpr[:,k] = self.obsDistr[k].log_pdf( X )
    return lpr 

  def set_dims( self, Data ):
    self.D = Data['X'].shape[1]

  def get_obs_suff_stats( self, SS, Data, LP ):
    ''' 
    '''
    if type(Data) is dict:
      X = Data['X']
    else:
      X = Data
    resp = LP['resp']

    SS['mean'] = np.dot( resp.T, X ) / SS['N'][:, np.newaxis]
    SS['covar'] = np.empty( (self.K, self.D, self.D) )
    for k in range( self.K):
      Xdiff = X - SS['mean'][k]
      SS['covar'][k] = np.dot( Xdiff.T * resp[:,k], Xdiff )
      SS['covar'][k] /= SS['N'][k]
    return SS
