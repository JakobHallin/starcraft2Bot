from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId


class MyBot(BotAI):
    async def on_step(self, iteration):
        #print(f"Step {iteration}")
        if self.townhalls:
            cc = self.townhalls.first
            if self.can_afford(UnitTypeId.SCV) and cc.is_idle:
                    self.do(cc.train(UnitTypeId.SCV))
                    print("Train SCV")

run_game(
    maps.get("Flat32"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)