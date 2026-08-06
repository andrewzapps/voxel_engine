from blocks import COAL_ORE, CRAFTING_TABLE, LOG, PLANKS, STONE, TORCH
from crafting import consume_recipe, match_recipe
from inventory import ItemStack


def test_match_recipe_finds_planks_from_a_single_log():
    grid = [ItemStack(LOG, 1), None, None, None]
    recipe = match_recipe(grid)

    assert recipe is not None
    assert recipe.output_id == PLANKS
    assert recipe.output_count == 4


def test_match_recipe_finds_crafting_table_from_four_planks():
    grid = [ItemStack(PLANKS, 1)] * 4
    recipe = match_recipe(grid)

    assert recipe is not None
    assert recipe.output_id == CRAFTING_TABLE


def test_match_recipe_finds_torch_from_coal_and_plank():
    grid = [ItemStack(COAL_ORE, 1), ItemStack(PLANKS, 1), None, None]
    recipe = match_recipe(grid)

    assert recipe is not None
    assert recipe.output_id == TORCH
    assert recipe.output_count == 4


def test_match_recipe_returns_none_for_unrelated_ingredients():
    grid = [ItemStack(STONE, 3), None, None, None]
    assert match_recipe(grid) is None


def test_match_recipe_returns_none_when_short_an_ingredient():
    #torch needs both coal and planks, not just coal
    grid = [ItemStack(COAL_ORE, 1), None, None, None]
    assert match_recipe(grid) is None


def test_consume_recipe_removes_exactly_what_the_recipe_needs():
    grid = [ItemStack(LOG, 1), None, None, None]
    recipe = match_recipe(grid)

    result = consume_recipe(grid, recipe)

    assert result == [None, None, None, None]


def test_consume_recipe_leaves_partial_stacks_behind():
    grid = [ItemStack(PLANKS, 5), None, None, None]
    #pretend a recipe needing 4 planks matched against a stack of 5
    from crafting import Recipe
    recipe = Recipe(ingredients={PLANKS: 4}, output_id=CRAFTING_TABLE, output_count=1)

    result = consume_recipe(grid, recipe)

    assert result[0] == ItemStack(PLANKS, 1)
