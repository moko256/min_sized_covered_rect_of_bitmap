import numpy as np
from PIL import Image, ImageOps
from typing import List, Self, Tuple
from collections import deque

class Node:
    def __init__(self, _value) -> None:
        self.parent = None
        self.children = []
        self.value = _value
    
    def append_child(self, n: Self):
        self.children.append(n)
        n.parent = self

class ReparsePoint:
    def __init__(self, _x: int, _y: int, _value) -> None:
        self.x = _x
        self.y = _y
        self.value = _value

print("finish import")

a = Image.open("test_color.png")

data = np.array(a)

# split white place
covered = np.zeros((data.shape[0], data.shape[1]))

candidate: List[Tuple[int]] = []

queue: deque[Tuple[int, int]] = deque()

tree = Node(None)

start = ()
start_color = ()

first_checkpoint = []
for x in range(data.shape[0]):
    first_checkpoint.append((x, 0))
    first_checkpoint.append((x, data.shape[0] - 1))
for y in range(1, data.shape[1] - 1):
    first_checkpoint.append((0, y))
    first_checkpoint.append((data.shape[1] - 1, y))
for c in first_checkpoint:
    queue.append(c)

while len(queue) > 0:
    target = queue.popleft()
    if covered[*target] == 1:
        continue
    current_color = data[*target]
    candidate.append(target)

    tree.append_child(Node(ReparsePoint(*target, current_color)))

    queue_erode: deque[Tuple[int, int]] = deque([target])
    while len(queue_erode) > 0:
        target_erode = queue_erode.popleft()

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next = (target_erode[0] + dx, target_erode[1] + dy)
            if (0 <= next[0] < data.shape[0]
                    and 0 <= next[1] < data.shape[1]
                    and covered[*next] == 0
                ):
                if (data[*next] == current_color).all():
                    covered[*next] = 1
                    queue_erode.append(next)
                else:
                    queue.append(next)
    pass


assert (covered == 1).all()

print(candidate)

b = Image.fromarray(data)
ba = np.array(b)
for p in candidate:
    ba[*p]  = (255, 0, 0, 255)
b = Image.fromarray(ba)
b.show()
# b.save("result.png")
