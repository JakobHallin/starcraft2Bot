
from __future__ import annotations

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId

class WorkerStackBot(BotAI):
    def __init__(self):
        self.worker_to_mineral_patch_dict: dict[int, int] = {}
        self.mineral_patch_to_list_of_workers: dict[int, set[int]] = {}
        self.minerals_sorted_by_distance: Units = Units([], self)
        # Distance 0.01 to 0.1 seems fine
        self.townhall_distance_threshold = 0.01
        # Distance factor between 0.95 and 1.0 seems fine
        self.townhall_distance_factor = 1

    async def build_workers(bot):
        #if bot.townhalls:
        cc = bot.townhalls.first
        ideal_workers = 22#sum(townhall.ideal_harvesters for townhall in bot.townhalls)+1

        if bot.can_afford(UnitTypeId.PROBE) and cc.is_idle and bot.workers.amount < ideal_workers:
            bot.do(cc.train(UnitTypeId.PROBE))   
            print(f"Train SCV: {bot.workers.amount} / {ideal_workers}")
            

    async def on_step(self, iteration: int):
       
        await self.build_workers()
        #await self.assign_workers()
        # Print info every 30 game-seconds
        # pyre-ignore[16]
        if int(self.time) in {10, 30, 50, 80, 100, 120}:
            print(f"[{int(self.time)}s] Minerals: {self.minerals} | Workers: {self.workers.amount}")
        if self.state.game_loop % (22.4 * 30) == 0:
            logger.info(f"{self.time_formatted} Mined a total of {int(self.state.score.collected_minerals)} minerals")


def main():
    run_game(
        maps.get("Flat96"),  # You can replace with any valid map
        [Bot(Race.Protoss, WorkerStackBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        random_seed=0,
    )


if __name__ == "__main__":
    main()