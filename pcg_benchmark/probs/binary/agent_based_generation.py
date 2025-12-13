import json
import os
from random import choice

from pcg_benchmark.probs.binary import BinaryProblem


class Agent:

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # 'N', 'S', 'E', 'W'

    def move(self, grid_max_x, grid_max_y):
        directions = {
            'N': (0, -1),
            'S': (0, 1),
            'E': (1, 0),
            'W': (-1, 0)
        }
        dx, dy = directions[self.direction]
        self.x = max(1, min(self.x + dx, grid_max_x - 1))
        self.y = max(1, min(self.y + dy, grid_max_y - 1))

    def turn(self):
        turns = {
            'N': ['E', 'W'],
            'S': ['E', 'W'],
            'E': ['N', 'S'],
            'W': ['N', 'S']
        }
        self.direction = choice(turns[self.direction])

class AgentBasedGeneration:
    _problem = BinaryProblem(width=60, height=60, path=120)
    p_turn_init=5  # probability to turn
    p_room_init=5  # probability to create a new room

    def __init__(
            self,
            p_turn_increase=5,
            p_room_increase=5
    ):
        self.content = [[0 for _ in range(self._problem._width)] for _ in range(self._problem._height)]
        self.agent = Agent(0, 0, 'N')
        self.p_turn = self.p_turn_init
        self.p_room = self.p_room_init
        self.p_turn_increase = p_turn_increase
        self.p_room_increase = p_room_increase

    def create_room(self):
        room_size = self._problem._random.integers(3, 8)
        for dx in range(-room_size//2, room_size//2 + 1):
            for dy in range(-room_size//2, room_size//2 + 1):
                x = self.agent.x + dx
                y = self.agent.y + dy
                if 0 <= x < self._problem._width - 1 and 0 <= y < self._problem._height - 1:
                    self.content[y][x] = 2

    def update(self):
        # move and dig
        self.agent.move(self._problem._width, self._problem._height)
        self.content[self.agent.y][self.agent.x] = 1

        nt = self._problem._random.integers(0, 100)
        if nt < self.p_turn:
            self.agent.turn()
            self.p_turn = 0
        else:
            self.p_turn += self.p_turn_increase

        nr = self._problem._random.integers(0, 100)
        if nr < self.p_room:
            self.create_room()
            self.p_room = 0
        else:
            self.p_room += self.p_room_increase

    def generate(self, steps=100):
        # Initialize agent in the center
        self.agent.x = self._problem._width // 2
        self.agent.y = self._problem._height // 2
        self.agent.direction = self._problem._random.choice(['N', 'S', 'E', 'W'])

        self.create_room()
        for _ in range(steps):
            self.update()
        self.create_room()

        content = self.content
        info = self._problem.info(content)
        result = {
            "p_turn_increase": self.p_turn_increase,
            "p_room_increase": self.p_room_increase,
            "steps": steps,
            "quality": self._problem.quality(info),
            "content": content
        }
        return result

def save(result, id):
    """Saves the generated level to a file."""
    folderpath = f"../../../task5_results/agent_based_generation"
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)
    filename = f"abg_{id}.json"
    full_filepath = os.path.join(folderpath, filename)
    with open(full_filepath, 'w') as f:
        json.dump(result, f, indent=4)

if __name__ == "__main__":
    turn_ps = [0.25, 0.5, 0.75, 1, 2, 5, 10]
    room_ps = [0.25, 0.5, 0.75, 1, 2, 5, 10]
    for p_room_increase in room_ps:
        for p_turn_increase in turn_ps:
            for i in range(25):
                generator = AgentBasedGeneration(p_turn_increase=p_turn_increase, p_room_increase=p_room_increase)
                level = generator.generate(steps=500)
                # -- save results to create plots later
                # save(level, f"turn{p_turn_increase}_room{p_room_increase}_{i}")
                # -- render for every depth to see the difference
                if i == 0:
                    image = generator._problem.render(generator.content)
                    folderpath = "../../../task5_results/images/agent_based_generation"
                    if not os.path.exists(folderpath):
                        os.makedirs(folderpath)
                    image.save(os.path.join(folderpath, f"abg_turn_{p_turn_increase}_room_{p_room_increase}.png"))