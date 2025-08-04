from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from loguru import logger
from tasks.infrastucture import build_supply_depots, build_barracks, build_orbiltal_command, expand, build_techlab, build_refinery
from tasks.actions import scout_enemy_base, attack_enemy
from tasks.research import research_upgrades_stimpack
from tasks.units import build_marines, build_marauders
from tasks.WorkerTaskManager import WorkerTaskManager
class MyBot(BotAI):
    def __init__(self):
        self.scout_unit = None
        self.scout_locations = []
        self.current_scout_index = 0
        self.enemy_base_location = None
        self.scouting_started = False
        self.last_move_time = 0
        
        self.max_barracks = 0 #starting with max 3 baracks but later can be increased
        self.techlab_built = False
        self.worker_manager = WorkerTaskManager(self)
        

    async def calldown_mule(self):
        if self.structures(UnitTypeId.ORBITALCOMMAND).ready.exists:
            oc = self.structures(UnitTypeId.ORBITALCOMMAND).first
            target_mineral = self.mineral_field.closest_to(oc)
            if oc.energy >= 50 and self.can_afford(AbilityId.CALLDOWNMULE_CALLDOWNMULE):
                self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target_mineral))
                print("Calling down MULE")

    async def on_start(self):
        self.client.game_step = 1
        await self.worker_manager.assign_workers()

    







    
                
   
    async def build_workers(bot):
        #if bot.townhalls:
        cc = bot.townhalls.first
        ideal_workers = sum(townhall.ideal_harvesters for townhall in bot.townhalls)+6

        if bot.can_afford(UnitTypeId.SCV) and cc.is_idle and bot.workers.amount < ideal_workers:
            bot.do(cc.train(UnitTypeId.SCV))   
            print(f"Train SCV: {bot.workers.amount} / {ideal_workers}")
            

    async def on_step(self, iteration):



        #await self.distribute_workers()
        await self.worker_manager.handle_idle_builders()
        
        #scout_enemy_base(self.worker_manager)

       # await build_orbiltal_command(self)
        await self.build_workers()
        await build_supply_depots(self)
        
        
       # await build_barracks(self)
      #  await build_techlab(self)
      #  await build_marines(self)
        #await attack_enemy(self)
       # await self.calldown_mule()
        
       # await expand(self)
       # await build_refinery(self)
       # await self.fill_refineries()
       # await research_upgrades_stimpack(self)
       # await build_marauders(self)
        
        
        

           

run_game(
    maps.get("Flat96"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)