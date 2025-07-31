from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.unit_typeid import UnitTypeId
async def research_upgrades_stimpack(bot):
    for barracks in bot.structures(UnitTypeId.BARRACKS).ready:
        if not barracks.has_add_on:
            continue

        # Get the Tech Lab unit attached to this Barracks
        tech_labs = bot.structures(UnitTypeId.BARRACKSTECHLAB).ready
        tech_lab = tech_labs.closest_to(barracks) if tech_labs.exists else None

        if tech_lab and tech_lab.is_idle:
            # Check if we can afford Stimpack and it's not already researched or pending
            if (
                bot.can_afford(UpgradeId.STIMPACK)
                and bot.already_pending_upgrade(UpgradeId.STIMPACK) == 0
            ):
                tech_lab.research(UpgradeId.STIMPACK)
                break  # Only issue one research per frame