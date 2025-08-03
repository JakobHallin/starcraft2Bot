from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


#suplly depots
async def build_supply_depots(bot):
    if bot.supply_left < 5 and not bot.already_pending(UnitTypeId.SUPPLYDEPOT):
        ccs = bot.townhalls.ready
        location = ccs.first.position.towards(bot.game_info.map_center, 5)
        available_workers = bot.workers.filter(
                lambda w: not w.is_constructing_scv and w.tag not in bot.builders_in_progress
            )
        builder: Unit = available_workers.closest_to(location)

        bot._unassign_worker(builder)                # ← THE critical line
        bot.workers_reserved_for_tasks.add(builder.tag)
        if ccs.exists and bot.can_afford(UnitTypeId.SUPPLYDEPOT):
            print("Build Supply Depot")
            await bot.build(UnitTypeId.SUPPLYDEPOT, near=location, build_worker=builder)
            print("building supply depot at", location)
            
              # Reassign workers after building a supply depot
            #await bot.build(UnitTypeId.SUPPLYDEPOT, near=location)






#build comand center
async def expand(bot):
    if bot.can_afford(UnitTypeId.COMMANDCENTER) and bot.townhalls.ready.exists:
        await bot.expand_now()



#build refinery
async def build_refinery(bot):
    if bot.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1:
        if bot.can_afford(UnitTypeId.REFINERY):
            ccs = bot.townhalls.ready
            if not ccs.exists:
                return  # No Command Centers ready

            cc = ccs.first
            geysers = bot.vespene_geyser.closer_than(15, cc)

            for vgs in geysers:
                # Skip if Refinery is already built
                if bot.gas_buildings.closer_than(1.0, vgs).exists:
                    continue

                # Skip if a Refinery is pending on this geyser
                if bot.gas_buildings.filter(lambda r: r.position.distance_to(vgs.position) < 1.0 and not r.is_ready).exists:
                    continue

                # Get available SCVs
                available_workers = bot.workers.filter(
                    lambda w: not w.is_constructing_scv and w.tag not in bot.builders_in_progress
                )
                if not available_workers.exists:
                    return  # No free workers

                builder = available_workers.closest_to(vgs)

                # Assign worker
                bot._unassign_worker(builder)
                bot.workers_reserved_for_tasks.add(builder.tag)

                await bot.build(UnitTypeId.REFINERY, vgs, build_worker=builder)
                print(f"Building Refinery {vgs.tag}")

                return  # Build only one Refinery per frame



async def build_orbiltal_command(bot):
    for cc in bot.townhalls.ready:
        if cc.type_id == UnitTypeId.COMMANDCENTER and bot.can_afford(UnitTypeId.ORBITALCOMMAND):
            bot.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))






#baracks
async def build_barracks(bot):
    total_barracks = bot.structures(UnitTypeId.BARRACKS).amount + bot.already_pending(UnitTypeId.BARRACKS)
    num_cc = bot.structures(UnitTypeId.COMMANDCENTER).amount
    num_orbitals = bot.structures(UnitTypeId.ORBITALCOMMAND).amount
    bot.max_barracks = 1 + num_cc * 2 + num_orbitals * 2 # Increase max barracks based on command centers
    if bot.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1 and total_barracks <  bot.max_barracks:
        if bot.can_afford(UnitTypeId.BARRACKS) and bot.townhalls.ready.exists:
            ccs = bot.townhalls.ready
            location = ccs.first.position.towards(bot.game_info.map_center, 5)
            builder: Unit = bot.workers.closest_to(location)
            bot._unassign_worker(builder)
            bot.workers_reserved_for_tasks.add(builder.tag)

            #worker = bot.workers.random_or(None)
            cc = bot.townhalls.ready.first
            #if worker and cc:
            build_pos = cc.position.towards(bot.game_info.map_center, 10)
            await bot.build(UnitTypeId.BARRACKS, near=build_pos, build_worker=builder)
            print(f"Building Barracks near {build_pos.rounded}")


async def build_techlab(bot):
    for barracks in bot.structures(UnitTypeId.BARRACKS).ready.idle:
        # Check if we can build a Tech Lab and if the barracks has no addon
        if not barracks.has_add_on and bot.can_afford(UnitTypeId.TECHLAB):
            # Build the Tech Lab
            bot.do(barracks(AbilityId.BUILD_TECHLAB_BARRACKS))
            bot.techlab_built = True
            print(f"Building Tech Lab on {barracks.tag}")