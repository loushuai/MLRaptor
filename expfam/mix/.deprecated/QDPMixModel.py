'''
 Factorized Variational Distribution
   for approximating a Dirichlet-Process Gaussian Mixture Model
   using the stick-breaking construction and truncating to at most K components

 Author: Mike Hughes (mike@michaelchughes.com)

 Model
 -------
 for each component k=1...K:
    stick length  v_k ~ Beta( 1, alpha0 )
    mixture weight  w_k <-- v_k * \prod_{l < k}(1-v_l)

 Variational Approximation
 -------
 q( Z, v, mu, Sigma ) = q(Z)q(v)q(mu|Sigma)q(Sigma)

 Parameters
 -------
   alpha0   : scalar hyperparameter of symmetric Dirichlet prior on mix. weights
   
 Inference
 -------
   See VBLearnerGMM.py

 References
 -------
   Pattern Recognition and Machine Learning, by C. Bishop.
'''

import numpy as np
from scipy.special import digamma, gammaln
from ..util.MLUtil import logsumexp, np2flatstr, flatstr2np

EPS = 1e-13
LOGPI = np.log(np.pi)
LOGTWO = np.log(2.00)
LOGTWOPI = np.log( 2.0*np.pi )

class DPMixModel( object ):

  def __init__(self, K, alpha0=1.0, truncType='z', **kwargs):
    self.qType = 'VB' # Cannot do EM for this model!
    self.K = K
    self.alpha1 = 1.0
    self.alpha0 = alpha0    
    self.truncType = truncType

    #  q( v_k ) = Beta( qalpha1[k], qalpha0[k] )
    self.qalpha1 = np.zeros( K )
    self.qalpha0 = np.zeros( K )
  
  def get_info_string( self):
    return 'DP infinite mixture model with %d components' % (self.K)

  def to_string( self ):
    return np2flatstr( self.qalpha0 ) + np2flatstr( self.qalpha1 )
    	
  def calc_local_params( self, Data, LP ):
    ''' 
    '''
    lpr = self.Elogw + LP['E_log_soft_ev']
    lprPerItem = logsumexp( lpr, axis=1 )
    resp   = np.exp( lpr-lprPerItem[:,np.newaxis] ) 
    LP['resp'] = resp
    return LP
    
  def get_global_suff_stats( self, Data, SS, LP ):
    ''' 
    '''
    SS['N'] = np.sum( LP['resp'], axis=0 )
    SS['Nall'] = SS['N'].sum()
    return SS

  def update_global_params( self, SS, rho=None, Ntotal=None, **kwargs ):
    '''
    '''
    ampF = 1
    if Ntotal is not None:
      ampF = Ntotal/SS['Nall']
    qalpha1 = self.alpha1 + ampF*SS['N']
    qalpha0 = self.alpha0*np.ones( self.K )
    qalpha0[:-1] += ampF*SS['N'][::-1].cumsum()[::-1][1:]
    
    if rho is None or rho==1:
      self.qalpha1 = qalpha1
      self.qalpha0 = qalpha0
    else:
      self.qalpha1 = rho*qalpha1 + (1-rho)*self.qalpha1
      self.qalpha0 = rho*qalpha0 + (1-rho)*self.qalpha0
    
    DENOM = digamma( self.qalpha0 + self.qalpha1 )
    self.ElogV      = digamma( self.qalpha1 ) - DENOM
    self.Elog1mV    = digamma( self.qalpha0 ) - DENOM

    if self.truncType == 'v':
      self.qalpha1[-1] = 1
      self.qalpha0[-1] = EPS #avoid digamma(0), which is way too HUGE
      self.ElogV[-1] = 0  # log(1) => 0
      self.Elog1mV[-1] = np.log(1e-40) # log(0) => -INF, never used
			 
    self.Elogw = self.ElogV.copy()
    self.Elogw[1:] += self.Elog1mV[:-1].cumsum()    

  def calc_evidence( self, Data, SS, LP ):
    return self.E_logpZ( LP ) - self.E_logqZ( LP ) \
           + self.E_logpV()   - self.E_logqV() \
           
  def E_logpZ( self, LP ):
    '''
      E[ log p( Z | V ) ] = \sum_n E[ log p( Z[n] | V )
         = \sum_n E[ log p( Z[n]=k | w(V) ) ]
         = \sum_n \sum_k z_nk log w(V)_k
    '''
    return np.sum( LP['resp'] * self.Elogw ) 
    
  def E_logqZ( self, LP ):
    return np.sum( LP['resp'] *np.log(LP['resp']+EPS) )
    

  ############################################################## stickbreak terms
  def E_logpV( self ):
    '''
      E[ log p( V | alpha ) ] = sum_{k=1}^K  E[log[   Z(alpha) Vk^(a1-1) * (1-Vk)^(a0-1)  ]]
         = sum_{k=1}^K log Z(alpha)  + (a1-1) E[ logV ] + (a0-1) E[ log (1-V) ]
    '''
    logZprior = gammaln( self.alpha0 + self.alpha1 ) - gammaln(self.alpha0) - gammaln( self.alpha1 )
    logEterms  = (self.alpha1-1)*self.ElogV + (self.alpha0-1)*self.Elog1mV
    if self.truncType == 'z':
	    return self.K*logZprior + logEterms.sum()    
    elif self.truncType == 'v':
      return self.K*logZprior + logEterms[:-1].sum()

  def E_logqV( self ):
    '''
      E[ log q( V | qa ) ] = sum_{k=1}^K  E[log[ Z(qa) Vk^(ak1-1) * (1-Vk)^(ak0-1)  ]]
       = sum_{k=1}^K log Z(qa)   + (ak1-1) E[logV]  + (a0-1) E[ log(1-V) ]
    '''
    logZq = gammaln( self.qalpha0 + self.qalpha1 ) - gammaln(self.qalpha0) - gammaln( self.qalpha1 )
    logEterms  = (self.qalpha1-1)*self.ElogV + (self.qalpha0-1)*self.Elog1mV
    if self.truncType == 'z':
      return logZq.sum() + logEterms.sum()
    elif self.truncType == 'v':
      return logZq[:-1].sum() + logEterms[:-1].sum()  # entropy of deterministic draw =0
