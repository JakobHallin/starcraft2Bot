from sc2.unit import Unit
from sc2.units import Units
#flags workers that are assigned to tasks
class WorkerTaskManager:
    def __init__(self, bot):
        self.bot = bot
        self.scout_workers: set[int] = set()
        self.builder_workers: set[int] = set()
        self.gas_workers_reserved: set[int] = set()

        #mineral patch and worker assignment
        self.worker_to_mineral_patch_dict: dict[int, int] = {}
        self.mineral_patch_to_list_of_workers: dict[int, set[int]] = {}
        self.minerals_sorted_by_distance: Units = Units([], self)
        # Distance 0.01 to 0.1 seems fine
        self.townhall_distance_threshold = 0.01
        # Distance factor between 0.95 and 1.0 seems fine
        self.townhall_distance_factor = 1
        self.workers_reserved_for_tasks: set[int] = set()


    #reserve workers for specific tasks
    def reserve_for_scout(self, worker: Unit):
        self._unassign_from_mining(worker)
        self.scout_workers.add(worker.tag)
    def reserve_for_builder(self, worker: Unit):
        self._unassign_from_mining(worker)
        self.builder_workers.add(worker.tag)
    def reserve_for_gas(self, worker: Unit):
        self._unassign_from_mining(worker)
        self.gas_workers_reserved.add(worker.tag)
    
    # Unassign worker from mining and reserve it for tasks
    def _unassign_from_mining(self, worker: Unit):
        self._unassign_worker(worker)
    
    
    def release_worker(self, worker: Unit):
        if worker.tag in self.scout_workers:
            self.scout_workers.remove(worker.tag)
        elif worker.tag in self.builder_workers:
            self.builder_workers.remove(worker.tag)
        elif worker.tag in self.gas_workers_reserved:
            self.gas_workers_reserved.remove(worker.tag)
        else:
            print(f"Warning: Worker {worker.tag} not found in any reserved set.")
        
        self.bot.workers_reserved_for_tasks.discard(worker.tag)
     
    #is unit reserved for a specific task
    def is_reserved(self, worker):
        return worker.tag in self.scout_workers or worker.tag in self.builder_workers or worker.tag in self.gas_workers_reserved
    
    def _unassign_worker(self, worker: Unit) -> None:
        """Remove `worker` from both bookkeeping dicts (if present)."""
        mineral_tag = self.worker_to_mineral_patch_dict.pop(worker.tag, None)
        if mineral_tag is not None:
            worker_set = self.mineral_patch_to_list_of_workers.get(mineral_tag, set())
            worker_set.discard(worker.tag)
            if not worker_set:          # patch now empty → drop the key
                self.mineral_patch_to_list_of_workers.pop(mineral_tag, None)

    async def assign_workers(self):
        self.minerals_sorted_by_distance = self.bot.mineral_field.closer_than(
            10, self.bot.start_location
        ).sorted_by_distance_to(self.bot.start_location)

        # Assign workers to mineral patch, start with the mineral patch closest to base
        for mineral in self.minerals_sorted_by_distance:
            # Assign workers closest to the mineral patch
            workers = self.bot.workers.tags_not_in(self.worker_to_mineral_patch_dict).sorted_by_distance_to(mineral)
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
    async def handle_mining_loop(self):
        minerals: dict[int, Unit] = {mineral.tag: mineral for mineral in self.bot.mineral_field}

        for worker in self.bot.workers:
            if self.is_reserved(worker):
                continue
            if worker.tag not in self.worker_to_mineral_patch_dict:
                continue

            mineral_tag = self.worker_to_mineral_patch_dict.get(worker.tag)
            mineral = minerals.get(mineral_tag)
            if mineral is None:
                continue

            if not worker.is_carrying_minerals:
                if not worker.is_gathering or worker.order_target != mineral.tag:
                    worker.gather(mineral)
            else:
                th = self.bot.townhalls.closest_to(worker)
                if worker.distance_to(th) > th.radius + worker.radius + self.bot.townhall_distance_threshold:
                    pos = th.position.towards(worker, th.radius * self.bot.townhall_distance_factor)
                    worker.move(pos)
                    worker.return_resource(queue=True)
                else:
                    worker.return_resource()
                    worker.gather(mineral, queue=True)
    
    
    async def handle_idle_builders(self):
        for worker in self.bot.workers.idle:
            if worker.tag in self.builder_workers:
                self.builder_workers.remove(worker.tag)
                self._unassign_worker(worker)
                
                mf = self.bot.mineral_field.closest_to(worker)
                #self.mineral_patch_to_list_of_workers[mineral.tag].add(worker.tag)
                #mineral_tag = self.worker_to_mineral_patch_dict.get(worker.tag)
                if mf:
                    self.bot.do(worker.gather(mf))
                    print(f"SCV {worker.tag} reassigned to mining after being idle.")
    
    async def fill_refineries(self):
        for refinery in self.bot.gas_buildings.ready:
            assigned = refinery.assigned_harvesters
            ideal = refinery.ideal_harvesters
            if assigned < ideal:
                for _ in range(ideal - assigned):
                    worker = self.bot.workers.gathering.random_or(None)
                    if worker:
                        self._unassign_worker(worker)
                        self.reserve_for_gas(worker)
                        self.bot.do(worker.gather(refinery))


