from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId


class MyBot(BotAI):
    def __init__(self):
        self.scout_unit = None
        self.scout_locations = []
        self.current_scout_index = 0
        self.enemy_base_location = None
        self.scouting_started = False
        self.last_move_time = 0

    async def build_workers(self):
        if self.townhalls:
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
    
    async def calldpown_mule(self):
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
            if self.can_afford(UnitTypeId.COMMANDCENTER):  # can we afford one?
                await self.expand_now()

    async def on_step(self, iteration):

        await self.distribute_workers()
        await self.build_orbiltal_command()
        await self.build_workers()
        await self.build_supply_depots()
        await self.build_barracks()
        await self.build_marines()
        await self.attack_enemy()
        await self.calldpown_mule()
        self.scout_enemy_base()
        await self.expand()

           

run_game(
    maps.get("Flat64"),  # You can replace with any valid map
    [Bot(Race.Terran, MyBot()), Computer(Race.Zerg, Difficulty.Easy)],
    realtime=False,
)