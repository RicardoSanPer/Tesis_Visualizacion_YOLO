import bpy
from bpy.types import Panel


class VIEW3D_PT_GeoNodesGeneratorPanel(Panel):
    """Draws a button in the 3D Viewport N-Panel"""
    bl_label = "GeoNodes Generator"
    bl_idname = "OBJECT_PT_geonodes_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "My Extension"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        vis_props = scene.yolo_visualization_settings
        
        col = layout.column(align=True)
        col.prop(vis_props, "size_scale")
        col.prop(vis_props, "layer_gap")

        #colores
        box = layout.box()
        col = box.column(align=True)

        for color in vis_props.layer_colors:
            row = col.row()
            row.prop(color, "color", text=color.name)

        col = layout.column(align=True)
        layout.separator()
        layout.operator("mesh.create_geonodes_object", text="Add GeoNodes Mesh", icon='GEOMETRY_NODES')

