#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function


NMAX = int(10e7)
ITT = int(10e7)
OPT_ITT = 1

STP = 1.0e-5
NEARL = 0.0028
H = NEARL*1.2

FARL = 0.03

EXPORT_ITT = 100
STAT_ITT = 1


def random_unit_vec(num, scale):

  from numpy.random import normal
  from numpy.linalg import norm
  from numpy import reshape

  rnd = normal(size=(num,3))
  d = norm(rnd,axis=1)
  rnd[:] /= reshape(d, (num,1))

  return rnd*scale

def load_obj(fn):

  from codecs import open
  from numpy import row_stack

  vertices = []
  faces = []

  with open(fn, 'r', encoding='utf8') as f:

    for l in f:
      if l.startswith('#'):
        continue

      values = l.split()
      if not values:
        continue
      if values[0] == 'v':
        vertices.append([float(v) for v in values[1:]])

      if values[0] == 'f':
        faces.append([int(v)-1 for v in values[1:]])

  np_vertices = row_stack(vertices)

  xmax = np_vertices[:,0].max()
  xmin = np_vertices[:,0].min()
  ymax = np_vertices[:,1].max()
  ymin = np_vertices[:,1].min()
  zmax = np_vertices[:,2].max()
  zmin = np_vertices[:,2].min()
  dx = xmax - xmin
  dy = ymax - ymin
  dz = zmax - zmin

  print('original')
  print('x min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(xmin,xmax,dx))
  print('y min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(ymin,ymax,dy))
  print('z min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(zmin,zmax,dz))

  np_vertices /= max([dx,dy,dz])
  np_vertices *= 0.02
  np_vertices += 0.5

  xmax = np_vertices[:,0].max()
  xmin = np_vertices[:,0].min()
  ymax = np_vertices[:,1].max()
  ymin = np_vertices[:,1].min()
  zmax = np_vertices[:,2].max()
  zmin = np_vertices[:,2].min()
  dx = xmax - xmin
  dy = ymax - ymin
  dz = zmax - zmin

  print('rescaled')
  print('x min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(xmin,xmax,dx))
  print('y min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(ymin,ymax,dy))
  print('z min max, {:0.8f} {:0.8f}, dst: {:0.8f}'.format(zmin,zmax,dz))

  return {
    'faces': faces,
    'vertices': [list(row) for row in np_vertices]
  }

def export_obj(dm,obj_name,fn):

  from numpy import zeros
  from codecs import open

  np_verts = zeros((NMAX,3),'float')
  np_tris = zeros((NMAX,3),'int')

  vnum = dm.np_get_vertices(np_verts)
  tnum = dm.np_get_triangles_vertices(np_tris)

  print('storing mesh ...')
  print('num vertices: {:d}, num triangles: {:d}'.format(vnum, tnum))

  with open(fn, 'wb', encoding='utf8') as f:

    f.write('o {:s}\n'.format(obj_name))

    for v in np_verts[:vnum,:]:
      f.write('v {:f} {:f} {:f}\n'.format(*v))

    f.write('s off\n')

    for t in np_tris[:tnum,:]:
      t += 1
      f.write('f {:d} {:d} {:d}\n'.format(*t))

    print('done.')


def main(argv):

  from differentialMesh3d import DifferentialMesh3d
  from time import time
  from modules.helpers import print_stats
  from numpy import unique
  from numpy.random import random

  name = argv[0]
  fn_obj = './data/base.obj'
  fn_out = './res/{:s}'.format(name)

  DM = DifferentialMesh3d(NMAX, FARL, NEARL, FARL)

  data = load_obj(fn_obj)
  DM.initiate_faces(data['vertices'], data['faces'])

  noise = random_unit_vec(DM.get_vnum(), STP*4)
  DM.position_noise(noise, scale_intensity=-1)

  DM.optimize_edges(H, STP)

  for he in xrange(DM.get_henum()):
    DM.set_edge_intensity(he, 1.0)

  for i in xrange(ITT):

    try:

      t1 = time()

      blocked = DM.optimize_position(STP, OPT_ITT, scale_intensity=1)
      # print('blocked: {:d}'.format(blocked))

      # vnum = DM.get_vnum()

      DM.optimize_edges(H, STP)
      if i%50==0:
        for he in unique((random(DM.get_henum())<0.01).nonzero()[0]):
          DM.add_edge_intensity(he, 1.0)

      DM.diminish_all_vertex_intensity(0.99)
      DM.smooth_intensity()

      if i%STAT_ITT==0:
        print_stats(i, time()-t1, DM)

      if i%EXPORT_ITT==0:
        fn = '{:s}_{:06d}.obj'.format(fn_out, i)
        export_obj(DM, 'thing_mesh', fn)

    except KeyboardInterrupt:

      break


if __name__ == '__main__' :

  import sys

  argv = sys.argv

  if False:

    import pstats, cProfile
    fn = './profile/profile'
    cProfile.run('main(argv[1:])',fn)
    p = pstats.Stats(fn)
    p.strip_dirs().sort_stats('cumulative').print_stats()

  else:

    main(argv[1:])

