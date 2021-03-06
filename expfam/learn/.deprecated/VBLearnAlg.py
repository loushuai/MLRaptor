'''
 Variational bayes learning algorithm

Author: Mike Hughes (mike@michaelchughes.com)
'''
import numpy as np
import time

import LearnAlg

class VBLearnAlg( LearnAlg.LearnAlg ):

  def __init__( self, expfamModel, **kwargs ):
    super( type(self), self).__init__( **kwargs )
    self.expfamModel = expfamModel

  def init_params( self, Data, **kwargs):
    self.expfamModel.set_obs_dims( Data )
    LP = dict()
    LP['resp'] = self.init_resp( Data['X'], self.expfamModel.K, **kwargs )
    SS = self.expfamModel.get_global_suff_stats( Data, LP )
    self.expfamModel.update_global_params( SS )
    if 'GroupIDs' in Data:
      LP = self.init_params_perGroup( Data, LP)
    return LP

  def init_params_perGroup(self, Data, LP ):
    GroupIDs = Data['GroupIDs']
    LP['N_perGroup'] = np.zeros( (len(GroupIDs),self.expfamModel.K)  )
    for gg in range( len(GroupIDs) ):
      LP['N_perGroup'][gg] = np.sum( LP['resp'][ GroupIDs[gg] ], axis=0 )
    return LP

  def fit( self, Data, seed ):
    self.start_time = time.time()
    status = 'max iters reached.'
    prevBound = -np.inf

    for iterid in xrange(self.Niter):
      if iterid==0:
        LP = self.init_params( Data, seed=seed )
        LP = self.expfamModel.calc_local_params( Data )
      else:
        # M-step
        self.expfamModel.update_global_params( SS ) 
        # E-step 
        LP = self.expfamModel.calc_local_params( Data )

      SS = self.expfamModel.get_global_suff_stats( Data, LP )
      evBound = self.expfamModel.calc_evidence( Data, SS, LP )

      # Save and display progress
      self.save_state(iterid, evBound)
      self.print_state(iterid, evBound)

      # Check for Convergence!
      #  throw error if our bound calculation isn't working properly
      #    but only if the gap is greater than some tolerance
      isConverged = self.verify_evidence( evBound, prevBound )

      if isConverged:
        status = 'converged.'
        break
      prevBound = evBound

    #Finally, save, print and exit 
    self.save_state(iterid, evBound, doFinal=True) 
    self.print_state(iterid, evBound, doFinal=True, status=status)
    return LP
