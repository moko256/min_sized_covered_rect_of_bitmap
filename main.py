import numpy as np
from PIL import Image, ImageOps
from typing import List, Tuple
from collections import deque


print("finish import")

a = ImageOps.invert(Image.open("test.bmp").convert("1"))

data = np.array(a)

# split white place
covered = np.zeros_like(data)

candidate: List[Tuple[int]] = []

queue: deque[Tuple[int, int]] = deque([(0, 0)])
assert data[0, 0] == 0

while len(queue) > 0:
    target = queue.popleft()
    if covered[*target] == 1:
        continue
    current_color = data[*target]
    candidate.append(target)

    queue_erode: deque[Tuple[int, int]] = deque([target])
    while len(queue_erode) > 0:
        target_erode = queue_erode.popleft()

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            next = (target_erode[0] + dx, target_erode[1] + dy)
            if (0 <= next[0] < data.shape[0]
                    and 0 <= next[1] < data.shape[1]
                    and covered[*next] == 0
                ):
                if data[*next] == current_color:
                    covered[*next] = 1
                    queue_erode.append(next)
                else:
                    queue.append(next)
    pass


assert (covered == 1).all()

print(candidate)

b = Image.fromarray(data).convert("RGB")
ba = np.array(b)
for p in candidate:
    ba[*p]  = (255, 0, 0)
b = Image.fromarray(ba)
b.show()
# b.save("result.png")
