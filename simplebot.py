from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2


class MyBot(BotAI):
    async def build_workers(self):
        if self.townhalls:
            cc = self.townhalls.first
            if self.can_afford(UnitTypeId.SCV) and cc.is_idle:
                    self.do(cc.train(UnitTypeId.SCV))
                    print("Train SCV")

    async def build_supply_depots(self):
        if self.supply_left < 5 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            ccs = self.townhalls.ready
            if ccs.exists and self.can_afford(UnitTypeId.SUPPLYDEPOT):
                location = ccs.first.position.towards(self.game_info.map_center, 5)
                await self.build(UnitTypeId.SUPPLYDEPOT, near=location)

    async def build_barracks(self):
        total_barracks = self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS)

        if self.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1 and total_barracks < 3:
            if self.can_afford(UnitTypeId.BARRACKS) and self.townhalls.ready.exists:
                worker = self.workers.random_or(None)
                cc = self.townhalls.ready.first
                if worker and cc:
                    build_pos = cc.position.towards(self.game_info.map_center, 10)
                    await self.build(UnitTypeId.BARRACKS, near=build_pos)
                    print(f"Building Barracks near {build_pos.rounded}")

    async def build_marines(self):
        for barracks in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE):
                self.do(barracks.train(UnitTypeId.MARINE))
                print("Training Marine")

    async def on_step(self, iteration):
        #print(f"Step {iteration}")
        await self.distribute_workers()
        await self.build_workers()
        await self.build_supply_depots()
        await self.build_barracks()
        await self.build_marines()

           

run_game(
    maps.get("Flat64"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)