from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId


#suplly depots
async def build_supply_depots(bot):
    if bot.supply_left < 5 and not bot.already_pending(UnitTypeId.SUPPLYDEPOT):
        ccs = bot.townhalls.ready
        if ccs.exists and bot.can_afford(UnitTypeId.SUPPLYDEPOT):
            location = ccs.first.position.towards(bot.game_info.map_center, 5)
            await bot.build(UnitTypeId.SUPPLYDEPOT, near=location)




#build comand center
async def expand(bot):
    if bot.can_afford(UnitTypeId.COMMANDCENTER) and bot.townhalls.ready.exists:
        await bot.expand_now()


async def build_refinery(bot):
    if bot.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1:
        if bot.can_afford(UnitTypeId.REFINERY) and bot.gas_buildings.amount < 2:
            vgs = bot.vespene_geyser.closest_to(bot.townhalls.first)
            if vgs:
                worker = bot.workers.closest_to(vgs)
                if worker:
                    bot.do(worker.build(UnitTypeId.REFINERY, vgs))
                    print("Building Refinery")


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
            worker = bot.workers.random_or(None)
            cc = bot.townhalls.ready.first
            if worker and cc:
                build_pos = cc.position.towards(bot.game_info.map_center, 10)
                await bot.build(UnitTypeId.BARRACKS, near=build_pos)
                print(f"Building Barracks near {build_pos.rounded}")


async def build_techlab(bot):
    for barracks in bot.structures(UnitTypeId.BARRACKS).ready.idle:
        # Check if we can build a Tech Lab and if the barracks has no addon
        if not barracks.has_add_on and bot.can_afford(UnitTypeId.TECHLAB):
            # Build the Tech Lab
            bot.do(barracks(AbilityId.BUILD_TECHLAB_BARRACKS))
            bot.techlab_built = True
            print(f"Building Tech Lab on {barracks.tag}")