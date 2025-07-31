from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
def scout_enemy_base(bot):
    if bot.enemy_base_location:
        return  # Already found, no need to continue

    # First time setup
    if not bot.scouting_started:
        if bot.units(UnitTypeId.SCV).amount > 0 and bot.enemy_start_locations:
            bot.scout_unit = bot.units(UnitTypeId.SCV).random
            bot.scout_locations = list(bot.enemy_start_locations)
            bot.current_scout_index = 0
            bot.scouting_started = True
            move_scout_to_next_location(bot)
        return

    # Safety check
    if not bot.scout_unit or bot.scout_unit.tag not in bot.units.tags:
        return


    # Check for enemy buildings
    if bot.enemy_structures:
        bot.enemy_base_location = bot.enemy_structures.closest_to(bot.scout_unit).position
        print(f"Enemy base found at {bot.enemy_base_location}")
        return

    # Move to next location
    if bot.time - bot.last_move_time > 20:
        bot.current_scout_index += 1
        if bot.current_scout_index < len(bot.scout_locations):
            move_scout_to_next_location(bot)
        else:
            print("Scouting complete. No enemy base found.")
            bot.scout_unit = None  # stop scouting

def move_scout_to_next_location(bot):
    target = bot.scout_locations[bot.current_scout_index]
    bot.scout_unit.move(target)
    bot.last_move_time = bot.time
    print(f"Moving scout to location {bot.current_scout_index + 1}: {target}")


async def attack_enemy(bot):
    marines = bot.units(UnitTypeId.MARINE)
    if marines.amount >= 12:
        target = bot.enemy_base_location  
        for marine in marines.idle: 
            bot.do(marine.attack(target))
        print(f"Attacking enemy base with {marines.amount} marines")

