from bpy.types import Context, Operator


class Rigify_Layers_Name_0_to_18_and_28_to_31:
    RIGIFY_0_18 = ('Face', 'Face (Primary)', 'Face (Secondary)',
                'Torso', 'Torso (Tweak)',
                'Fingers', 'Fingers (Detail)',
                'Arm.L (IK)', 'Arm.L (FK)', 'Arm.L (Tweak)',
                'Arm.R (IK)', 'Arm.R (FK)', 'Arm.R (Tweak)',
                'Leg.L (IK)', 'Leg.L (FK)', 'Leg.L (Tweak)',
                'Leg.R (IK)', 'Leg.R (FK)', 'Leg.R (Tweak)',
                )
    RIGIFY_28_31 = ('Root', 'DEF', 'MCH', 'ORG')

    @classmethod
    def execute(cls, operator: Operator, context: Context):
        b_coll = context.object.data.collections
        for coll in b_coll:
            split = coll.name.split(" ")
            if len(split) == 2 and split[1].isdigit():
                index = int(split[1]) - 1
                if 0 <= index < 18:
                    name = cls.RIGIFY_0_18[index]
                elif 28 <= index < 32:
                    name = cls.RIGIFY_28_31[index - 28]
                coll.name = name
