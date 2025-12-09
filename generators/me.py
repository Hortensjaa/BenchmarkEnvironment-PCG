import os
import json

import generators.search as search


def _bin(value, min_v, max_v, bins):
    value = max(min_v, min(value, max_v - 1e-9))
    return int((value - min_v) / (max_v - min_v) * bins)

def _save_space(space, iter_num=0, problem_name="unknown"):
    out_dir = "./task4_results/quality_control_diversity/" + problem_name
    path = os.path.join(out_dir, f"iter_{iter_num}.json")
    os.makedirs(out_dir, exist_ok=True)

    size = len(space)
    grid = []
    filled = 0

    for i in range(size):
        row = []
        for j in range(size):
            c = space[i][j]
            if c is None:
                row.append(None)
            else:
                filled += 1
                row.append({
                    # "content": c._content,
                    "control": c._control,
                    "info": c._info,
                    "quality": c._quality,
                    "diversity": c._diversity,
                    "controlability": c._controlability
                })
        grid.append(row)

    data = {
        "iter": iter_num,
        "space_size": size * size,
        "coverage": filled / (size * size),
        "grid": grid
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2, cls=search.NpEncoder)


class Generator(search.Generator):
    changes_in_iter = 100
    p_crossover = 0.25  # crossover instead of mutation chance
    children_num = 5
    space_size = 10
    
    def reset(self, **kwargs):
        super().reset(**kwargs)
        self._mut_rate = kwargs.get('mut_rate', 0.1)
        self._iter_num = 0

        # initialize space
        self._space = [[None for _ in range(self.space_size)] for _ in range(self.space_size)]
        self._bd_space = self._env._problem.descriptor_space()

        # initial population
        for _ in range(self.space_size * self.space_size):
            self._chromosomes.append(search.Chromosome(self._random))
            self._chromosomes[-1].random(self._env)

        # evaluate and put in correct bins
        search.evaluateChromosomes(self._env, self._chromosomes)
        for c in self._chromosomes:
            info = c._info
            x, y = self._env._problem.behavior_descriptor(info)

            ix = _bin(
                x,
                self._bd_space.X_behavior.min,
                self._bd_space.X_behavior.max,
                self.space_size
            )
            iy = _bin(
                y,
                self._bd_space.Y_behavior.min,
                self._bd_space.Y_behavior.max,
                self.space_size
            )

            # if better than current elite in this bin, replace
            elite = self._space[ix][iy]
            if elite is None or self._fitness_fn(c) > self._fitness_fn(elite):
                self._space[ix][iy] = c

        _save_space(self._space, self._iter_num, self._env._problem.name())

    def update(self):
        self._iter_num += 1
        elites = [c for row in self._space for c in row if c is not None]
        if len(elites) < 2:
            self.reset()
            return

        for _ in range(self.changes_in_iter):
            p1 = elites[self._random.integers(len(elites))]
            p2 = elites[self._random.integers(len(elites))]
            children = []

            # evolve
            for c in range(self.children_num):
                if self._random.random() < 0.5:
                    child = p1.crossover(p2)
                    child = child.mutation(self._env, self._mut_rate)
                else:
                    child = p1.mutation(self._env, self._mut_rate)
                children.append(child)

            # evaluate and put in correct bin
            search.evaluateChromosomes(self._env, children)
            for child in children:
                info = child._info
                x, y = self._env._problem.behavior_descriptor(info)
                ix = _bin(x, self._bd_space.X_behavior.min, self._bd_space.X_behavior.max, self.space_size)
                iy = _bin(y, self._bd_space.Y_behavior.min, self._bd_space.Y_behavior.max, self.space_size)
                current = self._space[ix][iy]
                if current is None or self._fitness_fn(child) > self._fitness_fn(current):
                    self._space[ix][iy] = child
            _save_space(self._space, self._iter_num, self._env._problem.name())

