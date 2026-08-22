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

        ## Tamaños
        box = layout.box()
        box.label(text="Dimensiones", icon="FIXED_SIZE")
        col = box.column(align=True)
        col.prop(vis_props, "size_scale")
        col.prop(vis_props, "layer_depth")
        col.prop(vis_props, "layer_gap")
        col.prop(vis_props, "layer_max_depth")

        # Visibilidad
        box = layout.box()
        box.label(text="Visibilidad", icon="HIDE_OFF")
        col = box.column(align=True)

        for item in vis_props.layer_properties:
            row = col.row()
            row.prop(item, "color", text=item.name)
            row.prop(item, "visibility", text="Simple")

        col = layout.column(align=True)
        layout.separator()
        layout.operator("mesh.create_geonodes_object", text="Generar geometría", icon='GEOMETRY_NODES')

