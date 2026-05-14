"""
robot ecosystem operation code

This module creates a test ecosystem and runs it for a specified duration, 
demonstrating the use of the ecosystem factory and deliverable creation functions
It simulates the operation of delivery bots, including charging and delivering pizzas, while providing options for debugging and message display.
"""

from .ecosystem.factory import *

# Duration is set to two weeks for development and rapid testing. Set to 52 weeks for your final tests.

import matplotlib.pyplot as plt
plt.close('all')  # optional: cleans up leftovers from prior runs
plt.ion()         # interactive mode ON (non-blocking windows)

# Create and configure the ecosystem using the factory function. 
# Study the factory function code to understand how the ecosystem is being created 
# and configured. Adjust the parameters as needed for your testing and development.  
es = ecofactory(robots = 3, droids = 3, drones = 3, chargers = ([55,20], [10, 10]), pizzas = 9)



charger = es.chargers()[0]
es.display(show = 1, pause = 2)                                                # show = 0 will turn off the display and speed up the run. Set to 1 for development and debugging, set to 0 for final runs. Note that when show = 0, you will not see the ecosystem or any messages, so it is wise to turn on messages (es.messages_on = True) when show = 0 for development and debugging. 
es.debug = True                                                            # this will directly display damage and warning messages. Note show needs to be zero  (show = 0)
es.messages_on = False                                                          # over 52 weeks it is wise to turn messages off as there are too many. But when researching turn on for shorter runs
es.duration = "1 week"                                                          # We are aiming to run for a year with minimum or no bot breakages

home = [40,20, 0]                                                               # Place to which bots will return when idle and from which they will start. This is also the location of the charger in this example, but it doesn't have to be. You can change this and the charger location to test the bots' ability to navigate around the ecosystem.
charge_threshold = 0.20    



# Helper function to return fraction of remaining charge
def bot_get_charge(bot) -> float:
  return (bot.soc / bot.max_soc)


  

def choose_charger(bot, chargers) -> int:                                                                    
    # Return the index of the nearest charger#
    
    min_dist = math.inf
    min_index = -1
    
    for index, charger in enumerate(chargers):
      dist = distance(charger.coordinates, bot.coordinates)
      if (dist < min_dist):
        min_dist = dist
        min_index = index
    return min_index


# Returns true if a bot has enough charge to complete a job and return to the nearest charger
def has_charge_to_start_job(bot, pizza) -> bool:

  total_dist = (
    distance(bot.coordinates, pizza.coordinates) +
    distance(pizza.coordinates, pizza.destination)
  )

  weight = bot.payload + pizza.weight

  energy_needed = energy_consumption(weight, bot.max_speed, bot.volitant) * total_dist

  nearest = choose_charger(bot, es.chargers())
  charger = es.chargers()[nearest]
  charger_dist = distance(charger.coordinates, bot.coordinates)

  energy_needed += energy_consumption(bot.payload, bot.max_speed, bot.volitant) * charger_dist

  return energy_needed < bot.soc * 0.9

# Helper function to find and choose the nearest charger
def charge_from_nearest(bot, chargers):
  # Prior to being assigned a task, check charge
  nearest_charger = choose_charger(bot, es.chargers())
  #print(f'Nearest Charger Index: {nearest_charger}')
  if (nearest_charger != -1):
    bot.charge(es.chargers()[nearest_charger])
  else:
    print("[ERROR]: No charger found?")
    quit()
  
# Returns true if the first bot can take over the second's job and complete it in a shorter time
def compare_bot_time(bot_main, bot_second, pizza) -> bool:
  # Avoid zero division
  speed_main = max(bot_main.max_speed, 1e-6)
  speed_second = max(bot_second.max_speed, 1e-6)

  # Bot 1 takes over bot 2's job
  main_cost = (
    distance(bot_main.coordinates, pizza.coordinates) +
    distance(pizza.coordinates, pizza.destination)
  ) / speed_main

  # Bot 2 keeps job
  second_cost = (
    distance(bot_second.coordinates, pizza.coordinates) +
    distance(pizza.coordinates, pizza.destination)
  ) / speed_second

  return main_cost < second_cost


def is_pizza_in_weight(pizza, bot):
  return pizza.weight <= (bot.max_payload - bot.payload)

def find_nearest_pizza(bot, pizzas) -> int:
  dist_min = math.inf
  nearest_pizza = -1 # Potentially a cause of crashing / failed interpretation - add bounds checking on access
  
  for pizza_index, pizza in enumerate(pizzas):
    if (not is_pizza_in_weight(pizza, bot)):
      continue # Skip pizzas that would overflow the payload
    if (pizza.status != 'ready'):
      #Only use ready pizzas
      continue
    dist = distance(pizza.coordinates, bot.coordinates)
    if (dist < dist_min):
      dist_min = dist
      nearest_pizza = pizza_index
  return nearest_pizza

while es.active:
  for bot in es.bots():

    #create_deliverables(es)                                                     # Use the create deliverables function to maintain a stock of ready pizzas

    if bot_get_charge(bot) < charge_threshold and bot.station is None:  
      # decision to charge when percent soc = 20%. This can be optimised and varied for each kind (see stretch objective)
      # ISSUE - Optimise by charging near a station when no pizzas are near
      charge_from_nearest(bot, es.chargers())
      #bot.charge(charger)                                                       # initiate charging.
    if bot.activity == 'idle':                                                  # if bot is idle, contract to deliver a ready pizza.
        # Optimisation - use nearest pizza
        pizza_index = find_nearest_pizza(bot, es.deliverables())
        if pizza_index == -1 or (not has_charge_to_start_job(bot, es.deliverables()[pizza_index])): # Boundary checking to avoid crashing
          continue
        pizza = es.deliverables()[pizza_index]
        # Optimisation - Only attempt pizzas of the correct weight
        pizza_under_weight = pizza.weight <= (bot.max_payload - bot.payload)
        if pizza.status == 'ready':
          # ISSUE - non optimal, choose correct bot type
          bot.deliver(pizza)                                             # ensure we do not contract to deliver a pizza already contracted by another bot
          
        if not bot.destination and bot.coordinates != home:
          # IF A SLOWER BOT IS EN ROUTE, FASTER BOT TAKES OVER
          bot.target_destination = home                                           # if we get here, we've gone through the list of pizzas and none was ready
    if bot.target_destination:bot.move()                                        # move whilst we have a destination. At the end of delivery, the bot status will be set to idle

  es.update()                                                                   # update when all bots have been processed and moved



def print_kpis(es, label):
    bots = es.bots()

    delivered_units = sum(bot.units_delivered for bot in bots)
    delivered_weight = sum(bot.weight_delivered for bot in bots)
    total_distance = sum(bot.distance for bot in bots)
    total_energy = sum(bot.energy for bot in bots)
    total_damage = sum(bot.damage for bot in bots)
    broken_bots = sum(1 for bot in bots if bot.status == "broken")

    print(f"\n{label} KPI RESULTS")
    print("-" * 40)
    print(f"{'Delivered units':<25}{delivered_units}")
    print(f"{'Delivered weight':<25}{delivered_weight:.2f}")
    print(f"{'Total distance':<25}{total_distance:.2f}")
    print(f"{'Total energy':<25}{total_energy:.2f}")
    print(f"{'Total damage':<25}{total_damage}")
    print(f"{'Broken bots':<25}{broken_bots}")


print_kpis(es, "Baseline")