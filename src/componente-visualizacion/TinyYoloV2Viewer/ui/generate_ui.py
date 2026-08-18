import bpy
from bpy.types import Panel


class OBJECT_PT_GeoNodesGeneratorPanel(Panel):
    """Draws a button in the 3D Viewport N-Panel"""
    bl_label = "GeoNodes Generator"
    bl_idname = "OBJECT_PT_geonodes_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "My Extension"

    def draw(self, context):
        layout = self.layout
        
        # Primary instantiation button
        col = layout.column(align=True)
        op = col.operator("mesh.create_geonodes_object", text="Add GeoNodes Mesh", icon='GEOMETRY_NODES')
        
        # Optional: override node group name dynamically if needed
        # op.node_group_name = "MyNodeGroup"