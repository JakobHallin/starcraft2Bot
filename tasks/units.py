from sc2.ids.unit_typeid import UnitTypeId
async def build_marines(bot):
    for barracks in bot.structures(UnitTypeId.BARRACKS).ready.idle:
        
        if bot.can_afford(UnitTypeId.MARINE):
            bot.do(barracks.train(UnitTypeId.MARINE))
            print("Training Marine")
async def build_marauders(bot):
    for barracks in bot.structures(UnitTypeId.BARRACKS).ready.idle:
        if barracks.has_add_on:
            if bot.can_afford(UnitTypeId.MARAUDER):
                bot.do(barracks.train(UnitTypeId.MARAUDER))
                print("Training Marauder")