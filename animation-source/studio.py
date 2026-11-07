"""Original motion plate for Zhi Jing: studio, instrument, camera and render.
Run: blender -b -P studio.py -- --out frames --start 1 --end 72
"""
import bpy, sys, os, math, argparse
from mathutils import Vector, Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
args=argparse.ArgumentParser()
args.add_argument('--out', required=True)
args.add_argument('--frames',type=int,default=96)
args.add_argument('--start',type=int,default=1)
args.add_argument('--end',type=int,default=96)
args.add_argument('--w',type=int,default=864)
args.add_argument('--h',type=int,default=756)
args.add_argument('--samples',type=int,default=14)
args.add_argument('--device',default='CPU')
args.add_argument('--save')
args.add_argument('--scale',type=float,default=8.0)
args.add_argument('--sample-frames',default='')
args.add_argument('--eye',nargs=3,type=float,default=(5.4,1.3,10.8))
args.add_argument('--roll',type=float,default=42)
args.add_argument('--point',nargs=3,type=float,default=(-.06,-.38,.9))
a=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
scene=bpy.context.scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def material(name, rgb, metal=0., rough=.35):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    return m

def finish(o,name,m,parent=None,bevel=0):
    o.name=name; o.data.materials.append(m)
    if parent:o.parent=parent
    if bevel:
        b=o.modifiers.new('Continuous fillet','BEVEL'); b.width=bevel; b.segments=6; b.harden_normals=True
        n=o.modifiers.new('Face-weighted normals','WEIGHTED_NORMAL'); n.keep_sharp=True
    return o

def block(name, xyz, sizes, m, parent=None, bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz); o=bpy.context.object
    o.dimensions=sizes; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,m,parent,bevel)

def disk(name,xyz,r,depth,m,parent=None,bevel=.012,normal=(0,0,1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=r,depth=depth,location=xyz)
    o=bpy.context.object; o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector(normal).to_track_quat('Z','Y')
    for p in o.data.polygons: p.use_smooth=len(p.vertices)==4
    return finish(o,name,m,parent,bevel)

def area(name, xyz, at, power, size, color, size_y=None):
    dat=bpy.data.lights.new(name,'AREA'); dat.energy=power; dat.shape='RECTANGLE'
    dat.size=size; dat.size_y=size if size_y is None else size_y; dat.color=color
    o=bpy.data.objects.new(name,dat); scene.collection.objects.link(o); o.location=xyz
    o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()

from hand import build_hand
hand_root=build_hand()
# The target is an anodised instrument block. Each of the four faces has the same
# engravings, so a ninety-degree turn ends in precisely the starting appearance.
orange=material('Vermilion | anodised aluminium',(.69,.073,.012),.54,.255)
dark_orange=material('Burnished vermilion',(.37,.033,.009),.73,.285)
rim=material('Polished copper edges',(.78,.26,.065),.82,.205)
track=material('Laser etched channel',(.175,.037,.016),.54,.36)
ink=material('Graphite inlay',(.014,.018,.022),.43,.29)
apricot=material('Vitreous orange marker',(.98,.41,.085),.36,.225)
target=bpy.data.objects.new('01 | Turn specimen',None);scene.collection.objects.link(target)
target.location=(0,.7,1.55)
block('Monolithic soft-square body',(0,0,0),(1.98,1.98,1.92),orange,target,.235)
# Machined annular inset. Use stacked very shallow pieces so they cast fine contact shadows.
disk('Circular tooling rim',(0,0,.958),.631,.016,dark_orange,target,.006)
disk('Crown',(0,0,.969),.592,.016,orange,target,.006)
disk('Crown, scribed centre',(0,0,.978),.224,.012,dark_orange,target,.004)
disk('Crown, spun insert',(0,0,.985),.199,.010,rim,target,.003)
for k in range(4):
    angle=k*math.pi/2
    x,y=.425*math.cos(angle),.425*math.sin(angle)
    part=block('Radial datum', (x,y,.98),(.235,.039,.014),track,target,.009);part.rotation_euler.z=angle+.12
    pos=Vector((math.cos(angle),math.sin(angle),0))
    tangent=Vector((-math.sin(angle),math.cos(angle),0))
    for rail in [-.56,-.41,-.26]:
        pos3=.987*pos+rail*tangent
        part=block('Side grip | milled flute',(*pos3[:2],.01),(.014,.045,.79),dark_orange,target,.006)
        part.rotation_euler.z=angle
    disk('Inset datum',tuple(.986*pos+.45*tangent+Vector((0,0,.32))),.085,.015,track,target,.004,pos)
    disk('Copper insert',tuple(.996*pos+.45*tangent+Vector((0,0,.32))),.062,.011,apricot,target,.003,pos)
# A fine, fourfold-symmetric indexing scale is legible when the block turns.
for k in range(48):
    angle=k*math.tau/48
    r=.546 if k%3 else .536
    length=.034 if k%3 else .055
    mark=block('Crown | etched graduation',(r*math.cos(angle),r*math.sin(angle),.979),
               (length,.012,.007),dark_orange,target,.002)
    mark.rotation_euler.z=angle
# Continuous wrist column exiting the panel, behind the rig's wrist / palm.
cuff=material('Wrist column | titanium',(.33,.37,.42),.83,.29)
rubber=material('Wrist seal',(.02,.026,.028),.25,.39)
block('Wrist stem',(0,-5.25,-.19),(1.7,4.25,.68),cuff,bevel=.28)
for k in range(5):
    block('Bellows',(0,-3.93-k*.125,-.1),(1.98,.092,.79),rubber,bevel=.041)
floor=material('Set | midnight basalt',(.008,.011,.020),.13,.5)
block('Set floor',(0,0,-1.72),(200,200,.14),floor,bevel=0)
world=bpy.data.worlds.new('Studio ambient'); scene.world=world; world.use_nodes=True
back=world.node_tree.nodes.get('Background');back.inputs[0].default_value=(.34,.405,.52,1);back.inputs[1].default_value=.23
area('Key | overhead silk',(-4,1,8),(0,-.4,.45),760,5.8,(1,.927,.842),4.0)
area('Edge | long blade',(4,3.8,5),(0,0,1),900,1.5,(.78,.87,1),6)
area('Fill | camera side',(2,-6,5.5),(0,-1,.9),430,4.5,(1,.98,.96),3.5)
area('Thumb edge',(-5,-2.5,2),(0,-.4,1),150,.9,(.68,.81,1),4)
# Portrait of the instrument: fingers sweep from lower left towards upper right.
point=Vector(a.point); cam=bpy.data.objects.new('Product camera',bpy.data.cameras.new('Orthographic product lens'));scene.collection.objects.link(cam)
cam.location=point+Vector(a.eye)
z=(cam.location-point).normalized(); y=(Vector((0,1,0))-z*Vector((0,1,0)).dot(z)).normalized(); x=y.cross(z).normalized()
cam.rotation_euler=(Matrix((x,y,z)).transposed() @ Matrix.Rotation(math.radians(a.roll),3,'Z')).to_euler()
cam.data.type='ORTHO'; cam.data.ortho_scale=a.scale; scene.camera=cam
scene.render.engine='CYCLES'; scene.cycles.samples=a.samples;scene.cycles.use_denoising=True
scene.cycles.max_bounces=4; scene.cycles.diffuse_bounces=2; scene.cycles.glossy_bounces=3
scene.cycles.transparent_max_bounces=2; scene.cycles.seed=7
if a.device=='METAL':
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL'; prefs.refresh_devices()
    for dev in prefs.devices: dev.use=(dev.type=='METAL')
    if any(dev.use for dev in prefs.devices):scene.cycles.device='GPU'
    print('RENDER DEVICES',[(d.name,d.use) for d in prefs.devices],flush=True)
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=a.w;scene.render.resolution_y=a.h;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=12
scene.render.fps=12;scene.frame_start=1;scene.frame_end=48
scene.render.use_persistent_data=True
out=Path(a.out).resolve();out.mkdir(exist_ok=True,parents=True)
# All parts stay in the moving hand's reference frame. The small roll of the wrist
# accompanies the finger handoff and returns to the exact starting orientation.
wrist=bpy.data.objects.new('Wrist | pronation',None);scene.collection.objects.link(wrist)
wrist.location=(0,-3.65,-.2)
for child in [hand_root,target,*[o for o in scene.objects if o.name.startswith(('Wrist stem','Bellows'))]]:
    child.parent=wrist
    child.location-=wrist.location
for f in range(1,50):
    u=2*math.pi*(f-1)/48
    wrist.rotation_euler=(math.radians(3.4)*(1-math.cos(u)), math.radians(6)*math.sin(u),
                          math.radians(-3.6)*math.sin(u))
    wrist.keyframe_insert(data_path='rotation_euler',frame=f)
# Same easing for the object even if the project is opened later in Blender.
for f in range(1,50):
    t=(f-1)/48
    eased=t-math.sin(2*math.pi*t)/(2*math.pi)
    target.rotation_euler.z=math.pi/2*eased
    target.keyframe_insert(data_path='rotation_euler',frame=f)
if a.save:
    scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.save).resolve()),compress=True)
for frame in ([int(s) for s in a.sample_frames.split(',')] if a.sample_frames else range(a.start,a.end+1)):
    clock=(frame-1)*48/a.frames+1
    scene.frame_set(math.floor(clock),subframe=clock%1)
    scene.render.filepath=str(out/f'{frame:04}.png')
    bpy.ops.render.render(write_still=True)
