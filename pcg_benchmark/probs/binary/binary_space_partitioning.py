import json
import os

from pcg_benchmark.probs.binary import BinaryProblem


class Node:
    """Helper class to store tree structure."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left = None
        self.right = None
        self.room = None  # Stores (x, y, w, h) of the final room


class BinarySpacePartitioning:
    _problem = BinaryProblem(width=60, height=60, path=120)

    def __init__(self, depth):
        self.depth = depth
        # Initialize grid with 0 (walls)
        self.content = [[0 for _ in range(self._problem._width)] for _ in range(self._problem._height)]
        self.root = None
        self.leaves = []

    def partition(self, x_start, y_start, x_end, y_end, depth):
        """Recursively splits space and creates the tree."""
        node = Node(x_start, y_start, x_end - x_start, y_end - y_start)

        if depth == 0:
            self.leaves.append(node)
            return node

        horizontal = self._problem._random.choice([True, False])

        if horizontal and (y_end - y_start) > 4:
            y_split = self._problem._random.integers(y_start + 2, y_end - 2)
            node.left = self.partition(x_start, y_start, x_end, y_split, depth - 1)
            node.right = self.partition(x_start, y_split + 1, x_end, y_end, depth - 1)
        elif not horizontal and (x_end - x_start) > 4:
            x_split = self._problem._random.integers(x_start + 2, x_end - 2)
            node.left = self.partition(x_start, y_start, x_split, y_end, depth - 1)
            node.right = self.partition(x_split + 1, y_start, x_end, y_end, depth - 1)
        else:
            self.leaves.append(node)
            return node

        return node

    def place_room(self, node):
        """Places a room ensuring it takes >= 75% of the partition space."""
        max_w = node.w
        max_h = node.h

        room_w = self._problem._random.integers(max(2, max_w // 4 * 3), max_w + 1)
        room_h = self._problem._random.integers(max(2, max_h // 4 * 3), max_h + 1)

        # 2. Enforce 75% Area Constraint
        partition_area = max_w * max_h
        target_area = partition_area * 0.75

        while (room_w * room_h) < target_area:
            if room_w >= max_w and room_h >= max_h:
                break

            expand_width = self._problem._random.choice([True, False])

            if expand_width:
                if room_w < max_w:
                    room_w += 1
                elif room_h < max_h:
                    room_h += 1
            else:
                if room_h < max_h:
                    room_h += 1
                elif room_w < max_w:  # Fallback to width if height is maxed
                    room_w += 1

        free_x = max_w - room_w
        free_y = max_h - room_h

        x_room = node.x + (free_x // 2)
        y_room = node.y + (free_y // 2)

        node.room = (x_room, y_room, room_w, room_h)

        for y in range(y_room, y_room + room_h):
            for x in range(x_room, x_room + room_w):
                if 0 <= y < self._problem._height and 0 <= x < self._problem._width:
                    self.content[y][x] = 2

    def create_hallway(self, x1, y1, x2, y2):
        """Draws a corridor."""
        if self._problem._random.choice([True, False]):
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.content[y1][x] = max(1, self.content[y1][x])
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.content[y][x2] = max(1, self.content[y][x2])
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.content[y][x1] = max(1, self.content[y][x1])
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.content[y2][x] = max(1, self.content[y2][x])

    def connect_rooms(self, node):
        """
        Recursively connects children nodes.
        Returns the center (x, y) of the connected cluster to the parent.
        """
        if node.left is None and node.right is None:
            rx, ry, rw, rh = node.room
            return rx + rw // 2, ry + rh // 2
        point_left = self.connect_rooms(node.left)
        point_right = self.connect_rooms(node.right)
        self.create_hallway(point_left[0], point_left[1], point_right[0], point_right[1])
        return self._problem._random.choice([point_left, point_right])

    def full_generation(self):
        # 1. Build Partition Tree
        self.root = self.partition(0, 0, self._problem._width, self._problem._height, self.depth)

        # 2. Place Rooms
        for leaf_node in self.leaves:
            self.place_room(leaf_node)

        # 3. Connect Rooms (Tree Traversal)
        if self.root:
            self.connect_rooms(self.root)

        # 4. Return result
        content = bsp.content
        info = bsp._problem.info(content)
        result = {
            "content": content,
            "depth": self.depth,
            "quality": bsp._problem.quality(info)
        }
        return result

def save(result, iter_num):
        """Saves the generated level to a file."""
        folderpath = f"../../../task5_results/binary_space_partitioning/{result.get('depth')}"
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        filename = f"bsp_{iter_num%10}.json"
        full_filepath = os.path.join(folderpath, filename)
        with open(full_filepath, 'w') as f:
            json.dump(result, f, indent=4)

if __name__ == "__main__":
    for i in range(20, 120):
        bsp = BinarySpacePartitioning(depth=i//10)
        res = bsp.full_generation()
        save(res, i)
        # -- render for every depth to see the difference
        # if (i % 10) == 0:
        #     image = bsp._problem.render(bsp.content)
        #     image.show()