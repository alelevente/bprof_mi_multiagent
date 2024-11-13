import numpy as np     
        
class MixedCostDistancePreference:
    def __init__(self, distance_mtx, alpha=0.5):
        assert alpha>0
        self.distance_mtx = distance_mtx
        self.alpha = alpha
        
    """Computes preferences based on alpha*cost+(1-alpha)*distance function.
       That results in prefering closer and cheaper parking against the more expensive and more distant ones.
       (Values gets normalized during calculation.)"""
    def __call__(self, buyer_id, auction_ids, bids):
        max_dist = max(list(self.distance_mtx[buyer_id].values()))
        max_bid = max(list(bids.values()))
        best_val = 10000
        best_auc_id = None
        
        for ac in bids:
            edge = ac.split("auc_pl")[-1]
            edge = edge.split("_")[0]
            pref_fn = self.alpha*bids[ac]/max_bid + (1-self.alpha)*self.distance_mtx[buyer_id][edge]/max_dist
            if pref_fn < best_val:
                best_val = pref_fn
                best_auc_id = ac
            
        return best_auc_id
    
