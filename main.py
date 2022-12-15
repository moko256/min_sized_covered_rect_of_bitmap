import numpy as np
from PIL import Image, ImageOps
from typing import List, Tuple
from collections import deque

a = ImageOps.invert(Image.open("test.bmp").convert("1"))

data = np.array(a)

# split white place
one_fill = data.copy()
inner_starts: List[Tuple[int, int]] = []
while True:
    it = np.nditer(one_fill, flags=["multi_index"])
    inner_place = None
    while not it.finished:
        pos = it.multi_index
        if it.value == 1:
            inner_place = pos
            break
        it.iternext()
    if inner_place == None:
        break
    inner_starts.append(inner_place)

    one_fill[*inner_place] = 0

    queue: deque[Tuple[int, int]] = deque([inner_place])
    while len(queue) > 0:
        target = queue.popleft()

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next = (target[0] + dx, target[1] + dy)
            if (0 <= next[0] < one_fill.shape[0]
                    and 0 <= next[1] < one_fill.shape[1]
                    and one_fill[*next] == 1):
                queue.append(next)
                one_fill[*next] = 0

assert (one_fill == 0).all()

print(inner_starts)

b = Image.fromarray(data)
b.show()
