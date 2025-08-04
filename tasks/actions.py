from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
#curently not working
def scout_enemy_base(bot):
    if bot.enemy_base_location:
        print(f"Enemy base already found at {bot.enemy_base_location}. No need to scout further.")
        return  # Already found, no need to continue

    # First time setup
    if not bot.scouting_started:
        if bot.units(UnitTypeId.SCV).amount > 0 and bot.enemy_start_locations:
            


            available_worker = bot.worker_manager.get_available_workers()
            if available_worker.exists:
                scout = available_worker.random
            else:
                print("No available SCV to scout.")
                return 

            bot.scout_unit = scout# scout_unit
            
            bot.worker_manager.reserve_for_scout(scout)
            bot.scout_locations = list(bot.enemy_start_locations)
            bot.current_scout_index = 0
            bot.scouting_started = True
            move_scout_to_next_location(bot)
        return

    # Safety check
    if not bot.scout_unit or bot.scout_unit.tag not in bot.units.tags:
        print("Scout unit is not available or has been lost.")
        return


    # Check for enemy buildings
    if bot.enemy_structures:
        bot.enemy_base_location = bot.enemy_structures.closest_to(bot.scout_unit).position
        #unsure what to do with the scout unit after finding the enemy base
       # print(f"Enemy base found at {bot.enemy_base_location}")
       # bot.worker_manager.release_worker(bot.scout_unit)  # Release the scout worker
       # bot.scout_unit = None  # stop scouting
        return

   
    if bot.scout_unit: #need to update the scout unit to get the new position
        live_scout = bot.units.find_by_tag(bot.scout_unit.tag)
        if live_scout:
            bot.scout_unit = live_scout  # Refresh with live object
        else:
            print("Scout unit is missing or dead.")
            bot.scout_unit = None
            return
    else:
        print("No scout unit assigned.")
        return

    current_target = bot.scout_locations[bot.current_scout_index]
    print(f"[Frame {bot.time}] SCV Position: {bot.scout_unit.position} | Target: {current_target}")
    print(f"Distance: {bot.scout_unit.distance_to(current_target)}")
     # Move to next location
    if bot.scout_unit.distance_to(current_target) < 10:
        bot.current_scout_index += 1
        print(f"Scouting scout index { bot.current_scout_index}")
        if bot.current_scout_index < len(bot.scout_locations):
            move_scout_to_next_location(bot)
        else:
            print("Scouting complete. No enemy base found.")
            bot.worker_manager.release_worker(bot.scout_unit)  # Release the scout worker
            
            bot.scout_unit = None  # stop scouting


def move_scout_to_next_location(bot):
    target = bot.scout_locations[bot.current_scout_index]
    bot.scout_unit.move(target)
    bot.last_move_time = bot.time
    print(f"Moving scout to location {bot.current_scout_index + 1}: {target} with tag {bot.scout_unit.tag} ")


async def attack_enemy(bot):
    marines = bot.units(UnitTypeId.MARINE)
    if marines.amount >= 12:
        target = bot.enemy_base_location  
        for marine in marines.idle: 
            bot.do(marine.attack(target))
        print(f"Attacking enemy base with {marines.amount} marines")

