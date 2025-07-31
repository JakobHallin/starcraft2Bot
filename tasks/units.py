from sc2.ids.unit_typeid import UnitTypeId
async def build_workers(bot):
    #if bot.townhalls:
    cc = bot.townhalls.first
    ideal_workers = sum(townhall.ideal_harvesters for townhall in bot.townhalls)+1

    if bot.can_afford(UnitTypeId.SCV) and cc.is_idle and bot.workers.amount < ideal_workers:
        bot.do(cc.train(UnitTypeId.SCV))   
        print(f"Train SCV: {bot.workers.amount} / {ideal_workers}")
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