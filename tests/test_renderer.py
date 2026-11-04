"""Run: python3 -m unittest discover -s tests"""
import os, sys, types, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FB:
    def __init__(s, w=250, h=128): s.w, s.h, s.p = w, h, {}
    def fill(s, c): s.p = {}; s.bg = c
    def pixel(s, x, y, c): s.p[(x, y)] = c
    def fill_rect(s, x, y, w, h, c):
        for i in range(w):
            for j in range(h): s.p[(x + i, y + j)] = c
    def rect(s, x, y, w, h, c):
        for i in range(w): s.p[(x + i, y)] = c; s.p[(x + i, y + h - 1)] = c
        for j in range(h): s.p[(x, y + j)] = c; s.p[(x + w - 1, y + j)] = c
    def hline(s, x, y, w, c): s.fill_rect(x, y, w, 1, c)


cfg = types.ModuleType("config")
cfg.FLOOR_ORDER = ["Fourth Floor", "Third Floor", "Second Floor", "Ground Floor"]
cfg.FLOOR_NICKNAMES = {"Second Floor": "2F", "Ground Floor": "1F", "Third Floor": "3F"}
cfg.ZONE_NICKNAMES = {("Ground Floor", "Living"): "1F Lounge"}
sys.modules["config"] = cfg
import renderer  # noqa: E402


def P(name, floor=None, zone=None, away=False, seen=None):
    return {"name": name, "floor": floor, "zone": zone, "away": away or floor is None, "seen": seen}


PEOPLE = [P("Ben", "Ground Floor", "Living"), P("Alice", "Second Floor", "Bedroom"), P("Dan", seen="11:30"),
          P("Eli", "Third Floor", "Study"), P("Cara", "Ground Floor", "Kitchen")]


class T(unittest.TestCase):
    def setUp(self):
        for k in ("PEOPLE_PRIORITY", "PEOPLE_ONLY", "PEOPLE_HIDE", "SHOW_AWAY"):
            if hasattr(cfg, k): delattr(cfg, k)

    def names(self): return [p["name"] for p in renderer.select_people(PEOPLE)]

    def test_default_order_floor_then_away_last(self):
        self.assertEqual(self.names(), ["Eli", "Alice", "Ben", "Cara", "Dan"])

    def test_priority_first_even_if_away(self):
        cfg.PEOPLE_PRIORITY = ["dan", "Ben"]
        self.assertEqual(self.names()[:2], ["Dan", "Ben"])

    def test_only_and_hide_and_no_away(self):
        cfg.PEOPLE_ONLY = ["alice", "ben", "dan"]; cfg.PEOPLE_HIDE = ["Ben"]; cfg.SHOW_AWAY = False
        self.assertEqual(self.names(), ["Alice"])
        cfg.PEOPLE_PRIORITY = ["Dan"]   # priority names show even when away is off
        self.assertEqual(self.names(), ["Dan", "Alice"])

    def test_where(self):
        self.assertEqual(renderer.where("Ground Floor", "Living"), "1F Lounge")          # nickname
        self.assertEqual(renderer.where("Third Floor", "Study"), "3F Study")             # floor nick + zone
        self.assertEqual(renderer.where("Third Floor", "Very Long Zone Name"), "3F Very Long")  # cut to 12
        self.assertEqual(renderer.where("Nowhere", None), "Nowhere")

    def test_renders_overflow_and_status(self):
        many = PEOPLE + [P("Fay", "Ground Floor", "Hall"), P("Gus", "Ground Floor", "Hall")]
        b, r = FB(), FB()
        renderer.render(b, r, many, {"Alice"})
        self.assertTrue(any(c == 0 for c in r.p.values()))   # red tile for the mover
        renderer.render_status(b, r, "Token rejected", ["a", "b"])


if __name__ == "__main__":
    unittest.main()
