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
        
        #mineral patch and worker assignment
        self.worker_to_mineral_patch_dict: dict[int, int] = {}
        self.mineral_patch_to_list_of_workers: dict[int, set[int]] = {}
        self.minerals_sorted_by_distance: Units = Units([], self)
        # Distance 0.01 to 0.1 seems fine
        self.townhall_distance_threshold = 0.01
        # Distance factor between 0.95 and 1.0 seems fine
        self.townhall_distance_factor = 1
        self.workers_reserved_for_tasks: set[int] = set()

    async def on_start(self):
        self.client.game_step = 1
        await self.assign_workers()

    async def assign_workers(self):
        self.minerals_sorted_by_distance = self.mineral_field.closer_than(
            10, self.start_location
        ).sorted_by_distance_to(self.start_location)

        # Assign workers to mineral patch, start with the mineral patch closest to base
        for mineral in self.minerals_sorted_by_distance:
            # Assign workers closest to the mineral patch
            workers = self.workers.tags_not_in(self.worker_to_mineral_patch_dict).sorted_by_distance_to(mineral)
            for worker in workers:
                # Assign at most 2 workers per patch
                # This dict is not really used further down the code, but useful to keep track of how many workers are assigned to this mineral patch - important for when the mineral patch mines out or a worker dies
                if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) < 2:
                    if len(self.mineral_patch_to_list_of_workers.get(mineral.tag, [])) == 0:
                        self.mineral_patch_to_list_of_workers[mineral.tag] = {worker.tag}
                    else:
                        self.mineral_patch_to_list_of_workers[mineral.tag].add(worker.tag)
                    # Keep track of which mineral patch the worker is assigned to - if the mineral patch mines out, reassign the worker to another patch
                    self.worker_to_mineral_patch_dict[worker.tag] = mineral.tag
                else:
                    break


    def _unassign_worker(self, worker: Unit) -> None:
        """Remove `worker` from both bookkeeping dicts (if present)."""
        mineral_tag = self.worker_to_mineral_patch_dict.pop(worker.tag, None)
        if mineral_tag is not None:
            worker_set = self.mineral_patch_to_list_of_workers.get(mineral_tag, set())
            worker_set.discard(worker.tag)
            if not worker_set:          # patch now empty → drop the key
                self.mineral_patch_to_list_of_workers.pop(mineral_tag, None)


    async def build_workers(bot):
        #if bot.townhalls:
        cc = bot.townhalls.first
        ideal_workers = 22#sum(townhall.ideal_harvesters for townhall in bot.townhalls)+1

        if bot.can_afford(UnitTypeId.SCV) and cc.is_idle and bot.workers.amount < ideal_workers:
            bot.do(cc.train(UnitTypeId.SCV))   
            print(f"Train SCV: {bot.workers.amount} / {ideal_workers}")
            

    async def calldown_mule(self):
        if self.structures(UnitTypeId.ORBITALCOMMAND).ready.exists:
            oc = self.structures(UnitTypeId.ORBITALCOMMAND).first
            target_mineral = self.mineral_field.closest_to(oc)
            if self.can_afford(AbilityId.CALLDOWNMULE_CALLDOWNMULE):
                self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target_mineral))
                print("Calling down MULE")
    async def fill_refineries(bot):
        for refinery in bot.gas_buildings.ready:
            assigned = refinery.assigned_harvesters
            ideal = refinery.ideal_harvesters
            if assigned < ideal:
                for _ in range(ideal - assigned):
                    worker = bot.workers.gathering.random_or(None)
                    if worker:
                        bot.do(worker.gather(refinery))

    
                
   
   

    async def on_step(self, iteration):

        all_assigned = set(self.worker_to_mineral_patch_dict)
        unassigned = self.workers.tags_not_in(all_assigned.union(self.workers_reserved_for_tasks))
        if unassigned:
            await self.assign_workers()
        
        if self.worker_to_mineral_patch_dict:
            # Quick-access cache mineral tag to mineral Unit
            minerals: dict[int, Unit] = {mineral.tag: mineral for mineral in self.mineral_field}

            worker: Unit
            for worker in self.workers:
                if not self.townhalls:
                    logger.error("All townhalls died - can't return resources")
                    break
                if worker.tag not in self.worker_to_mineral_patch_dict:
                    continue

                mineral_tag = self.worker_to_mineral_patch_dict.get(worker.tag)
                mineral = minerals.get(mineral_tag)
                if mineral is None:
                    logger.error(f"Mined out mineral with tag {mineral_tag} for worker {worker.tag}")
                    continue

                # Order worker to mine at target mineral patch if isn't carrying minerals
                if not worker.is_carrying_minerals:
                    if not worker.is_gathering or worker.order_target != mineral.tag:
                        worker.gather(mineral)
                # Order worker to return minerals if carrying minerals
                else:
                    th = self.townhalls.closest_to(worker)
                    # Move worker in front of the nexus to avoid deceleration until the last moment
                    if worker.distance_to(th) > th.radius + worker.radius + self.townhall_distance_threshold:
                        pos: Point2 = th.position
                        # pyre-ignore[6]
                        worker.move(pos.towards(worker, th.radius * self.townhall_distance_factor))
                        worker.return_resource(queue=True)
                    else:
                        worker.return_resource()
                        worker.gather(mineral, queue=True)

        #await self.distribute_workers()

        #await build_orbiltal_command(self)
        await self.build_workers()
        await build_supply_depots(self)
        
        
        #await build_barracks(self)
        #await build_techlab(self)
        #await build_marines(self)
        #await attack_enemy(self)
        #await self.calldown_mule()
        #scout_enemy_base(self)
        #await expand(self)
        #await build_refinery(self)
        #await research_upgrades_stimpack(self)
        #await self.fill_refineries()
        #await self.build_marauders()
        
        
        

           

run_game(
    maps.get("Flat96"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)