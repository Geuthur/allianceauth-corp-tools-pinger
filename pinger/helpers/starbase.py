import ast
import math
from django.utils import timezone
from corptools.models import Starbase, EveItemType

from allianceauth.services.hooks import get_extension_logger

logger = get_extension_logger(__name__)

def has_fuel_block(starbase: Starbase) -> bool:
    """Check if the starbase has any fuel blocks in its fuels list."""
    if not starbase.fuels:
        return False
    try:
        type_ids = []
        # Get TypeIDs from fuels
        for item in ast.literal_eval(starbase.fuels):
            type_ids.append(int(item['type_id']))
        
        # Check if any of the fuel TypeIDs are in the list of known fuel blocks (group_id=1136)
        return EveItemType.objects.filter(
            type_id__in=type_ids,
            group_id=1136
        ).exists()
    except Exception as e:
        logger.warning(f"Error parsing fuels for this starbase: {e}")
        return False

def starbase_fuel_duration(starbase: Starbase) -> timezone.timedelta | None:
    """
    Calculate the estimated fuel duration as a timedelta.
    Returns a None if there are no fuel blocks.
    """
    if has_fuel_block(starbase) is False:
        return None

    # Get the total quantity of fuel blocks
    fuel_quantity = get_fuel_blocks_quantity(starbase)
    if fuel_quantity == 0:
        return None
    
    # Calculate the fuel duration in seconds
    seconds = _fuel_duration_seconds(starbase, fuel_quantity)

    return timezone.timedelta(seconds=seconds)

def get_fuel_blocks_quantity(starbase: Starbase) -> int:
    """
    Calculate the total quantity of fuel blocks in the starbase's fuels list.
    """
    if not starbase.fuels:
        return 0
    try:
        # Get TypeIDs and quantities from fuels
        fuel_data = {int(item['type_id']): int(item['quantity']) for item in ast.literal_eval(starbase.fuels)}
        # Get TypeIDs of known fuel blocks (group_id=1136)
        fuel_block_type_ids = EveItemType.objects.filter(
            group_id=1136
        ).values_list('type_id', flat=True)
        # Sum the quantities of fuel blocks
        total_fuel_blocks = sum(
            quantity for type_id, quantity in fuel_data.items() if type_id in fuel_block_type_ids
        )
        return total_fuel_blocks
    except Exception as e:
        logger.debug(f"Error calculating fuel blocks quantity: {e}")
        return 0

def _fuel_duration_seconds(starbase: Starbase, fuel_quantity: int, sov_discount: float = 0) -> int:
    """
    Calculate how long the fuel lasts in seconds based on the starbase type and fuel quantity.
    Args:
        fuel_quantity (int): The quantity of fuel blocks.
        sov_discount (float): The sovereignty discount to apply (default is 0).
    """
    if "small" in starbase.type_name.name.lower():
        fuel_per_hour = 10
    elif "medium" in starbase.type_name.name.lower():
        fuel_per_hour = 20
    elif "large" in starbase.type_name.name.lower():
        fuel_per_hour = 40
    else:
        raise ValueError("Unknown starbase type for fuel duration calculation.")

    seconds = math.floor(3600 * fuel_quantity / (fuel_per_hour * (1 - sov_discount)))
    return seconds
