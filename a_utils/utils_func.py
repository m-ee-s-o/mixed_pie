from bpy.types import Event


def get_center(a, b=None):
    total = a + b if b is not None else sum(a)
    return total / 2


def get_input_keys(combine=True):
    modifiers_list = ('PERIOD', 'PLUS', 'MINUS')
    operators_list = ('PLUS', 'MINUS', 'ASTERIX', 'SLASH')
    numbers = {}
    modifiers = {}
    operators = {}
    for i in Event.bl_rna.properties['type'].enum_items:
        identifier = i.identifier
        name = i.name
        name = name.removeprefix("Numpad ")
        if (len(name) == 1) and name.isdigit():
            numbers[identifier] = name
        elif identifier.endswith((modifiers_list)) and not identifier.startswith('NDOF'):
            modifiers[identifier] = name
            if identifier != 'PERIOD':
                operators[identifier] = name
        elif identifier.endswith((operators_list)) and not identifier.startswith(('BACK', 'NDOF')):
            operators[identifier] = name

    return {**numbers, **modifiers, **operators} if combine else (numbers, modifiers, operators)


def recur_get_bcoll_children(parent, children=None):
    if not children:
        children = []
    if not parent.is_expanded:
        return children
    for child in parent.children:
        children.append(child)
        recur_get_bcoll_children(child, children)
    return children


def recur_get_bone_collections(collection):
    bcolls = []
    for bcoll in collection:
        bcolls.append(bcoll)
        bcolls.extend(recur_get_bcoll_children(bcoll))
    return bcolls
