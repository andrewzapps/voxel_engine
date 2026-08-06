from inventory import MAX_STACK, Inventory, ItemStack


def test_add_item_fills_first_empty_slot():
    inv = Inventory()
    inv.add_item(block_id=3, count=5)

    assert inv.slots[0] == ItemStack(3, 5)
    assert all(slot is None for slot in inv.slots[1:])


def test_add_item_stacks_onto_existing_pile_before_using_a_new_slot():
    inv = Inventory()
    inv.add_item(3, count=5)
    inv.add_item(3, count=2)

    assert inv.slots[0] == ItemStack(3, 7)
    assert inv.slots[1] is None


def test_add_item_overflows_into_a_new_stack_past_max_stack_size():
    inv = Inventory()
    inv.add_item(3, count=MAX_STACK)
    inv.add_item(3, count=10)

    assert inv.slots[0] == ItemStack(3, MAX_STACK)
    assert inv.slots[1] == ItemStack(3, 10)


def test_take_one_decrements_and_clears_when_empty():
    inv = Inventory()
    inv.slots[0] = ItemStack(3, 2)

    first = inv.take_one(0)
    assert first == 3
    assert inv.slots[0] == ItemStack(3, 1)

    second = inv.take_one(0)
    assert second == 3
    assert inv.slots[0] is None


def test_take_one_from_empty_slot_returns_none():
    inv = Inventory()
    assert inv.take_one(0) is None


def test_serialization_round_trips():
    inv = Inventory()
    inv.slots[0] = ItemStack(3, 7)
    inv.slots[5] = ItemStack(1, 64)

    data = inv.to_serializable()

    restored = Inventory()
    restored.load_serializable(data)

    assert restored.slots[0] == ItemStack(3, 7)
    assert restored.slots[5] == ItemStack(1, 64)
    assert restored.slots[1] is None
