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

    async def build_workers(self):
        #if self.townhalls:
        cc = self.townhalls.first
        ideal_workers = sum(townhall.ideal_harvesters for townhall in self.townhalls)+1

        if self.can_afford(UnitTypeId.SCV) and cc.is_idle and self.workers.amount < ideal_workers:
            self.do(cc.train(UnitTypeId.SCV))   
            print(f"Train SCV: {self.workers.amount} / {ideal_workers}")


    async def build_supply_depots(self):
        if self.supply_left < 5 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
            ccs = self.townhalls.ready
            if ccs.exists and self.can_afford(UnitTypeId.SUPPLYDEPOT):
                location = ccs.first.position.towards(self.game_info.map_center, 5)
                await self.build(UnitTypeId.SUPPLYDEPOT, near=location)

    async def build_barracks(self):
        total_barracks = self.structures(UnitTypeId.BARRACKS).amount + self.already_pending(UnitTypeId.BARRACKS)
        num_cc = self.structures(UnitTypeId.COMMANDCENTER).amount
        num_orbitals = self.structures(UnitTypeId.ORBITALCOMMAND).amount
        self.max_barracks = 1 + num_cc * 2 + num_orbitals * 2 # Increase max barracks based on command centers
        if self.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1 and total_barracks <  self.max_barracks:
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
    async def build_marauders(self):
        for barracks in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if barracks.has_add_on:
                if self.can_afford(UnitTypeId.MARAUDER):
                    self.do(barracks.train(UnitTypeId.MARAUDER))
                    print("Training Marauder")

    async def attack_enemy(self):
        marines = self.units(UnitTypeId.MARINE)
        if marines.amount >= 12:
            target = self.enemy_base_location  
            for marine in marines.idle: 
                self.do(marine.attack(target))
            print(f"Attacking enemy base with {marines.amount} marines")

    async def build_orbiltal_command(self):
       for cc in self.townhalls.ready:
            if cc.type_id == UnitTypeId.COMMANDCENTER and self.can_afford(UnitTypeId.ORBITALCOMMAND):
                self.do(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

    
    async def calldown_mule(self):
        if self.structures(UnitTypeId.ORBITALCOMMAND).ready.exists:
            oc = self.structures(UnitTypeId.ORBITALCOMMAND).first
            target_mineral = self.mineral_field.closest_to(oc)
            if self.can_afford(AbilityId.CALLDOWNMULE_CALLDOWNMULE):
                self.do(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, target_mineral))
                print("Calling down MULE")

    
    def scout_enemy_base(self):
        if self.enemy_base_location:
            return  # Already found, no need to continue

        # First time setup
        if not self.scouting_started:
            if self.units(UnitTypeId.SCV).amount > 0 and self.enemy_start_locations:
                self.scout_unit = self.units(UnitTypeId.SCV).random
                self.scout_locations = list(self.enemy_start_locations)
                self.current_scout_index = 0
                self.scouting_started = True
                self.move_scout_to_next_location()
            return

        # Safety check
        if not self.scout_unit or self.scout_unit.tag not in self.units.tags:
            return


        # Check for enemy buildings
        if self.enemy_structures:
            self.enemy_base_location = self.enemy_structures.closest_to(self.scout_unit).position
            print(f"Enemy base found at {self.enemy_base_location}")
            return

        # Move to next location
        if self.time - self.last_move_time > 20:
            self.current_scout_index += 1
            if self.current_scout_index < len(self.scout_locations):
                self.move_scout_to_next_location()
            else:
                print("Scouting complete. No enemy base found.")
                self.scout_unit = None  # stop scouting

    def move_scout_to_next_location(self):
        target = self.scout_locations[self.current_scout_index]
        self.scout_unit.move(target)
        self.last_move_time = self.time
        print(f"Moving scout to location {self.current_scout_index + 1}: {target}")

    async def expand(self):
        if self.can_afford(UnitTypeId.COMMANDCENTER) and self.townhalls.ready.exists:
            await self.expand_now()
            #self.max_barracks += 1
    async def build_refinery(self):
        if self.structures(UnitTypeId.SUPPLYDEPOT).ready.amount >= 1:
            if self.can_afford(UnitTypeId.REFINERY) and self.gas_buildings.amount < 2:
                vgs = self.vespene_geyser.closest_to(self.townhalls.first)
                if vgs:
                    worker = self.workers.closest_to(vgs)
                    if worker:
                        self.do(worker.build(UnitTypeId.REFINERY, vgs))
                        print("Building Refinery")

    async def build_techlab(self):

        for barracks in self.structures(UnitTypeId.BARRACKS).ready.idle:
            # Check if we can build a Tech Lab and if the barracks has no addon
            if not barracks.has_add_on and self.can_afford(UnitTypeId.TECHLAB):
                # Build the Tech Lab
                self.do(barracks(AbilityId.BUILD_TECHLAB_BARRACKS))
                self.techlab_built = True
                print(f"Building Tech Lab on {barracks.tag}")
                
    async def research_upgrades_stimpack(self):
        for barracks in self.structures(UnitTypeId.BARRACKS).ready:
            if not barracks.has_add_on:
                continue

            # Get the Tech Lab unit attached to this Barracks
            tech_labs = self.structures(UnitTypeId.BARRACKSTECHLAB).ready
            tech_lab = tech_labs.closest_to(barracks) if tech_labs.exists else None

            if tech_lab and tech_lab.is_idle:
                # Check if we can afford Stimpack and it's not already researched or pending
                if (
                    self.can_afford(UpgradeId.STIMPACK)
                    and self.already_pending_upgrade(UpgradeId.STIMPACK) == 0
                ):
                    tech_lab.research(UpgradeId.STIMPACK)
                    break  # Only issue one research per frame

    async def on_step(self, iteration):

        await self.distribute_workers()
        await self.build_orbiltal_command()
        await self.build_workers()
        await self.build_supply_depots()
        await self.build_barracks()
        await self.build_techlab()
        #await self.build_marines()
        await self.attack_enemy()
        await self.calldown_mule()
        self.scout_enemy_base()
        await self.expand()
        await self.build_refinery()
        await self.research_upgrades_stimpack()
        #await self.build_marauders()
        
        

           

run_game(
    maps.get("Flat96"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)