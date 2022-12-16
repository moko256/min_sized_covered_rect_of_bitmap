import numpy as np
from PIL import Image, ImageOps
from typing import List, Self, Tuple, TypeVar, Generic
from collections import deque


Node_T = TypeVar("Node_T")


class Node(Generic[Node_T]):
    def __init__(self, _value: Node_T) -> None:
        self.parent = None
        self.children = []
        self.value = _value

    def append_child(self, n: Self):
        self.children.append(n)
        n.parent = self


class ReparsePoint:
    def __init__(self, _x: int, _y: int, _value: Node_T) -> None:
        self.x = _x
        self.y = _y
        self.value = _value


def collect_reparse_point(data) -> Node:
    covered = np.zeros((data.shape[0], data.shape[1]))

    tree: Node = Node(None)

    queue: deque[Tuple[Node, Tuple[int, int]]] = deque()

    first_checkpoint = []
    for x in range(data.shape[0]):
        first_checkpoint.append((x, 0))
        first_checkpoint.append((x, data.shape[0] - 1))
    for y in range(1, data.shape[1] - 1):
        first_checkpoint.append((0, y))
        first_checkpoint.append((data.shape[1] - 1, y))
    for c in first_checkpoint:
        queue.append((tree, c))

    while len(queue) > 0:
        parent_node, target = queue.popleft()
        if covered[*target] == 1:
            continue
        current_color = data[*target]

        next_node = Node(ReparsePoint(*target, current_color))
        parent_node.append_child(next_node)

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
                        queue.append((next_node, next))
        pass

    assert (covered == 1).all()
    return tree


def main():
    print("start main")

    a = Image.open("test_color.png")
    data = np.array(a)

    reparsed = collect_reparse_point(data)

    candidate = []
    queue = deque([reparsed])
    level = 0
    while len(queue) > 0:
        level += 1
        c = queue.popleft()
        for nc in c.children:
            candidate.append((level, (nc.value.x, nc.value.y)))
            queue.append(nc)

    b = Image.fromarray(data)
    ba = np.array(b)
    for l, p in candidate:
        ba[*p] = (255, 255 / l, 0, 255)
    b = Image.fromarray(ba)
    b.show()
    # b.save("result.png")

if __name__ == "__main__":
    main()