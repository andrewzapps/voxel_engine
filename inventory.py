from dataclasses import dataclass

MAX_STACK = 64
HOTBAR_SIZE = 9
MAIN_SIZE = 27
TOTAL_SLOTS = HOTBAR_SIZE + MAIN_SIZE


@dataclass(frozen=True)
class ItemStack:
    block_id: int
    count: int


class Inventory:
    def __init__(self):
        #slots 0-8 are the hotbar, 9-35 are the main grid - same layout
        #real minecraft uses, so the hotbar is just the top row of this
        self.slots = [None] * TOTAL_SLOTS

    def add_item(self, block_id, count=1):
        #world.get_voxel hands back numpy uint8s, and those don't survive a
        #trip through json - keep stacks as plain python ints from the start
        block_id = int(block_id)

        #top up any existing pile of the same block first
        for i, stack in enumerate(self.slots):
            if stack is not None and stack.block_id == block_id and stack.count < MAX_STACK:
                added = min(count, MAX_STACK - stack.count)
                self.slots[i] = ItemStack(block_id, stack.count + added)
                count -= added
                if count == 0:
                    return

        #then spill whatever's left into empty slots
        for i, stack in enumerate(self.slots):
            if stack is None:
                added = min(count, MAX_STACK)
                self.slots[i] = ItemStack(block_id, added)
                count -= added
                if count == 0:
                    return

        #inventory's full - the rest just doesn't fit, same as it would on the ground

    def take_one(self, index):
        stack = self.slots[index]
        if stack is None:
            return None

        self.slots[index] = ItemStack(stack.block_id, stack.count - 1) if stack.count > 1 else None
        return stack.block_id

    def to_serializable(self):
        return [[stack.block_id, stack.count] if stack is not None else None for stack in self.slots]

    def load_serializable(self, data):
        self.slots = [ItemStack(entry[0], entry[1]) if entry is not None else None for entry in data]
