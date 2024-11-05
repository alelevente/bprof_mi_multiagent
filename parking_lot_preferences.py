import numpy as np

def min_price(buyer_id, auction_ids, bids):
    """Computes preferences based only on current bids."""
    best_val = 10000
    best_auc_id = None

    for ac in bids:
        pref_fn = bids[ac]
        if pref_fn < best_val:
            best_val = pref_fn
            best_auc_id = ac

    return best_auc_id

class MinDistancePreference:
    """Computes preferences based on distance to a particular parking lot.
       It results in prefering the closest parking alternative against more distant ones."""
    def __init__(self, distance_mtx):
        self.distance_mtx = distance_mtx           
            
    def __call__(self, buyer_id, auction_ids, bids):
        best_val = 10000
        best_auc_id = None
        
        for ac in bids:
            edge = ac.split("auc_pl")[-1]
            edge = edge.split("_")[0]
            pref_fn = self.distance_mtx[buyer_id][edge]
            if pref_fn < best_val:
                best_val = pref_fn
                best_auc_id = ac
            
        return best_auc_id
        
        
class BalancedCostDistancePreference(MinDistancePreference):
    """Computes preferences based on 0.5*cost+0.5*distance function.
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
            pref_fn = bids[ac]/max_bid + self.distance_mtx[buyer_id][edge]/max_dist
            if pref_fn < best_val:
                best_val = pref_fn
                best_auc_id = ac
            
        return best_auc_id
    
