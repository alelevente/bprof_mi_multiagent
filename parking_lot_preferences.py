import numpy as np

def min_price(buyer_id, auction_ids, bids):
    """Computes preferences based only on current bids."""
    return np.argmin(bids)

class MinDistancePreference:
    """Computes preferences based on distance to a particular parking lot.
       It results in prefering the closest parking alternative against more distant ones."""
    def __init__(self, distance_mtx, parking_capacities):
        self.distance_mtx = {}
        for x in distance_mtx:
            distances = []
            for i in range(len(parking_capacities)):
                for j in range(parking_capacities[i]):
                    distances.append(distance_mtx[x][i])
            self.distance_mtx[x] = distances
            
        self.parking_ranges = []
        last = 0
        for caps in parking_capacities:
            for i in range(caps):
                self.parking_ranges.append(last+caps)
            last = last+caps
            
            
    def __call__(self, buyer_id, auction_ids, bids):
        distance_vector = np.array(self.distance_mtx[buyer_id])
        active_indices = [int(auc_id.split("auc")[-1]) for auc_id in auction_ids]
        distance_vector = distance_vector[active_indices]
        return np.argmin(distance_vector)
        
        
class BalancedCostDistancePreference(MinDistancePreference):
    """Computes preferences based on 0.5*cost+0.5*distance function.
       That results in prefering closer and cheaper parking against the more expensive and more distant ones.
       (Values gets normalized during calculation.)"""
    def __call__(self, buyer_id, auction_ids, bids):
        distance_vector = np.array(self.distance_mtx[buyer_id])
        active_indices = [int(auc_id.split("auc")[-1]) for auc_id in auction_ids]
        distance_vector = distance_vector[active_indices]
        #normalizing into range [0,1]:
        bids = np.array(bids) / max(bids)
        distance_vector = distance_vector / max(distance_vector)
        return np.argmin(bids + distance_vector)
    
class IndividualPreference:
    """Calculates preferences based on a preliminary calculated preference list.
        This may symbolize that one has favorite parking lots."""
    def __init__(self, buyer_ids, auction_count):
        self.preference_lists = {}
        for buyer in buyer_ids:
            self.preference_lists[buyer] = np.random.permutation(auction_count)
            
    def __call__(self, buyer_id, auction_ids, bids):
        pref_vector = self.preference_lists[buyer_id]
        active_indices = [int(auc_id.split("auc")[-1]) for auc_id in auction_ids]
        pref_vector = pref_vector[active_indices]
        return np.min(pref_vector)