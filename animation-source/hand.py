"""Five-finger hand for the in-hand rotation study. World +Z is palm-side."""
import math
from functools import lru_cache
import bpy
from mathutils import Matrix, Vector

TAU = math.tau
V = Vector


def material(name, color, metal=0.0, rough=.36, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    for key, value in (('Base Color', (*color, 1)), ('Metallic', metal),
                       ('Roughness', rough), ('Coat Weight', coat)):
        if key in bs.inputs:
            bs.inputs[key].default_value = value
    mat.diffuse_color = (*color, 1)
    return mat


def link_obj(name, data, parent=None):
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def mesh_obj(name, rings, mat, parent, flip=False):
    n = len(rings[0])
    faces = [tuple(range(n - 1, -1, -1))]
    for i in range(len(rings)-1):
        for j in range(n):
            k = (j + 1) % n
            faces.append((i*n+j, i*n+k, (i+1)*n+k, (i+1)*n+j))
    end = (len(rings)-1)*n
    faces.append(tuple(end+i for i in range(n)))
    if flip:
        faces = [tuple(reversed(face)) for face in faces]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for ring in rings for v in ring], [], faces)
    mesh.materials.append(mat)
    mesh.update()
    for poly in mesh.polygons[1:-1]:
        poly.use_smooth = True
    return link_obj(name, mesh, parent)


def signpow(x, p):
    return math.copysign(abs(x)**p, x)


def finger_loft(name, sections, mat, parent, count=32):
    """Rings are (station, halfwidth, halfdepth, z-center, x-center)."""
    rings = []
    for y, w, d, z, x in sections:
        ring = []
        for j in range(count):
            a = -TAU*j/count
            ring.append((x+w*signpow(math.cos(a), .7), y, z+d*signpow(math.sin(a),.72)))
        rings.append(ring)
    return mesh_obj(name, rings, mat, parent)


def catmull(points, resolution=4):
    curve = []
    corners = [V((*p, 0)) for p in points]
    for i, b in enumerate(corners):
        a, c, d = corners[i-1], corners[(i+1)%len(corners)], corners[(i+2)%len(corners)]
        for j in range(resolution):
            t = j/resolution
            curve.append((2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t*t
                          +(-a+3*b-3*c+d)*t*t*t)*.5)
    return curve


def palm_plate(name, outline, low, high, mat, root, lift=None):
    curve = catmull(outline)
    area = sum(curve[i-1].x*p.y - p.x*curve[i-1].y for i,p in enumerate(curve))
    if area < 0:
        curve.reverse()
    normals=[]
    for i,p in enumerate(curve):
        tangent=(curve[(i+1)%len(curve)]-curve[i-1]).normalized()
        normals.append(V((-tangent.y,tangent.x,0)))
    # A constant 2D inset gives each perimeter a machined fillet. The final two
    # coplanar rings terminate the fillet so planar caps keep planar reflections.
    r=min(.052,(high-low)*.32)
    bevel=[(r+.017,low),(r,low)]
    for j in range(1,6):
        theta=math.pi*j/10
        bevel.append((r-r*math.sin(theta),low+r-r*math.cos(theta)))
    bevel.append((0,high-r))
    for j in range(1,6):
        theta=math.pi*j/10
        bevel.append((r-r*math.cos(theta),high-r+r*math.sin(theta)))
    bevel.append((r+.02,high))
    rings = []
    for inset,z in bevel:
        ring=[]
        for p,n in zip(curve,normals):
            q=p+inset*n
            ring.append((q.x,q.y,z+(lift(q.x,q.y) if lift else 0)))
        rings.append(ring)
    return mesh_obj(name,rings,mat,root)


def contact_treads(name, outline, heights, mat, parent, z):
    # Parallel, softly terminated channels cut across the local pad contour.
    shape=catmull(outline,6)
    for h in heights:
        ends=[]
        for i,b in enumerate(shape):
            a=shape[i-1]
            va=a.y-.35*a.x-h
            vb=b.y-.35*b.x-h
            if va*vb < 0:
                ends.append(a+(b-a)*va/(va-vb))
        if len(ends)!=2:
            continue
        ends.sort(key=lambda p:p.x)
        a,b=ends
        axis=(b-a).normalized()
        if (b-a).length < .23:
            continue
        a+=.065*axis
        b-=.065*axis
        curve_line(name,[(a.x,a.y,z),((a.x+b.x)*.5,(a.y+b.y)*.5,z),
                         (b.x,b.y,z)],.010,mat,parent)


def axis_part(name, start, end, profile, mat, parent, sides=36):
    """Surface of revolution between two arbitrary positions."""
    a, b = V(start), V(end)
    axis = (b-a).normalized()
    other = V((0,1,0)) if abs(axis.y) < .85 else V((1,0,0))
    u = axis.cross(other).normalized()
    v = axis.cross(u)
    rings = [[a+(b-a)*t + r*(math.cos(TAU*j/sides)*u+math.sin(TAU*j/sides)*v)
              for j in range(sides)] for t,r in profile]
    return mesh_obj(name,rings,mat,parent)


def curve_line(name, points, r, mat, parent):
    curve = bpy.data.curves.new(name,'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 10
    curve.bevel_depth = r
    curve.bevel_resolution = 2
    curve.use_fill_caps = True
    path = curve.splines.new('BEZIER')
    path.bezier_points.add(len(points)-1)
    for p, co in zip(path.bezier_points,points):
        p.co = co
        p.handle_left_type = p.handle_right_type = 'AUTO'
    curve.materials.append(mat)
    return link_obj(name,curve,parent)


def hinge(name, w, radius, mat, parent):
    axle_half = w*.95
    start, end = (-axle_half,0,0),(axle_half,0,0)
    axis_part(name+' · elastomer gasket',start,end,
              [(0,radius*.82),(.05,radius),(.95,radius),(1,radius*.82)],mat['black'],parent)
    for s in (-1,1):
        # Offset shell hardware on both faces of the axis; hex socket catches the rim light.
        x = s*axle_half
        axis_part(name+' · retainer',(x,0,0),(x+s*.035,0,0),
                  [(0,.77*radius),(.65,.77*radius),(1,.66*radius)],mat['steel'],parent)
        axis_part(name+' · socket',(x+s*.035,0,0),(x+s*.038,0,0),
                  [(0,.27*radius),(1,.25*radius)],mat['black'],parent,6)


TIP_SHELL = [( .02,.63,.50),(.09,.86,.71),(.22,1.01,.84),(.42,1,.86),
             (.67,.92,.82),(.83,.79,.75),(.94,.57,.54),(.989,.28,.29),(1,.075,.08)]
TIP_PAD = [(.24,.24,.02,.76),(.30,.53,.085,.77),(.41,.70,.14,.80),(.63,.71,.16,.75),
           (.78,.62,.15,.66),(.88,.41,.10,.57),(.93,.21,.035,.45)]


def segment(name, length, width, typ, mat, parent):
    w = width/2
    fingertip = typ == 2
    base = .04 if typ else .02
    # A slender structural spar is visible between the armor and the hinge.
    finger_loft(name+' · link',[(0,w*.67,w*.53,0,0),(.10*length,w*.82,w*.66,0,0),
              (.78*length,w*.62,w*.54,-.012,0),(length,w*.56,w*.47,-.01,0)],
              mat['metal'],parent)
    if fingertip:
        sections = TIP_SHELL
    else:
        sections = [(base,.57,.50),(.085,.79,.68),(.18,.97,.83),(.34,1,.88),
                    (.57,.94,.85),(.73,.82,.77),(.83,.73,.68),(.92,.62,.58),(.96,.53,.42)]
    finger_loft(name+' · ceramic shell',[(t*length,w*a,w*b,-.018,0) for t,a,b in sections],
                mat['pearl'],parent)
    # Palmar side tactile insert: low profile and flush edge, broadest on the distal phalanx.
    if fingertip:
        padrows = TIP_PAD
    else:
        padrows=[(.25,.18,.02,.73),(.31,.47,.07,.79),(.42,.58,.12,.79),
                 (.62,.54,.12,.73),(.73,.44,.075,.65),(.78,.2,.025,.60)]
    finger_loft(name+' · tactile insert',[(length*t,w*a,w*b,w*z-.01,0) for t,a,b,z in padrows],
                mat['pad'],parent,24)
    if fingertip:
        for k in range(3):
            yy = (.46+k*.081)*length
            zz = w*(.91-k*.018)-.009
            curve_line(name+' · tactile rib', [(-w*.45,yy-.018,zz-.016),
                (0,yy,zz+.003),(w*.45,yy-.018,zz-.016)],.009,mat['rubber'],parent)
    # A thin parting groove subtly describes the ceramic cover's section.
    t0,a0,b0=sections[2]
    lip=[]
    for k in range(24):
        phi=TAU*k/23
        lip.append((w*a0*1.005*signpow(math.cos(phi),.7), t0*length,
                    w*b0*1.005*signpow(math.sin(phi),.72)-.018))
    curve_line(name+' · cover parting line',lip,.007,mat['etch'],parent)
    if not fingertip:
        # Fine, longitudinal flutes on the lateral shoulders remain visible in profile.
        for side in (-1,1):
            theta=.45
            edge=[]
            for t0,a0,b0 in sections[3:6]:
                edge.append((side*w*a0*1.006*math.cos(theta)**.7,t0*length,
                            -.018+w*b0*1.006*math.sin(theta)**.72))
            curve_line(name+' · shell flute',edge,.011,mat['silver'],parent)
    hinge(name,w,w*(.64 if typ else .76),mat,parent)


def palm_assembly(mat, root):
    perimeter=[(-.80,-3.53),(.66,-3.48),(1.11,-3.08),(1.46,-2.47),
               (1.68,-1.49),(1.64,-.75),(1.56,-.35),(1.33,-.11),
               (.48,.12),(-.46,.20),(-1.33,.035),(-1.62,-.32),
               (-1.68,-1.11),(-1.59,-2.26),(-1.24,-2.91)]
    palm_plate('Palm · carbon chassis',perimeter,-.37,.09,mat['black'],root)
    # Duplicated silhouette creates a continuous precision-machined waistline.
    narrow=[(x*.976,(y+1.58)*.984-1.58) for x,y in perimeter]
    palm_plate('Palm · titanium perimeter',narrow,-.31,-.12,mat['steel'],root)
    pearl_side=[(-.70,-3.38),(.48,-3.32),(.83,-3.10),(.91,-2.84),(.62,-2.62),
                (.16,-2.30),(-.22,-1.69),(-.38,-1.17),(-.69,-.84),(-1.20,-.70),
                (-1.43,-.88),(-1.50,-1.37),(-1.42,-2.22),(-1.10,-2.99)]
    far_side=[(.76,-2.67),(1.09,-2.71),(1.36,-2.25),(1.52,-1.57),(1.51,-.87),
              (1.40,-.52),(.93,-.55),(.50,-.78),(.19,-1.21),(.03,-1.79),
              (.16,-2.12),(.40,-2.36)]
    knuckle=[(-1.47,-.60),(-1.46,-.20),(-1.20,-.07),(-.42,.09),(.41,.04),
             (1.20,-.15),(1.42,-.37),(1.37,-.48),(.92,-.48),(.50,-.63),
             (.12,-.92),(-.12,-1.24),(-.25,-1.44),(-.38,-1.07),(-.63,-.79),
             (-.98,-.65)]
    palm_plate('Palm · thenar armor',pearl_side,.035,.245,mat['pearl'],root)
    palm_plate('Palm · hypothenar armor',far_side,.035,.21,mat['pearl'],root)
    palm_plate('Palm · metacarpal bridge',knuckle,.045,.19,mat['silver'],root)
    # A removable central panel follows the load path from the wrist to the finger bridge.
    insert=[(-.40,-2.55),(-.29,-2.16),(-.43,-1.77),(-.70,-1.38),
            (-1.00,-1.15),(-1.23,-1.18),(-1.27,-1.49),(-1.14,-1.99),(-.91,-2.37),(-.63,-2.58)]
    palm_plate('Palm · thenar contact pad',insert,.243,.294,mat['pad'],root)
    contact_treads('Palm · traction groove',insert,[-2.28+i*.115 for i in range(13)],mat['rubber'],root,.293)
    # Laser-marked personal monogram at the heel of the hand.
    for x in (-.36,-.22):
        curve_line('井 · engraved stroke',[(x,-3.10,.246),(x+.015,-2.78,.246)],.012,mat['etch'],root)
    for y in (-3.00,-2.87):
        curve_line('井 · engraved stroke',[(-.45,y,.246),(-.13,y,.246)],.012,mat['etch'],root)
    for x,y,z in [(1.25,-1.72,.209),(-1.20,-.40,.190),(.53,-.27,.190),(-.78,-2.78,.245)]:
        axis_part('Palm · countersunk fastener',(x,y,z),(x,y,z+.018),
                  [(0,.053),(.65,.053),(1,.044)],mat['steel'],root)
        axis_part('Palm · fastener inset',(x,y,z+.018),(x,y,z+.020),
                  [(0,.022),(1,.022)],mat['black'],root,6)
    # Short concentric cuff stack. The forearm continues beyond the bottom crop.
    sections=[(-5.15,.75,.53,-.13,0),(-4.92,.77,.52,-.13,0),
              (-4.25,.84,.56,-.11,0),(-3.89,.90,.55,-.10,0),(-3.77,.87,.51,-.10,0)]
    finger_loft('Wrist · forearm shell',sections,mat['pearl'],root)
    for y,w,d,l,m in [(-3.88,.92,.57,.13,'steel'),(-3.74,.83,.46,.35,'black'),(-3.43,.88,.48,.14,'metal')]:
        finger_loft('Wrist · coupling',[(y,w*.93,d*.93,-.09,0),(y+.03,w,d,-.09,0),
                    (y+l-.03,w,d,-.09,0),(y+l,w*.93,d*.93,-.09,0)],mat[m],root)


def _basis(direction, lateral):
    yy = direction.normalized()
    xx = lateral-yy*lateral.dot(yy)
    xx.normalize()
    zz = xx.cross(yy)
    return Matrix((xx, yy, zz)).transposed().to_quaternion()


# Root point, knuckle direction, phalanx lengths/widths, contact polar angle,
# contact height, gait phase, and spread of the thrust arc. Angles are degrees.
DIGITS = (
    ('Index',(-1.22,-.00,.04),(-.45,1.51,.36),(1.62,1.18,.87),(.72,.61,.55),137,1.85,.08,14),
    ('Middle',(-.42,.15,.04),(-.12,1.84,.02),(1.87,1.27,.91),(.74,.62,.55),101,1.82,.22,12),
    ('Ring',(.43,.085,.04),(.15,1.69,.07),(1.71,1.15,.83),(.69,.58,.52),67,1.68,.56,13),
    ('Little',(1.21,-.15,.00),(.68,1.11,.31),(1.34,.95,.72),(.61,.50,.46),22,1.45,.68,15),
    ('Thumb',(-1.19,-1.68,.02),(-1.06,.77,.41),(1.38,1.26,1.00),(.89,.75,.65),204,1.51,.88,16),
)


@lru_cache(maxsize=10)
def _tip_samples(length,width):
    w=width*.5
    profiles=[(t,a,b,-.018) for t,a,b in TIP_SHELL]
    profiles += [(t,a,b,w*z-.01) for t,a,b,z in TIP_PAD]
    return tuple(V((w*a*signpow(math.cos(phi),.7),t*length,
                    offset+w*b*signpow(math.sin(phi),.72)))
                 for t,a,b,offset in profiles for phi in [TAU*n/16 for n in range(16)])


def _specimen_distance(dip,tip,lateral,cube_angle,samples):
    # Distance to the rounded metal surface, measured at physical shell/pad locations.
    rotation=_basis(tip-dip,lateral)
    co,si=math.cos(cube_angle),math.sin(cube_angle)
    nearest=float('inf')
    for local in samples:
        px,py,pz=dip + rotation @ local
        py-=.7
        x=abs(px*co+py*si)-.755
        y=abs(-px*si+py*co)-.755
        z=abs(pz-1.55)-.725
        d=math.sqrt(max(0,x)**2+max(0,y)**2+max(0,z)**2) + min(0,max(x,y,z)) - .235
        nearest=min(nearest,d)
    return nearest


def finger_pose(spec, t):
    name, origin, first, lengths, widths, angle, height, offset, excursion = spec
    a,b,c = lengths
    cycle = (t-offset)%1
    # Slow advancing contact and a quicker retreat behind the next corner.
    wave=math.sin(TAU*cycle)
    release=(max(0.,-math.cos(TAU*cycle))**2)
    az=math.radians(angle+excursion*wave)
    radial=V((math.cos(az),math.sin(az),0))
    tangent=V((radial.y,-radial.x,0))
    cube_angle=(t-math.sin(TAU*t)/TAU)*math.pi*.5
    local=az-cube_angle
    edge=1.0/max(abs(math.cos(local)),abs(math.sin(local)))
    # Rounded corners cut back from the square by a small radius.
    edge -= .13*max(0,(edge-1.)/.414)**2
    root=V(origin)
    contact_center=V((0,.7,height + .10*wave + .08*release))
    first_vec=V(first)+radial*(.13*release)+tangent*(.12*wave)
    first_vec.z+=.19*release+.075*wave
    pip=root + a*first_vec.normalized()
    desired_gap=.003 + .32*release
    distance=edge + widths[2]*.23 + desired_gap
    outward=radial+V((0,0,-.20))
    samples=_tip_samples(c,widths[2])
    for step in range(4):
        target=contact_center+radial*distance
        axis=(target-pip).normalized()
        reach=min(max((target-pip).length,abs(b-c)+.001),b+c-.003)
        target=pip+axis*reach
        bend=(outward-axis*outward.dot(axis)).normalized()
        along=(b*b-c*c+reach*reach)/(2.*reach)
        dip=pip+axis*along+bend*math.sqrt(max(0,b*b-along*along))
        actual_gap=_specimen_distance(dip,target,tangent,cube_angle,samples)
        error=desired_gap-actual_gap
        if abs(error)<.003:
            break
        distance+=min(.12,max(-.12,1.09*error))
    return [root,pip,dip,target],tangent


def build_hand():
    mats={
      'pearl':material('Hand | pearl ceramic',(.72,.76,.78),.31,.26,.28),
      'silver':material('Hand | satin titanium',(.38,.42,.46),.82,.31,.15),
      'metal':material('Hand | graphite titanium',(.145,.165,.19),.82,.27,.1),
      'steel':material('Hand | turned steel',(.48,.55,.61),.91,.20,.15),
      'black':material('Hand | carbon joint',(.027,.034,.045),.47,.31,.08),
      'pad':material('Hand | tactile elastomer',(.078,.090,.104),.10,.53),
      'rubber':material('Hand | pad relief',(.108,.125,.138),.12,.52),
      'etch':material('Hand | etched graphite',(.14,.17,.18),.48,.36),
    }
    root = link_obj('Hand · wrist datum', None)
    palm_assembly(mats,root)
    for spec in DIGITS:
        name,origin,first,lengths,widths,*rest=spec
        links=[]
        for j,(length,width) in enumerate(zip(lengths,widths)):
            prt=link_obj(name+' · phalanx '+str(j+1),None,root)
            prt.rotation_mode='QUATERNION'
            segment(name+' '+str(j+1),length,width,j,mats,prt)
            links.append(prt)
        last_quat=[None]*3
        for frame in range(1,50):
            points,lateral=finger_pose(spec,(frame-1)/48)
            for j,prt in enumerate(links):
                q=_basis(points[j+1]-points[j],lateral)
                if last_quat[j] is not None:
                    q.make_compatible(last_quat[j])
                last_quat[j]=q.copy()
                prt.location=points[j]
                prt.rotation_quaternion=q
                prt.keyframe_insert(data_path='location',frame=frame)
                prt.keyframe_insert(data_path='rotation_quaternion',frame=frame)
    bpy.context.scene.frame_set(1)
    return root
