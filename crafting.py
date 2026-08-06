from dataclasses import dataclass

from blocks import COAL_ORE, CRAFTING_TABLE, LOG, PLANKS, TORCH
from inventory import ItemStack


@dataclass(frozen=True)
class Recipe:
    ingredients: dict  # block_id -> required count, shapeless - order in the grid doesn't matter
    output_id: int
    output_count: int


#everything here fits in the 2x2 personal grid, same as real minecraft doesn't
#need a table for planks/sticks/the table itself. tools are left out on
#purpose - there's no mining-speed or durability system for them to plug
#into yet, so a "wooden pickaxe" item would just be a decoration
RECIPES = (
    Recipe(ingredients={LOG: 1}, output_id=PLANKS, output_count=4),
    Recipe(ingredients={PLANKS: 4}, output_id=CRAFTING_TABLE, output_count=1),
    Recipe(ingredients={COAL_ORE: 1, PLANKS: 1}, output_id=TORCH, output_count=4),
)


def match_recipe(grid_stacks):
    counts = {}
    for stack in grid_stacks:
        if stack is not None:
            counts[stack.block_id] = counts.get(stack.block_id, 0) + stack.count

    for recipe in RECIPES:
        if counts == recipe.ingredients:
            return recipe
    return None


def consume_recipe(grid_stacks, recipe):
    remaining = dict(recipe.ingredients)
    new_grid = list(grid_stacks)

    for i, stack in enumerate(new_grid):
        if stack is None:
            continue
        needed = remaining.get(stack.block_id, 0)
        if needed <= 0:
            continue

        taken = min(needed, stack.count)
        remaining[stack.block_id] -= taken
        left = stack.count - taken
        new_grid[i] = ItemStack(stack.block_id, left) if left > 0 else None

    return new_grid
