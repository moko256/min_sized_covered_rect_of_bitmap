import numpy as np
from PIL import Image, ImageOps
from typing import List, Dict, Self, Tuple, TypeVar, Generic
from enum import Enum, auto
from collections import deque


Node_T = TypeVar("Node_T")


class Node(Generic[Node_T]):
    def __init__(self, _value: Node_T) -> None:
        self.parent: Node[Node_T] = None
        self.children: List[Node_T] = []
        self.value: Node_T = _value

    def append_child(self, n: Self):
        self.children.append(n)
        n.parent = self


class ReparsePoint:
    def __init__(self, _x: int, _y: int, _value: Node_T) -> None:
        self.x = _x
        self.y = _y
        self.value = _value


def is_in_range(data, coord) -> bool:
    assert len(coord) <= len(data.shape)
    for m, v in zip(data.shape, coord):
        if not (0 <= v < m):
            return False
    return True


def collect_reparse_point(data) -> Node[ReparsePoint]:
    covered = np.zeros((data.shape[0], data.shape[1]))

    tree: Node = Node(None)

    queue: deque[Tuple[Node, Tuple[int, int]]] = deque()

    first_checkpoint = []
    for x in range(data.shape[0]):
        first_checkpoint.append((x, 0))
        first_checkpoint.append((x, data.shape[1] - 1))
    for y in range(1, data.shape[1] - 1):
        first_checkpoint.append((0, y))
        first_checkpoint.append((data.shape[0] - 1, y))
    for c in first_checkpoint:
        queue.append((tree, c))

    while len(queue) > 0:
        parent_node, target = queue.popleft()
        if covered[*target] == 1:
            continue
        covered[*target] = 1
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


class PathDir(Enum):
    Up = auto()
    Down = auto()
    Left = auto()
    Right = auto()


class IslandPathData:
    def __init__(self, _x: int, _y: int, _path: List[PathDir]) -> None:
        self.start_x = _x
        self.start_y = _y
        self.path = _path


path_dir_inverted = {
    PathDir.Up: PathDir.Down,
    PathDir.Down: PathDir.Up,
    PathDir.Left: PathDir.Right,
    PathDir.Right: PathDir.Left,
}

path_dir_to_coord_diff = {
    PathDir.Up: (0, -1),
    PathDir.Down: (0, 1),
    PathDir.Left: (-1, 0),
    PathDir.Right: (1, 0),
}


def to_bi_order(d: Dict[PathDir, PathDir]):
    new_d = {
        **d,
        **{path_dir_inverted[v]: path_dir_inverted[k] for k, v in d.items()},
    }
    return new_d


# Defines paterns
#          key: Down   = where came from
#             1  v  0
# value: Left <- *     = where going
#             0     0
to_paths_patterns_color_invertable = {
    (0, 0,
     0, 0): {},
    (1, 0,
     0, 0): to_bi_order({PathDir.Down: PathDir.Left}),
    (0, 1,
     0, 0): to_bi_order({PathDir.Down: PathDir.Right}),
    (0, 0,
     1, 0): to_bi_order({PathDir.Up: PathDir.Left}),
    (0, 0,
     0, 1): to_bi_order({PathDir.Up: PathDir.Right}),
    (1, 0,
     1, 0): to_bi_order({PathDir.Down: PathDir.Down}),
    (1, 1,
     0, 0): to_bi_order({PathDir.Right: PathDir.Right}),
}
to_paths_patterns = {
    **to_paths_patterns_color_invertable,
    **{tuple([1-ik for ik in k]): v for k, v in to_paths_patterns_color_invertable.items()},

    # Special patterns
    # When we invert colors, we need invert I/O directions.
    (1, 0,
     0, 1): to_bi_order({PathDir.Down: PathDir.Left, PathDir.Up: PathDir.Right}),
    (0, 1,
     1, 0): to_bi_order({PathDir.Down: PathDir.Right, PathDir.Up: PathDir.Left}),
}


def island_to_paths(data, start: Tuple[int, int], target_color) -> IslandPathData:
    start_coord_under_pixel: Tuple[int, int] = None
    start_dir = None
    for (dx, dy), (cupx, cupy), next_dir in [
        ((-1, 0), (0, 1), PathDir.Up),
        ((1, 0),  (1, 0), PathDir.Down),
        ((0, -1), (0, 0), PathDir.Right),
        ((0, 1),  (1, 1), PathDir.Left),
    ]:
        next = (start[0] + dx, start[1] + dy)
        if not (is_in_range(data, next) and (data[*next] == target_color).all()):
            start_coord_under_pixel = (start[0] + cupx, start[1] + cupy)
            start_dir = next_dir
            break
    assert start_coord_under_pixel != None  # Inside the wall!
    assert start_dir != None

    path: List[PathDir] = [start_dir]
    current_coord_under_pixel: Tuple[int, int] = start_coord_under_pixel

    def target_color_or_zero(data, now, offset, target_color):
        nx, ny = now
        ox, oy = offset
        coord = (nx + ox, ny + oy)
        if is_in_range(data, coord) and (data[coord] == target_color).all():
            return 1
        return 0

    while True:
        last_move = path[-1]
        cx, cy = current_coord_under_pixel
        ndx, ndy = path_dir_to_coord_diff[last_move]
        nd = (cx + ndx, cy + ndy)
        current_coord_under_pixel = nd

        if current_coord_under_pixel == start_coord_under_pixel:
            break

        near_pixels = (
            target_color_or_zero(data, nd, (-1, -1), target_color),
            target_color_or_zero(data, nd, (0, -1), target_color),
            target_color_or_zero(data, nd, (-1, 0), target_color),
            target_color_or_zero(data, nd, (0, 0), target_color),
        )
        next_move = to_paths_patterns[near_pixels][last_move]

        path.append(next_move)
    return IslandPathData(*start_coord_under_pixel, path)


class IslandEdge:
    def __init__(self, _start_x: int, _start_y: int, _end_x: int, _end_y: int, _length: int, _dir: PathDir) -> None:
        self.start_x = _start_x
        self.start_y = _start_y
        self.end_x = _end_x
        self.end_y = _end_y
        self.length = _length
        self.dir = _dir


def normalize_island_path_to_edges(path: IslandPathData) -> List[IslandEdge]:
    new_path: List[IslandEdge] = []

    continueing_length = 1
    cx = path.start_x
    cy = path.start_y
    for i in range(1, len(path.path) + 1):
        before = i - 1
        if i >= len(path.path) or path.path[before] != path.path[i]:
            dx, dy = path_dir_to_coord_diff[path.path[before]]
            cex = cx + dx * continueing_length
            cey = cy + dy * continueing_length

            new_path.append(
                IslandEdge(
                    cx, cy,
                    cex, cey,
                    continueing_length,
                    path.path[before]
                )
            )

            cx = cex
            cy = cey
            continueing_length = 1
        else:
            continueing_length += 1
    if len(new_path) >= 3:
        if new_path[0].dir == new_path[-1].dir:
            # Closed?
            assert new_path[-1].end_x == new_path[0].start_x
            assert new_path[-1].end_y == new_path[0].start_y

            new_path[0].start_x = new_path[-1].start_x
            new_path[0].start_y = new_path[-1].start_y
            new_path[0].length += new_path[-1].length
            del new_path[-1]
    return new_path


class Rect:
    def __init__(self, _x: int, _y: int, _w: int, _h: int, _color) -> None:
        self.x = _x
        self.y = _y
        self.w = _w
        self.h = _h
        self.color = _color


def split_into_rect(edges: List[IslandEdge], color) -> List[Rect]:
    # 'Non-degeneracy' island only.
    y_list: List[int] = []
    for i, e in enumerate(edges):
        if e.dir in [PathDir.Left, PathDir.Right]:
            assert e.start_y == e.end_y
            y_list.append(i)
    y_list.sort(key=lambda i: edges[i].end_y)

    x_list: List[int] = []
    x_list_top_y: Dict[int, int] = {}
    for i, e in enumerate(edges):
        if e.dir in [PathDir.Up, PathDir.Down]:
            assert e.start_x == e.end_x
            x_list_top_y[i] = min([e.start_y, e.end_y])

    rects = []

    def x_insert(i: int):
        x_list.append(i)

    def x_delete(i: int):
        x_list.remove(i)

    def x_extract(h: IslandEdge):
        assert h.start_y == h.end_y
        h_left_x = min([h.start_x, h.end_x])
        h_right_x = max([h.start_x, h.end_x])
        left_i: int = None
        right_i: int = None
        left: IslandEdge = None
        right: IslandEdge = None
        for xi in x_list:
            xv = edges[xi]
            xt = x_list_top_y[xi]
            if xt < h.start_y:
                assert xv.start_x == xv.end_x
                if xv.start_x <= h_left_x and (not (left != None and xv.start_x <= left.start_x)):
                    left_i = xi
                    left = xv
                elif xv.start_x >= h_right_x and (not (right != None and xv.start_x >= right.start_x)):
                    right_i = xi
                    right = xv
        assert left == None or left.dir == PathDir.Up
        assert right == None or right.dir == PathDir.Down

        if h.dir == PathDir.Right:
            assert left != None or right != None
            if left != None:
                rects.append(Rect(
                    left.start_x,
                    x_list_top_y[left_i],
                    h.start_x - left.start_x,
                    h.start_y - x_list_top_y[left_i],
                    color,
                ))

            if right != None:
                rects.append(Rect(
                    h.end_x,
                    x_list_top_y[right_i],
                    right.start_x - h.end_x,
                    h.end_y - x_list_top_y[right_i],
                    color,
                ))
        elif h.dir == PathDir.Left:
            assert left != None and right != None
            rects.append(Rect(
                left.start_x,
                x_list_top_y[right_i],
                right.start_x - left.start_x,
                h.end_y - x_list_top_y[left_i],
                color,
            ))
        else:
            assert False

        x_list_top_y[left_i] = h.start_y
        x_list_top_y[right_i] = h.start_y

    for hi in y_list:
        H = edges[hi]
        # Edges is closed loop.
        before_index = hi-1
        after_index = (hi+1) % len(edges)

        before = edges[before_index]
        after = edges[after_index]

        from_to_dir = (before.dir, after.dir)
        if H.dir == PathDir.Right:
            A = before
            B = after
            A_index = before_index
            B_index = after_index
            if from_to_dir == (PathDir.Up, PathDir.Down):
                # 1)
                x_insert(A_index)
                x_insert(B_index)
            elif from_to_dir == (PathDir.Down, PathDir.Up):
                # 3)
                x_delete(A_index)
                x_delete(B_index)
                x_extract(H)
            elif from_to_dir == (PathDir.Down, PathDir.Down):
                # 8)
                x_insert(A_index)
                x_delete(B_index)
                x_extract(H)
            elif from_to_dir == (PathDir.Up, PathDir.Up):
                # 7)
                x_insert(A_index)
                x_delete(B_index)
                x_extract(H)
            else:
                assert False  # Unnormalized path.
        elif H.dir == PathDir.Left:
            A = after
            B = before
            A_index = after_index
            B_index = before_index
            if from_to_dir == (PathDir.Up, PathDir.Down):
                # 2)
                x_insert(A_index)
                x_insert(B_index)
                x_extract(H)
            elif from_to_dir == (PathDir.Down, PathDir.Up):
                # 3)
                x_extract(H)  # extract first
                x_delete(A_index)
                x_delete(B_index)
            elif from_to_dir == (PathDir.Down, PathDir.Down):
                # 5)
                x_insert(A_index)
                x_delete(B_index)
                x_extract(H)
            elif from_to_dir == (PathDir.Up, PathDir.Up):
                # 6)
                x_insert(A_index)
                x_delete(B_index)
                x_extract(H)
            else:
                assert False  # Unnormalized path.
        else:
            assert False  # Not horizontal edge.

    assert len(x_list) == 0

    return rects


# DO NOT FORGET THAT PIL USES X DOWN AXIS
def left_x_down_y_to_pil_axis(data):
    return np.transpose(data, (1, 0, 2))


def pil_axis_to_left_x_down_y(data):
    return np.transpose(data, (1, 0, 2))


def main1():
    a = Image.open("test_color.png")
    data = np.array(pil_axis_to_left_x_down_y(a))

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

    ba = np.array(data)
    for l, p in candidate:
        ba[*p] = (255, 255 / l, 0, 255)
    b = Image.fromarray(left_x_down_y_to_pil_axis(ba))
    b.show()
    # b.save("result.png")


def main2():
    data = np.ones((3, 3, 3), dtype=np.uint8) * 255
    data[0, 1] = (255, 0, 0)
    data[1, 1] = (255, 0, 0)
    data[1, 0] = (255, 0, 0)
    data[2, 2] = (255, 0, 0)

    ipd = island_to_paths(data, (1, 1), (255, 0, 0))
    print(ipd.start_x)
    print(ipd.start_y)
    print(ipd.path)

    b = Image.fromarray(data, mode="RGB")
    # b.show()
    # b.save("result2.png")


def main3():
    a = Image.open("test_color.png")
    data = pil_axis_to_left_x_down_y(np.array(a))

    reparsed = collect_reparse_point(data)

    candidate: List[Tuple[int, ReparsePoint]] = []
    queue = deque([reparsed])
    level = 0
    while len(queue) > 0:
        level += 1
        c = queue.popleft()
        for nc in c.children:
            candidate.append((level, nc.value))
            queue.append(nc)

    for l, rp in candidate:
        path = island_to_paths(data, (rp.x, rp.y), rp.value)
        color_hex = "#" + "".join(f"{n:02X}" for n in [
                                  rp.value[0], rp.value[1], rp.value[2]]) + f" ({rp.value[3]/255.0*100:.1f}%)"

        npd = normalize_island_path_to_edges(path)
        pc = " ".join([
            f"({v.start_x}, {v.start_y})"
            + {PathDir.Up: "↑", PathDir.Down: "↓",
               PathDir.Left: "←", PathDir.Right: "→"}[v.dir]
            + f"{v.length}({v.end_x}, {v.end_y})"
            for v in npd
        ])
        print(
            f"Depth: {l}, Start: ({path.start_x}, {path.start_y}), Color: {color_hex}\n{pc}\n")


def main4():
    data = np.ones((3, 3, 3), dtype=np.uint8) * 255
    data[0, 1] = (255, 0, 0)
    data[1, 1] = (255, 0, 0)
    data[1, 0] = (255, 0, 0)
    data[2, 2] = (255, 0, 0)

    ipd = island_to_paths(data, (1, 1), (255, 0, 0))
    print(ipd.start_x)
    print(ipd.start_y)
    print(ipd.path)

    npd = normalize_island_path_to_edges(ipd)
    rects = split_into_rect(npd, (0, 0, 1))
    for r in rects:
        print(f"{r.x},{r.y},{r.w},{r.h}")


if __name__ == "__main__":
    print("start main")
    main4()
