"""Contains useful functions and definitions for the measurement tasks"""

import os, sys
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET

import traci
SUMO_HOME = os.environ["SUMO_HOME"] #locating the simulator
sys.path.append(SUMO_HOME+"/tools")
import sumolib

import auction

############################################
#          Miscellaneous functions         #
############################################

def read_movements(filename: str) -> list:
    '''Reads the given route file and returns the edges of the routes'''
    
    movements = []
    
    for vehicle in sumolib.xml.parse(filename, "vehicle"):
        route = vehicle.route[0] # access the first (and only) child element with name 'route'
        edges = route.edges.split()
        movements.append(edges)
        
    return movements


def get_distance_to_parkings(traci, vehicle_id: str, sumo_parkings_lane_id: list) -> np.array:
    '''Collecting distances of parking lots for each vehicles'''
    distances = []
    for p in sumo_parkings_lane_id:
        distances.append(traci.simulation.getDistanceRoad(
            traci.vehicle.getRoadID(vehicle_id), 0, p, 0))
    return distances


def read_pl_capacities(filename: str) -> (list,list):
    '''Reads an additional file that contains parking lot definitions. Returns the parking lot ids and the corresp. capacities'''
    tree = ET.parse(filename)
    root = tree.getroot()
    p_ids = []
    p_capacities = []
    for parea in root:
        p_ids.append(parea.attrib["id"])
        p_capacities.append(parea.attrib["roadsideCapacity"])
    return p_ids, p_capacities


def init_auction_method(parking_capacities, vehicle_ids, starting_prices, preference_function, bid_step = 10, max_price = 1000)-> (list, list):
    """Initializes the participants of the auction method
       -------------
       parameters:
           - parking_capacities: capacity values of the parking lots (number of auctions),
           - vehicle_ids: IDs of vehicles (buyers),
           - starting_prices: list of starting prices of the auctions,
           - preference_function: the function that calculates which parking lot is preferred.
                                   signature: preference_function(buyer_object, current_price_list),
           - bid_step: amount of money by which current bids will be increased during auctions,
           - max_price: maximum price that the buyers are willing to accept"""
    
    auctions = []
    buyers = []
    
    for pcap in parking_capacities:
        for i in range(pcap):
            auctions.append(auction.Auctioneer(starting_prices[len(auctions)], bid_step, "auc%d"%i))
            
    buyers = [auction.Buyer(auctions, max_price, preference_function, buyer_id=vehicle_ids[i]) for i in range(len(vehicle_ids))]
    return auctions, buyers

def map_auction_to_parking_area(auction_id, parking_capacities, parking_ids):
    i, tot = 0, 0
    auction_index = int(auction_id.split("auc")[-1])
    if auction_index == 0:
        return parking_ids[0]
    while tot != auction_index:
        if parking_capacities[i]+tot >= auction_index:
            return parking_ids[i]
        else:
            tot += parking_capacities[i]
            i += 1
            
def auction_results_to_parking_mapping(auction_results, buyers, parking_capacities, parking_ids):
    result_map = {}
    for i, auc in enumerate(auction_results):
        p_area = map_auction_to_parking_area(auc["auction_id"], parking_capacities, parking_ids)
        result_map[auc["buyer_id"]] = p_area
    return result_map

############################################
#            Simulation functions          #
############################################

def run_basic_simulation(gui_needed: bool, scenario: str):
    '''Runs a basic SUMO simulation.
        -----------------------
        parameters:
        - gui-needed: if true SUMO is started with GUI
        - scenario: path to the .sumocfg file to run'''
    
    sumo_binary = "sumo-gui" if gui_needed else "sumo"
    sumo_cmd = [sumo_binary, "-c", scenario]
    if gui_needed:
        sumo_cmd.append("-d")
        sumo_cmd.append("200")
    #starting SUMO server:
    traci.start(sumo_cmd)
    
    #conducting the simulation:
    step = 0
    while step < 600:
        step += 1
        traci.simulationStep()
    
    traci.close()
    

def init_controlled_simulation(gui_needed: bool, scenario: str, output_file, movements: list, parking_lot_file: str):
    '''Initializes a TraCI-controlled simulation. Runs simulation until each vehicles get departed.
       Returns obtained distances to parking lots, parking lot ids and parking lot capacities.
       ----------------
       parameters:
        - traci_commands: commands to start TraCI with,
        - movements: list of the edges simulated vehicles shall go through,
        - parking_lot_file: path to the file defining parkingAreas
        
       returns:
        the distances between vehicles and parking lots, parking lot ids, parking lot capacities, vehicle ids'''
    #preparing command line parameters for SUMO and TraCI:
    traci_commands = []
    if gui_needed:
        traci_commands.append("sumo-gui")
    else:
        traci_commands.append("sumo")
    traci_commands.append("-c")
    traci_commands.append(scenario)
    traci_commands.append("--summary-output")
    traci_commands.append(output_file)
    
    traci.start(traci_commands)
    
    #running simulation until each vehicles get departed:
    dep_num = 0
    while dep_num < len(movements):
        traci.simulationStep()
        dep_num += traci.simulation.getDepartedNumber()
    
    #collecting parking capacities:
    p_ids, p_caps = read_pl_capacities(parking_lot_file)
    distances = {}
    p_edges = [p_id.split("pl")[-1] for p_id in p_ids]
    veh_ids = traci.vehicle.getIDList()
    for id_ in veh_ids:
        distances[id_] = get_distance_to_parkings(traci, id_, p_edges)
    
    return distances, p_ids, p_caps, veh_ids



def simulate_after_auction(traci, parking_mapping, max_step = 600):
    """Conducts simulations until a given timestamp. Within each step,
        the function tries to redirect vehicles to a designated parking lot.
        ----------------
        parameters:
        traci: a TraCI object,
        parking_mapping: a map that assigns vehicles (keys) to parking lots (values),
        max_step: simulation will run until this timestamp is reached"""
    
    step = 1
    while step < max_step:
        step += 1
        traci.simulationStep()
             
        #redirecting vehicles to parking lots:
        veh_list = traci.vehicle.getIDList()
        for v in veh_list:
            try:
                traci.vehicle.changeTarget(v, parking_mapping[v].split("pl")[-1])
                traci.vehicle.setParkingAreaStop(v, parking_mapping[v], duration=86400)
            except:
                pass
    traci.close

############################################
#        Output processing functions       #
############################################
def get_stopped_vehicles_from_output(output_file: str):
    '''Extracts number of stopped vehicles from a simulation summary output.
        ------------------------
        parameters:
        - output_file: the simulation output to parse
        
        Returns: time and #stopped vehicle pairs'''
    
    t, v = [], [] #(time x value) pairs
    for time, val in sumolib.xml.parse_fast(output_file, "step", ("time", "stopped")):
        t.append(sumolib.miscutils.parseTime(time))
        v.append(float(val))
    return t,v

def plot_stopped_vehicles(time_values, stopped_values, titles):
    fig, ax = plt.subplots()
    
    for i in range(len(time_values)):
        ax.plot(time_values[i],
                np.array(stopped_values[i])/max(stopped_values[i])*100,
                label=titles[i])
        
    ax.set_xlabel("timestep")
    ax.set_ylabel("% of stopped vehicles")
    ax.set_title("Number of stopped vehicles")
    ax.legend()
    return fig, ax