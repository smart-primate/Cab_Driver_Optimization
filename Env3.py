# Import routines

import numpy as np
import math
import random
from itertools import permutations

# Defining hyperparameters
m = 5 # number of cities, ranges from 1 ..... m
t = 24 # number of hours, ranges from 0 .... t-1
d = 7  # number of days, ranges from 0 ... d-1
C = 5 # Per hour fuel and other costs
R = 9 # per hour revenue from a passenger

""" 
    Note on location numbering:
    The states (locations) at which the cab driver can be located are numbered from 1 to 5 in our MDP.
    This is contrary to how it is defined in the Time Matrix, where the locations are numbered 0 to 4. 
    Hence, we use the MDP definition of the location numbering, but subtract '1' from it whenever the Time Matrix needs to be referred.
"""

class CabDriver():

    def __init__(self):
        """initialise your state and define your action space and state space"""
        # Including all possible permutaions of the actions (source,destination), including no action, 
        # i.e. remaining in respective current state 
                      
        self.action_space = [(0,0)]  + list(permutations([i for i in range(1,m+1)], 2))
        self.state_space = [[x,y,z] for x in range(1,m+1) for y in range(t) for z in range(d)]
        self.state_init = random.choice(self.state_space)   # Random initialization.

        # Start the first round
        self.reset()


    ## Encoding state (or state-action) for NN input

    def state_encod_arch1(self, state):
        """convert the state into a vector so that it can be fed to the NN. This method converts a given state into a vector format. Hint: The vector is of size m + t + d."""
        
        # initialize vector state
        state_encod = [0 for x in range(m+t+d)]
        
        # Encode location
        state_encod[state[0]-1] = 1
        
        # Encode hour of day
        state_encod[m + state[1]] = 1
        
        # Encode day of week
        state_encod[m + t + state[2]] = 1
        
        return state_encod

    # Use this function if you are using architecture-2 
    # def state_encod_arch2(self, state, action):
    #     """convert the (state-action) into a vector so that it can be fed to the NN. This method converts a given state-action pair into a vector format. Hint: The vector is of size m + t + d + m + m."""
  
    #     return state_encod


    ## Getting number of requests

    def requests(self, state):
        """Determining the number of requests basis the location. 
        Use the table specified in the MDP and complete for rest of the locations"""
        location = state[0]
        if location == 1:
            requests = np.random.poisson(2)
        if location == 2:
            requests = np.random.poisson(12)
        if location == 3:
            requests = np.random.poisson(4)
        if location == 4:
            requests = np.random.poisson(7)
        if location == 5:
            requests = np.random.poisson(8)

        # limiting number of requests to 15, as prescribed in MDP document.
        if requests >15:
            requests =15
        
        possible_actions_index = random.sample(range(1, (m-1)*m +1), requests) + [0]
        actions = [self.action_space[i] for i in possible_actions_index]
    
        return possible_actions_index,actions   



    def reward_func(self, state, action, Time_matrix):
        """Takes in state, action and Time-matrix and returns the reward
        
        reward = (revenue earned from pickup point ? to drop point ?) - 
                 (Cost of battery used in moving from pickup point ? to drop point ?) - 
                 (Cost of battery used in moving from current point ? to pick-up point ?)        
        """
        
        next_state, wait_time, transit_time, ride_time = self.next_state_func(state, action, Time_matrix)

        revenue_time = ride_time
        idle_time = wait_time + transit_time
        
        # Calculate reward
        reward = (R * revenue_time) - (C * (revenue_time + idle_time))

        return reward

    

    def next_state_func(self, state, action, Time_matrix):
        """Takes state and action as input and returns next state"""
        
        curr_loc = state[0]
        curr_time = state[1]
        curr_day = state[2]
        pickup_loc = action[0]
        drop_loc = action[1]
        
        # reward depends on time, initializing relevant variables
        total_time = 0
        wait_time = 0
        ride_time = 0
        transit_time = 0
        
        # next state depends on possible actions taken by cab driver. There are 3 cases for the same.
        
        # 1. Cab driver refuses i.e. action (0,0)
        if (pickup_loc == 0) and (drop_loc == 0):
            wait_time = 1
            next_loc = curr_loc
        
        # 2. Driver wants to have pickup and is at same location
        elif pickup_loc == curr_loc:
            ride_time = Time_matrix[curr_loc-1][drop_loc-1][curr_time][curr_day]
            next_loc = drop_loc
            
        ## 3. Driver wants to pickup and is at different location
        else:
            transit_time = Time_matrix[curr_loc-1][pickup_loc-1][curr_time][curr_day]
            updated_time, updated_day = self.get_updated_day_time(curr_time, curr_day, transit_time)
            ride_time =  Time_matrix[pickup_loc-1][drop_loc-1][updated_time][updated_day]
            next_loc  = drop_loc
            curr_time = updated_time
            curr_day = updated_day
        
        total_time = ride_time + wait_time
        updated_time, updated_day = self.get_updated_day_time(curr_time, curr_day, total_time)
        next_state = [next_loc, updated_time, updated_day]        
        
        return next_state, wait_time, transit_time, ride_time

    
    def get_updated_day_time(self, time, day, duration):
        '''
        Takes the current day, time and time duration and returns updated day and time based on the time duration of travel
        '''
        if time + int(duration) < 24:     # no need to change day
            updated_time = time + int(duration)
            updated_day = day
        else:
            updated_time = (time + int(duration)) % 24
            days_passed = (time + int(duration)) // 24
            updated_day = (day + days_passed ) % 7
        return updated_time, updated_day


    def reset(self):
        self.state_init = random.choice(self.state_space)
        return self.action_space, self.state_space, self.state_init
