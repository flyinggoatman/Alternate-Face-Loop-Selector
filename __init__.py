"""
Alternating Face Loop Selector
Quickly select alternating face loops (horizontal or vertical) in mesh edit mode.

This extension provides a specialized selection tool that allows users to select
every other face loop in a mesh. It works by analyzing mesh topology to identify
parallel face loops and then applies a configurable selection pattern.
"""

import bpy
import bmesh

class MESH_OT_alternate_face_loops(bpy.types.Operator):
    """Select alternating face loops (every other loop in horizontal or vertical direction)"""
    bl_idname = "mesh.alternate_face_loops"
    bl_label = "Alternate Face Loops"
    bl_options = {'REGISTER', 'UNDO'}

    skip: bpy.props.IntProperty(
        name="Skip Count",
        description="Number of loops to skip between selections (skip=1 for every other loop)",
        default=1, min=1, max=100
    )
    offset: bpy.props.IntProperty(
        name="Offset",
        description="Offset value (0 = include first loop, 1 = skip it, etc.)",
        default=0, min=0, max=10,
        options={'HIDDEN'}
    )

    
    repeat: bpy.props.IntProperty(
        name="Repeat",
        description="Maximum iterations until no new faces are selected",
        default=5, min=1, max=20
    )
    debug_mode: bpy.props.BoolProperty(
        name="Debug Mode",
        description="Show detailed diagnostic output during execution",
        default=False
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and 
                obj.mode == 'EDIT' and 
                obj.type == 'MESH' and 
                context.tool_settings.mesh_select_mode[2])  # face select mode

    def _debug_print(self, msg):
        if self.debug_mode:
            print(msg)

    def _connected_loop_component(self, face_list):
        self._debug_print(f"[COMP] Starting connected component on {len(face_list)} faces.")
        if not face_list:
            return []
        visited_local = set()
        comp = []
        to_visit = [face_list[0]]
        while to_visit:
            f = to_visit.pop()
            if f in visited_local:
                continue
            visited_local.add(f)
            comp.append(f)
            for e in f.edges:
                for nb in e.link_faces:
                    if nb in face_list and nb not in visited_local:
                        to_visit.append(nb)
        self._debug_print(f"[COMP] Component complete with {len(comp)} faces: {[f.index for f in comp]}")
        return comp

    def _trace_face_loop(self, bm, start_face, start_edge):
        self._debug_print(f"[TRACE] Starting trace on Face #{start_face.index}.")
        loop_faces = []
        face = start_face
        prev_face = None
        real_start_face = start_face
        edge_to_enter = start_edge
        if edge_to_enter is None:
            if len(start_face.edges) < 2:
                self._debug_print("[TRACE] Not enough edges; returning start face.")
                return [start_face]
            edge_to_enter = list(start_face.edges)[0]
        self._debug_print(f"[TRACE] Using edge with {len(edge_to_enter.link_faces)} linked faces.")

        def get_opposite_edge(face_, edge_):
            if len(face_.edges) != 4:
                for e_ in face_.edges:
                    if e_ != edge_:
                        return e_
                return edge_
            face_edges = list(face_.edges)
            if edge_ in face_edges:
                idx = face_edges.index(edge_)
                opp_idx = (idx + 2) % 4
                return face_edges[opp_idx]
            return edge_

        opp_edge = get_opposite_edge(face, edge_to_enter)
        loop_faces.append(face)
        max_traversal = 200
        traversal_count = 0
        while traversal_count < max_traversal:
            traversal_count += 1
            next_face = None
            for lf in opp_edge.link_faces:
                if lf is not face:
                    next_face = lf
                    break
            self._debug_print(f"[TRACE] Traversal {traversal_count}: Current Face #{face.index} via Edge with {len(opp_edge.link_faces)} linked faces.")
            if not next_face:
                self._debug_print("[TRACE] No next face found; breaking trace.")
                break
            if next_face == real_start_face:
                self._debug_print(f"[TRACE] Returned to start Face #{real_start_face.index}. Loop complete.")
                if next_face not in loop_faces:
                    loop_faces.append(next_face)
                break
            if next_face in loop_faces:
                self._debug_print(f"[TRACE] Face #{next_face.index} already in loop (partial cycle). Breaking trace.")
                break
            shared_edge = opp_edge
            prev_face = face
            face = next_face
            opp_edge = get_opposite_edge(face, shared_edge)
            loop_faces.append(face)
        if traversal_count >= max_traversal:
            self._debug_print("[TRACE] Max traversal reached; possible infinite loop prevention.")
        self._debug_print(f"[TRACE] Completed trace with {len(loop_faces)} faces: {[f.index for f in loop_faces]}")
        return loop_faces

    def execute(self, context):
        # If you want to always use fixed values, you could define them here
        # skip, offset, repeat = 1, 0, 5
        # self.debug_mode = False
        # But for now, we'll keep them as operator properties (they just won't be shown in the UI)

        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()

        if self.debug_mode:
            print("\n=== [Alternate Face Loops] START ===")

        iteration = 0
        prev_selected_count = -1

        while iteration < self.repeat:
            iteration += 1
            self._debug_print(f"\n>>> AUTOMATIC ITERATION {iteration}")
            current_selected = [f for f in bm.faces if f.select]
            current_count = len(current_selected)
            self._debug_print(f"[EXEC] Selected faces before iteration: {current_count}")

            if current_count == prev_selected_count:
                self._debug_print("[EXEC] No new faces selected in last iteration. Stopping automatic iterations.")
                break
            prev_selected_count = current_count

            init_faces = [f for f in bm.faces if f.select]
            if not init_faces:
                self.report({'WARNING'}, "No faces selected")
                return {'CANCELLED'}
            initial_loop = []
            if len(init_faces) == 1:
                start_face = init_faces[0]
                loop_candidates = []
                if len(start_face.edges) == 4:
                    edges = list(start_face.edges)
                    edge_pairs = [(edges[0], edges[2]), (edges[1], edges[3])]
                else:
                    edge_pairs = [(e, e) for e in start_face.edges]
                for e_pair in edge_pairs:
                    loop = self._trace_face_loop(bm, start_face, e_pair[0])
                    if loop:
                        loop_candidates.append(loop)
                if loop_candidates:
                    initial_loop = max(loop_candidates, key=lambda L: len(L))
                else:
                    initial_loop = [start_face]
            else:
                faces_set = set(init_faces)
                continuous = True
                for f in init_faces:
                    neighbors_in_selection = sum(
                        (1 for e in f.edges for adj in e.link_faces if adj != f and adj in faces_set)
                    )
                    if neighbors_in_selection > 2:
                        continuous = False
                        break
                if continuous:
                    initial_loop = init_faces.copy()
                else:
                    active_face = bm.faces.active or init_faces[0]
                    initial_loop = self._trace_face_loop(bm, active_face, None) or [active_face]
            self._debug_print(f"[EXEC] Derived initial loop with {len(initial_loop)} faces: {[f.index for f in initial_loop]}")
            for f in initial_loop:
                f.select = True

            visited = set(initial_loop)
            loops = [initial_loop]
            frontier_above = initial_loop[:]
            frontier_below = initial_loop[:]
            iterations_bfs = 0
            max_iterations = 1000
            side_index = 1
            while (frontier_above or frontier_below) and iterations_bfs < max_iterations:
                iterations_bfs += 1
                self._debug_print(f"--- BFS Iteration {iterations_bfs}, side_index={side_index} ---")
                next_above = []
                next_below = []
                for face in frontier_above:
                    for edge in face.edges:
                        for nb in edge.link_faces:
                            if nb != face and nb not in visited:
                                next_above.append(nb)
                                visited.add(nb)
                self._debug_print(f"[BFS] Found {len(next_above)} new faces above.")
                if next_above:
                    comp = self._connected_loop_component(next_above)
                    self._debug_print(f"[BFS] Above component has {len(comp)} faces: {[f.index for f in comp]}")
                    if comp:
                        loops.append(comp)
                for face in frontier_below:
                    for edge in face.edges:
                        for nb in edge.link_faces:
                            if nb != face and nb not in visited:
                                next_below.append(nb)
                                visited.add(nb)
                self._debug_print(f"[BFS] Found {len(next_below)} new faces below.")
                if next_below:
                    comp = self._connected_loop_component(next_below)
                    self._debug_print(f"[BFS] Below component has {len(comp)} faces: {[f.index for f in comp]}")
                    if comp:
                        loops.append(comp)
                frontier_above = next_above
                frontier_below = next_below
                side_index += 1
                if not next_above and not next_below:
                    self._debug_print("[BFS] No more faces found; BFS expansion ended.")
                    break
            if iterations_bfs >= max_iterations:
                self._debug_print("[BFS] Warning: Reached BFS iteration limit.")
            if not loops:
                self.report({'WARNING'}, "No face loops found for the selection.")
                return {'CANCELLED'}
            self._debug_print(f"[EXEC] BFS produced {len(loops)} loop sets (raw).")
            total_loops = len(loops)
            step = self.skip + 1
            start_index = self.offset
            to_select_indices = set(range(start_index, total_loops, step))
            self._debug_print(f"[EXEC] Using skip={self.skip}, offset={self.offset}, total_loops={total_loops}.")
            self._debug_print(f"[EXEC] Loop indices to select: {to_select_indices}.")
            for i, loop_faces in enumerate(loops):
                self._debug_print(f"  Loop index={i} has {len(loop_faces)} faces: {[f.index for f in loop_faces]}")
            for idx, loop_faces in enumerate(loops):
                select_flag = (idx in to_select_indices)
                for f in loop_faces:
                    f.select = select_flag
            try:
                bmesh.update_edit_mesh(me)
            except TypeError:
                bmesh.update_edit_mesh(me)
            current_selected = [f for f in bm.faces if f.select]
            new_count = len(current_selected)
            self._debug_print(f"[EXEC] Selected faces after iteration: {new_count}")
        if self.debug_mode:
            print("=== [Alternate Face Loops] END ===\n")
        return {'FINISHED'}

class MESH_PT_alt_face_loops(bpy.types.Panel):
    bl_label = "Alternate Face Loops"
    bl_idname = "MESH_PT_alt_face_loops"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Select"
    bl_context = "mesh_edit"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.mode == 'EDIT' and
                context.active_object.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        # Just show a single button for running the operator
        col.label(text="Run Alternate Face Loops:")
        col.operator(MESH_OT_alternate_face_loops.bl_idname,
                     text="Select Alternate Face Loops", icon='SELECT_INTERSECT')
        # Optionally show debug mode only:
        layout.prop(context.window_manager, "afl_debug", text="Debug Mode")

def menu_func_face(self, context):
    self.layout.separator()
    self.layout.operator(MESH_OT_alternate_face_loops.bl_idname,
                         text="Alternate Face Loops", icon='SELECT_INTERSECT')

classes = (MESH_OT_alternate_face_loops, MESH_PT_alt_face_loops)

def register():
    bpy.types.WindowManager.afl_debug = bpy.props.BoolProperty(
        name="Debug Mode",
        description="Show detailed diagnostics in the console",
        default=False
    )
    # The other props (afl_skip, afl_offset, afl_repeat) are still defined on the operator
    # but we won't expose them in the UI anymore.
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu_func_face)

def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu_func_face)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.afl_debug

if __name__ == "__main__":
    register()
