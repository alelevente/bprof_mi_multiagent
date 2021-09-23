import numpy as np


############################################
# Buyer implementation:
class Buyer:
    def __init__(self, auctions, max_bid, pref_function, buyer_id=""):
        self.auctions = auctions[:]
        self.max_bid = max_bid
        self.act_bids = [0 for i in range(len(auctions))]
        self.preference = 0
        self.pref_function = pref_function
        self.auction_won = False
        self.overbid = True
        self.id = buyer_id
        
    def ask_bid(self, auction, current_bid):
        if (current_bid > self.max_bid) or (self.auction_won):
            return False
        
        idx = self.auctions.index(auction) #identifying auction
        #collecting current bids:
        bids = self.act_bids
        bids[idx] = current_bid 
        if self.overbid:
            #calculating preferences:
            current_preference = self.pref_function(self, bids)
            self.overbid = current_preference != idx #buyer is not overbid when he accepts the bid
            return current_preference == idx
        
    def tell_overbid(self, auction):
        self.overbid = True
    
    def tell_won(self, auction):
        self.auction_won = True
    
#############################################
# Auctioneer implementation:
class Auctioneer:
    def __init__(self, starting_price, bid_step):
        self.starting_price = starting_price
        self.current_price = starting_price
        self.bid_step = bid_step
        self.buyers = []
        self.winner = None
        self.no_winner = 0
        self.status = "running" #status of the auction
        
    def add_buyer(self, buyer):
        self.buyers.append(buyer)
        
    def make_auction_round(self):
        if self.status != "running": return
        #check if buyers want to bid at the current price:
        was_winner = False
        for buyer in self.buyers:
            if buyer.ask_bid(self, self.current_price):
                #buyer is willing to give the current bid
                if not(self.winner is None):
                    self.winner.tell_overbid(self) #telling previous winner that he is no longer winning
                self.current_price += self.bid_step #price increased
                self.winner = buyer #setting current winner
                self.no_winner = 0 #bid received
                was_winner = True
        
        if not(was_winner):
            self.no_winner += 1
        
        if self.no_winner >= 3:
            #Going once, going twice, then its gone!
            if not(self.winner is None):
                self.status = "won"
                self.winner.tell_won(self)
            else:
                self.status = "terminated"
                
                
#############################################
# Running auctions:

def _check_run_conditions(auctions, buyers):
    """Checks whether the auctions shall run one more round."""
    #if len(auctions)<=len(buyers):
    num_running = 0
    for auction in auctions:
        if auction.status == "running": num_running += 1
    return num_running > 0
    #else:
    #    num_won = 0
    #    for buyer in buyers:
    #        if buyer.auction_won: num_won += 1
    #    return num_won < len(buyers)

def run_auctions(auctions, buyers, run_to_completeness=True):
    #initializing auctions:
    for buyer in buyers:
        for auction in auctions:
            auction.add_buyer(buyer)
            
    #running auctions:
    while _check_run_conditions(auctions, buyers):
        for auction in auctions:
            auction.make_auction_round()
            
    #collecting results:
    auctions_won = []
    auctions_terminated = []
    for auction in auctions:
        if auction.status == "won":
            auctions_won.append(
                {"auction_index": auctions.index(auction),
                 "buyer_index": buyers.index(auction.winner),
                 "price": auction.current_price-auction.bid_step})
        else:
            auctions_terminated.append(auction)
            
    if not(run_to_completeness): return auctions_won
    #when running to completeness:
    buyer_map = []
    for i in range(len(buyers)):
        if not(buyers[i].auction_won):
            buyer_map.append(i)
               
    #initializing new participants:
    new_auctions, new_buyers = [], [] #lists of new participants
    auction_map = [] # mapping new indices to the original ones
    
    #creating new auctions:
    for auction in auctions_terminated:
        new_auction = Auctioneer(auction.starting_price, auction.bid_step)
        new_auctions.append(new_auction)
        auction_map.append(auctions.index(auction))
    #creating new buyers:
    for i in buyer_map:
        new_buyer = Buyer(new_auctions, buyers[i].max_bid, buyers[i].pref_function, buyers[i].id)
        new_buyers.append(new_buyer)
    if (len(new_auctions) > 0) and (len(new_buyers) > 0):
        new_run_results = run_auctions(new_auctions, new_buyers, run_to_completeness)
        
        #mapping back to original indices:
        for result in new_run_results:
            auctions_won.append({
                "auction_index": auction_map[result["auction_index"]],
                "buyer_index": buyer_map[result["buyer_index"]],
                "price": result["price"]
            })
    return auctions_won