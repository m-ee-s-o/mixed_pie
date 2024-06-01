from collections import defaultdict
from ..f_keymap.keymap_init import addon_keymaps


km_s = defaultdict(list)


class KMI:
    def __init__(self, km, kmi):
        self.km = km
        self._kmi = kmi
        self.id_user = 0
        self.display_name = None

    def __getattribute__(self, name):
        kmi = super().__getattribute__("_kmi")
        if name == "display_name":
            if (display_name := super().__getattribute__("display_name")) is not None:
                return display_name
            return kmi.name
        elif (attr := getattr(kmi, name, None)):
            return attr
        return super().__getattribute__(name)


def register():
    km_s.clear()
    for km, kmi in addon_keymaps:
        c_kmi = KMI(km, kmi)
        km_s[km.name].append(c_kmi)
        if kmi.name in {"Rotate View", "Scale, 3D View", "Viewport Display"}:
            c_kmi.display_name = kmi.name + f": {km.name}"
    # print(km_s.keys())
