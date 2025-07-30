from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class MyBot(BotAI):
    async def on_step(self, iteration):
        #print(f"Step {iteration}")
        if self.townhalls:
            cc = self.townhalls.first
            if self.can_afford(UnitTypeId.SCV) and cc.is_idle:
                    self.do(cc.train(UnitTypeId.SCV))
                    print("Train SCV")

        total_depots = self.structures(UnitTypeId.SUPPLYDEPOT).amount + self.already_pending(UnitTypeId.SUPPLYDEPOT)
        if self.structures(UnitTypeId.SUPPLYDEPOT).amount + self.already_pending(UnitTypeId.SUPPLYDEPOT) < 4:
            if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                worker = self.workers.random_or(None)
                if worker:
                    base = self.townhalls.first.position
                    offset_x = 4 + (total_depots * 2)
                    build_pos = Point2((base.x + offset_x, base.y))
                    self.do(worker.build(UnitTypeId.SUPPLYDEPOT, build_pos))
                    print(f"Building Supply Depot #{total_depots + 1} at {build_pos.rounded}")
                    #return to mine after 
                    mineral_field = self.mineral_field.closest_to(worker)
                    self.do(worker.gather(mineral_field))

run_game(
    maps.get("Flat64"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)