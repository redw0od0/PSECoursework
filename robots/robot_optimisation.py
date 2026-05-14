


"""
robot ecosystem operation code
"""

from .ecosystem.factory import *
import math

import matplotlib.pyplot as plt
plt.close('all')
plt.ion()


def bot_get_charge(bot) -> float:
  return bot.soc / bot.max_soc


def choose_charger(bot, chargers) -> int:
  min_dist = math.inf
  min_index = -1

  for index, charger in enumerate(chargers):
    dist = distance(charger.coordinates, bot.coordinates)
    if dist < min_dist:
      min_dist = dist
      min_index = index

  return min_index


def has_charge_to_start_job(bot, pizza) -> bool:
  total_dist = (
    distance(bot.coordinates, pizza.coordinates) +
    distance(pizza.coordinates, pizza.destination)
  )

  energy_needed = energy_consumption(
    bot.payload + pizza.weight,
    bot.max_speed,
    bot.volitant
  ) * total_dist

  nearest = choose_charger(bot, es.chargers())
  charger = es.chargers()[nearest]

  charger_dist = distance(charger.coordinates, bot.coordinates)

  energy_needed += energy_consumption(
    bot.payload,
    bot.max_speed,
    bot.volitant
  ) * charger_dist

  return energy_needed < bot.soc * 0.99

def dynamic_charge_threshold(bot):

  chargers = es.chargers()

  nearest_index = choose_charger(bot, chargers)

  if nearest_index == -1:
    return 0.40

  charger = chargers[nearest_index]

  dist_to_charger = distance(bot.coordinates, charger.coordinates)

  # normalised travel risk
  travel_risk = dist_to_charger / 60.0

  # drone penalty
  if bot.volitant:
    base = 0.22
  elif bot.max_speed >= 2:
    base = 0.18
  else:
    base = 0.15

  # workload pressure
  ready_pizzas = sum(
    1 for p in es.deliverables()
    if p.status == "ready"
  )

  workload_bonus = 0

  if ready_pizzas > 8:
    workload_bonus -= 0.05
  elif ready_pizzas < 3:
    workload_bonus += 0.05

  threshold = (
    base +
    travel_risk * 0.25 +
    workload_bonus
  )

  return max(0.10, min(threshold, 0.45))


def charge_from_nearest(bot):
  nearest = choose_charger(bot, es.chargers())

  if nearest == -1:
    print("[ERROR]: No charger found")
    return

  bot.charge(es.chargers()[nearest])


##  PIZZA DECISION OPTIMISATION

def is_pizza_in_weight(pizza, bot):
  return pizza.weight <= (bot.max_payload - bot.payload)

def find_nearest_pizza(bot, pizzas) -> int:
  dist_min = math.inf
  nearest = -1

  for i, pizza in enumerate(pizzas):

    if pizza.status != "ready":
      continue

    if not is_pizza_in_weight(pizza, bot):
      continue

    dist = distance(pizza.coordinates, bot.coordinates)

    if dist < dist_min:
      dist_min = dist
      nearest = i

  return nearest


def print_kpis(es, label):
  bots = es.bots()

  print(f"\n{label} KPI RESULTS")
  print("-" * 40)

  print("Delivered units:", sum(b.units_delivered for b in bots))
  print("Delivered weight:", sum(b.weight_delivered for b in bots))
  print("Total distance:", sum(b.distance for b in bots))
  print("Total energy:", sum(b.energy for b in bots))
  print("Total damage:", sum(b.damage for b in bots))
  print("Broken bots:", sum(1 for b in bots if b.status == "broken"))

def can_keep_moving(bot):
  return bot.soc > bot.max_soc * 0.1 # Can keep moving at 10% charge

def run_modified(duration):

  charger_list = (
    [55, 20]

  )

  global es
  es = ecofactory(robots=3, droids=3, drones=3, chargers=charger_list, pizzas=9)

  es.display(show=0, pause=0.1)
  es.debug = True
  es.messages_on = False
  es.duration = duration


  pizza_swaps = 0

  while es.active:

    for bot in es.bots():
        #charge_threshold = 0.20
      charge_threshold = dynamic_charge_threshold(bot)


      # CHARGING
      if bot_get_charge(bot) < charge_threshold and bot.station is None:
        charge_from_nearest(bot)

      # ASSIGN JOB
      if bot.activity == "idle":

        pizzas = es.deliverables()
        pizza_index = find_nearest_pizza(bot, pizzas)

        if pizza_index == -1:
          continue

        pizza = pizzas[pizza_index]

        if not has_charge_to_start_job(bot, pizza):
          continue

        bot.deliver(pizza)

      # MOVE
      if bot.target_destination:
        # Bail-out when charge is low
        if bot_get_charge(bot) < 0.1 and bot.activity != "charging":
          bot.target_destination = None
          charge_from_nearest(bot)
          continue
        bot.move()

    es.update()

  return collect_kpis(es, "Modified")












def collect_kpis(es, label):
  bots = es.bots()

  delivered = sum(b.units_delivered for b in bots)
  weight = round(sum(b.weight_delivered for b in bots), 2)
  distance_total = round(sum(b.distance for b in bots), 2)
  energy_total = round(sum(b.energy for b in bots), 2)
  damage_total = round(sum(b.damage for b in bots), 2)
  broken = sum(1 for b in bots if b.status == "broken")

  efficiency = 0

  if energy_total > 0:
    efficiency = round(delivered / energy_total, 4)

  return {
    "label": label,
    "delivered": delivered,
    "weight": weight,
    "distance": distance_total,
    "energy": energy_total,
    "damage": damage_total,
    "broken": broken,
    "efficiency": efficiency
  }















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


def print_comparison_table(base, mod):

  print("\n")
  print("=" * 72)
  print("KPI COMPARISON")
  print("=" * 72)

  headers = (
    "Metric",
    "Baseline",
    "Modified",
    "Delta %"
  )

  print(f"{headers[0]:<20}{headers[1]:<15}{headers[2]:<15}{headers[3]:<15}")
  print("-" * 72)

  metrics = [
    ("delivered", "Delivered"),
    ("weight", "Weight"),
    ("distance", "Distance"),
    ("energy", "Energy"),
    ("damage", "Damage"),
    ("broken", "Broken Bots"),
    ("efficiency", "Efficiency")
  ]

  for key, label in metrics:

    b = base[key]
    m = mod[key]

    if b == 0:
      delta = 0
    else:
      delta = ((m - b) / b) * 100

    print(
      f"{label:<20}"
      f"{str(b):<15}"
      f"{str(m):<15}"
      f"{delta:>7.2f}%"
    )

  print("=" * 72)


def run_baseline(duration):
  es = ecofactory(robots = 3, droids = 3, drones = 3, chargers = [55,20], pizzas = 9)
  charger = es.chargers()[0]
  es.display(show = 0, pause = 10)                                                # show = 0 will turn off the display and speed up the run. Set to 1 for development and debugging, set to 0 for final runs. Note that when show = 0, you will not see the ecosystem or any messages, so it is wise to turn on messages (es.messages_on = True) when show = 0 for development and debugging. 
  es.debug = False                                                                # this will directly display damage and warning messages. Note show needs to be zero  (show = 0)
  es.messages_on = False                                                          # over 52 weeks it is wise to turn messages off as there are too many. But when researching turn on for shorter runs
  es.duration = duration                                                          # We are aiming to run for a year with minimum or no bot breakages

  home = [40,20, 0]                                                               # Place to which bots will return when idle and from which they will start. This is also the location of the charger in this example, but it doesn't have to be. You can change this and the charger location to test the bots' ability to navigate around the ecosystem.
  charge_threshold = 0.20                                                         # this is the soc percentage at which bots will decide to charge. This can be optimised and varied for each kind (see stretch objective)                               

  while es.active:

    for bot in es.bots():

      #create_deliverables(es)                                                     # Use the create deliverables function to maintain a stock of ready pizzas

      if bot.soc / bot.max_soc < charge_threshold and bot.station is None:        # decision to charge when percent soc = 20%. This can be optimised and varied for each kind (see stretch objective)
        bot.charge(charger)                                                       # initiate charging.
      if bot.activity == 'idle':                                                  # if bot is idle, contract to deliver a ready pizza.
        for pizza in es.deliverables():
          if pizza.status == 'ready':
            bot.deliver(pizza)                                                    # ensure we do not contract to deliver a pizza already contracted by another bot
            break
        if not bot.destination and bot.coordinates != home:
          bot.target_destination = home                                           # if we get here, we've gone through the list of pizzas and none was ready
      if bot.target_destination:bot.move()                                        # move whilst we have a destination. At the end of delivery, the bot status will be set to idle

    es.update()                                                                   # update when all bots have been processed and moved

  return collect_kpis(es, "Baseline")


duration = '52 week'
baseline = run_baseline(duration)
modified = run_modified(duration)

print_comparison_table(baseline, modified)