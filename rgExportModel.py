# Blender WebGL Exporter
# Ruben Garza, Jr.
# Created 2014-01-21

bl_info = {
  "name": "WebGL Export",
  "author": "Ruben Garza, Jr.",
  "version": (2, 0, 0),
  "blender": (3, 4, 0),
  "location": "File > Import-Export",
  "description": "Export WebGL",
  "category": "Import-Export"
}

import bpy
import os
import math
from datetime import datetime
import mathutils
from mathutils import Vector
from bpy.props import StringProperty, FloatProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import (ImportHelper, ExportHelper, axis_conversion,)
import bmesh
import numpy as np

class ExportGeo(bpy.types.Operator, ExportHelper):
  """Export to webgl file format (.model)""" # blender will use this as a tooltip for menu items and buttons.
  bl_idname = "export_scene.geo"             # unique identifier for buttons and menu items to reference.
  bl_label = "Export Geo"                    # display name in the interface.
  filename_ext = ".geo"

  def execute(self, context):
    keywords = self.as_keywords(ignore=("axis_forward",
                      "axis_up",
                      "filter_glob",
                      "check_existing",
                      ))

    keys = sorted(keywords.keys())
    for kw in keys:
      print(kw, ":", keywords[kw])

    Export.file(self, context, **keywords)
    return {'FINISHED'}

class Export():
  def file(operator, context, filepath="",):
    file_out = open(filepath, 'w')

    if len(bpy.context.selected_objects) < 1:
      return
    selected = bpy.context.selected_objects
    selected_count = len(selected)

    now = datetime.now()
    print('\n\n\nExport\n' + now.strftime("%Y/%m/%d %H:%M:%S"))
    file_out.write('{\n')
    file_out.write(spc(0) + '"meta": {' + '\n')  # Open Meta
    file_out.write(spc(1) + '"filename": "' + bpy.path.basename(bpy.data.filepath) + '",' + '\n')
    file_out.write(spc(1) + '"created": "' + now.strftime("%Y/%m/%d %H:%M:%S") + '"' + '\n')
    file_out.write(spc(0) + '},\n')        # Close Meta

    geoList = []
    armList = []
    for count, model in enumerate(bpy.context.selected_objects):
      print (model.name + " " + model.type + "\n" )
      if model.type == "ARMATURE":
        armList.append(model)
      if model.type == "MESH":
        print("mesh!!!")
        geoList.append(model)

    file_out.write(spc(0) + '"geometry": {\n')

    for count, model in enumerate(geoList):
      last = False if count < len(geoList)-1 else True
      print ('\nGEOMETRY ' + str(count+1) + " of " + str(len(geoList)) + "\nName: " + model.name + "\n" )
      writegeo(model, 0, file_out, last)
    file_out.write(spc(0) +'},\n')
    file_out.write(spc(0) + '"armature": {\n')
    for count, model in enumerate(armList):
      last = False if count < len(armList)-1 else True
      print ('\nARMATURE ' + str(count+1) + " of " + str(len(armList)) + "\nName: " + model.name + "\n" )
      #writegeo(model, 0, file_out, last)
    file_out.write(spc(0) +'}\n')       


    # Close Tags
    file_out.write('}')              # Close JSON
    file_out.close()

    # Finished
    print("done!\n\n")


def zero(number_in):
  number_out = number_in
  if -0.0001 < number_out < 0.0001:
    number_out = 0
  return number_out

def spc(indent):
  print_spacer = " "
  for indentCnt in range(0,indent):
    print_spacer += " "
  return print_spacer

def processArray(inArray):
  digits  = 5
  outStr  = ""
  for count, element in enumerate(inArray):
    if (abs(round(element) - element) < 0.0001):
      outStr += str(round(element))
    else:
      outStr += str(round(element, digits))
    if count < len(inArray)-1:
      outStr +=","
  return outStr

def truncate(number):
  digits  = 5
  stepper = 10.0 ** digits
  return str(math.trunc(stepper * number) / stepper)

def writegeo(node, indent, file_out, last):
  print(spc(indent), node.name, node.type)

  file_out.write(spc(indent+1) + '"'+ node.name + '":{\n')
  file_out.write(spc(indent+2) + '"type": "' + node.type + '",\n')
  file_out.write(spc(indent+2) + '"class": "' + node.get('class', "") + '",\n')
  file_out.write(spc(indent+2) + '"category": "' + node.get('category', "") + '",\n')

  pos_x = zero(-node.location[0])
  pos_y = zero(node.location[2])
  pos_z = zero(node.location[1])
  rot_x = zero(-node.rotation_euler[0])
  rot_y = zero(node.rotation_euler[1])
  rot_z = zero(node.rotation_euler[2])

  file_out.write(spc(indent+2) + '"position": [' + truncate(pos_x) + ',' + truncate(pos_y) + "," + truncate(pos_z) + '],\n')
  file_out.write(spc(indent+2) + '"rotation": [' + truncate(rot_x) + ',' + truncate(rot_y) + ',' + truncate(rot_z) + '],\n')

  stub_scale = True
  if node.type == "EMPTY":
    file_out.write(spc(indent+2) + '"scale": ' + truncate(node.empty_draw_size/2) + '\n')
    write_collision(node, indent+2, file_out)
    stub_scale = False
  if node.type == "MESH":
    file_out.write(spc(indent+2) + '"scale": ' + truncate(node.scale[0]) + ',\n')
    write_mesh(node, indent+2, file_out)
    stub_scale = False
  if stub_scale:
    file_out.write(spc(indent+2) + '"scale": 1.0' + '\n')

  end_comma = '' if last else ","
  file_out.write(spc(indent+1) + '}'+end_comma+'\n')

def writearm(node, indent, file_out, last):
  print(spc(indent), node.name, node.type)

  file_out.write(spc(indent+1) + '"'+ node.name + '":{\n')
  file_out.write(spc(indent+2) + '"type": "' + node.type + '",\n')
  file_out.write(spc(indent+2) + '"class": "' + node.get('class', "") + '",\n')
  file_out.write(spc(indent+2) + '"category": "' + node.get('category', "") + '",\n')

  pos_x = zero(-node.location[0])
  pos_y = zero(node.location[2])
  pos_z = zero(node.location[1])
  rot_x = zero(-node.rotation_euler[0])
  rot_y = zero(node.rotation_euler[1])
  rot_z = zero(node.rotation_euler[2])

  file_out.write(spc(indent+2) + '"position": [' + truncate(pos_x) + ',' + truncate(pos_y) + "," + truncate(pos_z) + '],\n')
  file_out.write(spc(indent+2) + '"rotation": [' + truncate(rot_x) + ',' + truncate(rot_y) + ',' + truncate(rot_z) + '],\n')

  stub_scale = True

  write_arm(node, indent+2, file_out)

  end_comma = '' if last else ","
  file_out.write(spc(indent+1) + '}'+end_comma+'\n')


# http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
def find_tangent(temp_node, vert, faceNum):
  face = temp_node.faces[faceNum]
  dco1 = temp_node.verts[face.verts[1]].co - temp_node.verts[face.verts[0]].co
  dco2 = temp_node.verts[face.verts[2]].co - temp_node.verts[face.verts[0]].co

  try:
    tempUV0 = temp_node.data.uv_layers.active.data[face.loop_indices[0]].uv
    tempUV1 = temp_node.data.uv_layers.active.data[face.loop_indices[1]].uv
    tempUV2 = temp_node.data.uv_layers.active.data[face.loop_indices[2]].uv
  except:
    tempUV0 = Vector((0.0, 0.0))
    tempUV1 = Vector((1.0, 0.0))
    tempUV2 = Vector((0.0, 0.0))

  duv1 = tempUV1 - tempUV0
  duv2 = tempUV2 - tempUV0

  tangent = dco2*duv1.y - dco1*duv2.y
  bitangent = dco2*duv1.x - dco1*duv2.x

  # Handle Mirrored UVs
  # TODO: Turn on (flip currently does nothing)
  flip = False
  if dco2.cross(dco1).dot(bitangent.cross(tangent)) > 0:
    flip = True

  vert_tangent = mathutils.Vector((0,0,0,1))

  for a in range(0,3):
    if face.vertices[a] == vert:
      verNor = temp_node.data.vertices[face.vertices[a]].normal
      temp_tangent = tangent - verNor*tangent.dot(verNor)
      temp_tangent.normalize()
      vert_tangent =  mathutils.Vector((temp_tangent.x, temp_tangent.y, temp_tangent.z, 1.0))
      if flip:
        vert_tangent = mathutils.Vector((temp_tangent.x, temp_tangent.y, temp_tangent.z, -1.0))
  return vert_tangent


def get_bmesh(in_node):
  context = bpy.context
  dg = context.evaluated_depsgraph_get()
  ob = in_node.copy()
  bm = bmesh.new()
  bm.from_object(ob, dg)
  bmesh.ops.triangulate(bm, faces=bm.faces )
  bpy.data.objects.remove(ob, do_unlink=True)
  return bm

def write_mesh(in_node, indent, file_out):
  temp_node  = get_bmesh(in_node)
  multi_vert = [[]] * len(temp_node.verts)
  face_remap = []
  face_list  = []
  num_tris   = len(temp_node.faces) #TODO: remove
  num_verts  = len(temp_node.verts) #TODO: remove
  dupe_vert_count = 0
  has_vc     = temp_node.loops.layers.color.active is not None
  vc_lay     = temp_node.loops.layers.color.active

  print (spc(indent), "Remapping verts for UVs")

  for face in temp_node.faces:
    for loop in face.loops:
      idx = 0
      uv = loop[temp_node.loops.layers.uv.active].uv
      vv = multi_vert[loop.vert.index][:]
      newUV = [loop.vert.index,
        -loop.vert.co.x,  loop.vert.co.z,loop.vert.co.y,
        uv.x, 1-uv.y,
        -loop.vert.normal.x, loop.vert.normal.z, loop.vert.normal.y]
      if temp_node.loops.layers.color.active is not None:
        vc = loop[vc_lay]
        newUV.extend(vc[:])
      if newUV not in vv:
        vv.append(newUV)
        dupe_vert_count += 1
        idx = len(vv)-1
      else:
        idx = vv.index(newUV)
      face_list.append(loop.vert.index)
      face_remap.append(idx)
      multi_vert[loop.vert.index] = vv

  position_list = []
  uv_list       = []
  normal_list   = []
  color_list    = []
  vcount = 0
  for count, v in enumerate(multi_vert):
    for m in v:
      m.insert(0, vcount)
      position_list.extend(m[2:5])
      uv_list.extend(m[5:7])
      normal_list.extend(m[7:10])
      if has_vc:
        color_list.extend(m[10:13])
      vcount +=1

  position_list = processArray(position_list)
  uv_list       = processArray(uv_list)
  normal_list   = processArray(normal_list)
  color_list    = processArray(color_list)

  # Index New,Original | Position -X,Z,Y | UV U,1-V | Normal -X,Z,Y | vColor R,G,B

  # Vertex Positions
  print (spc(indent), "_vertices")
  file_out.write(spc(indent) + '"vertices":[' + position_list + '],\n')

  # Triangle Indices
  tri_list = ""
  print (spc(indent), "_Indices")
  for count, l in enumerate(face_remap):
    tri_list += (str(multi_vert[face_list[count]][l][0]))
    if count < len(face_remap)-1 : tri_list += ","
  file_out.write(spc(indent) + '"indices":[' + tri_list + '],\n')

  # UVs
  print (spc(indent), "_uvs")
  file_out.write(spc(indent) + '"UV":[' + uv_list + '],\n')

  # Vertex Colors
  if has_vc:
    print (spc(indent), "_Vertex Colors")
    file_out.write(spc(indent) + '"vertexcolors":[' + color_list + '],\n')
  else:
    print('No vertex colors!')

  # Normals
  print(spc(indent), "_normals")
  file_out.write(spc(indent) + '"normals":[' + normal_list + ']\n')

  # Tangents
  # print(spc(indent), "_tangents")
  # file_out.write(spc(indent) + '"tangents":[')
  # tangent_list = []
  # for vert in temp_node.verts:
  #   tangent_list.append(mathutils.Vector((0, 0, 0, 0)))
  #
  # for face in temp_node.faces:
  #   for vCnt in range(0,3):
  #     tmpTan = find_tangent(temp_node, face.verts[vCnt], face.index)
  #     tangent_list[face.verts[vCnt]] = tmpTan
  #
  # #for tangent_counter in tangent_list:
  #   #tangent_counter.normalize()
  #
  # cnt = 0
  # for face in temp_node.faces:
  #   for a in range(0,3):
  #     vert_tangent = tangent_list[face.verts[a]]
  #     vert_tangent = checkZeroXYZ(vert_tangent)
  #
  #     file_out.write(str(vert_tangent.x)[:str_length] + ',' + str(vert_tangent.z)[:str_length] + ',' + str(vert_tangent.y)[:str_length] + ',' + str(vert_tangent.w)[:str_length])
  #     if cnt < num_tris*3-1:
  #       file_out.write(',')
  #     cnt += 1
  # file_out.write('],\n')

  # Weights
  # print(spc(indent), "_weights")
  # file_out.write(spc(indent) + '"weights":{\n')
  # if len(temp_node.vertex_groups) > 0:
  #   file_out.write(spc(indent+1) + '"index": [')
  #   print_comma = False
  #   for face in temp_node.faces:
  #     for vert in face.verts:
  #       if print_comma:
  #         file_out.write(',')
  #       else:
  #         print_comma = True
  #       file_out.write(str(temp_node.verts[vert].index))
  #   file_out.write('],\n')                          # Close index
  #
  #   file_out.write(spc(indent+1) + '"weightlist": [')
  #   first_v = True
  #   for vert in temp_node.verts:
  #     if not first_v:
  #        file_out.write(',')
  #     else:
  #       first_v = False
  #     file_out.write('[')                         # Open vert array
  #     first_g = True
  #     for ver in vert.groups:
  #       if not first_g:
  #          file_out.write(',')
  #       else:
  #         first_g = False
  #       file_out.write('[' + str(ver.group) + "," + str(ver.weight) + ']')
  #     file_out.write(']')                         # Close vert array
  #   file_out.write(']\n')                           # Close weight list
  #
  # file_out.write(spc(indent) + '}' + '\n')                  # Close weights

  # Garbage Collection
  position_list = None
  uv_list       = None
  normal_list   = None
  color_list    = None
  temp_node.free();
  write_collision(in_node, indent, file_out)


def write_arm(in_node, indent, file_out):
  print("wee")

def write_collision(in_node, indent, file_out):
  str_length = 7

  hasCollision = False
  for childCnt in range(len(in_node.children)):
    if in_node.children[childCnt].get('class', "") == "collision": hasCollision = True

  if hasCollision == True:
    print (spc(indent), "_collision")
    file_out.write(',\n' + spc(indent) + '"collision":[\n')
    for childCnt in range(len(in_node.children)):
      if in_node.children[childCnt].get('class', "") == "collision":
        file_out.write(spc(indent+1) + '{\n')
        file_out.write(spc(indent+2) + '"name": "' + in_node.children[childCnt].name + '",\n')
        temp_node = get_bmesh(in_node.children[childCnt])
        num_verts = len(temp_node.data.vertices)
        file_out.write(spc(indent+2) + '"vpos":[')
        print (spc(indent), "_vpos")
        cnt = 0
        for vertex in temp_node.data.vertices:
          # Positions
          v = vertex.co
          v = checkZeroXYZ(v)

          file_out.write('[' + str(v.x)[:str_length] + ',' + str(v.z)[:str_length] + ',' + str(v.y)[:str_length] + ']')
          if cnt < num_verts-1: file_out.write(',')
          cnt = cnt + 1

        file_out.write(']\n')
        file_out.write(spc(indent+1) + '}\n')
        bpy.ops.object.delete()        # Delete temp object
    file_out.write(spc(indent) + ']')


def checkZeroXYZ(inXYZ):
  if (inXYZ.x < 0.0001 and inXYZ.x > -0.0001): inXYZ.x = 0
  if (inXYZ.y < 0.0001 and inXYZ.y > -0.0001): inXYZ.y = 0
  if (inXYZ.z < 0.0001 and inXYZ.z > -0.0001): inXYZ.z = 0
  return inXYZ

def checkZeroXY(inXY):
  if (inXY.x < 0.0001 and inXY.x > -0.0001): inXY.x = 0
  if (inXY.y < 0.0001 and inXY.y > -0.0001): inXY.y = 0
  return inXY

# def checkZeroArray(inArray):
#   for element in inArray:
#     if (element < 0.0001 and element > -0.0001):element = 0
#   return inArray

def checkZeroArray(inArray):
  newArr = []
  for element in inArray:
    if (element < 0.0001 and element > -0.0001):
      newArr.append(0)
    else:
      newArr.append(element)
  return newArr

def menu_func_export(self, context):
  self.layout.operator(ExportGeo.bl_idname, text="LightShade (.geo)")

classes = (
  ExportGeo,
)

def register():
  for cls in classes:
    bpy.utils.register_class(cls)

  bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
  bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

  for cls in classes:
    bpy.utils.unregister_class(cls)

if __name__ == "__main__":
  register()
