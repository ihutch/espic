# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import math
import numpy as np
import matplotlib
matplotlib.use('Qt4Agg') # GUI backend
import matplotlib.pyplot as plt
import IPython.core.display as IPdisp

# <codecell>

%load_ext cythonmagic

# <codecell>

z_min = -25.
z_max = 25.
n_cells = 100
n_points = n_cells+1
dz = (z_max-z_min)/(n_points-1)
print 'dz =', dz
eps = 1e-4
grid = np.arange(z_min,z_max+eps,dz,dtype=np.float32)

# <codecell>

extra_storage_factor = 1.2
ion_seed = 384
np.random.seed(ion_seed)
n_ions = 10000
largest_ion_index = [n_ions-1]
ion_storage_length = int(extra_storage_factor*n_ions)
ions = np.zeros([2,ion_storage_length],dtype=np.float32)
ions[0][0:n_ions] = np.random.rand(n_ions)*(z_max-z_min) + z_min # positions
v_th_i = 1
v_d_i = 0
ions[1][0:n_ions] = np.random.randn(n_ions)*v_th_i + v_d_i # velocities
#ions[2][0:n_ions] = np.ones(n_ions,dtype=np.float32) # relative weights

# List remaining slots in reverse order to prevent memory fragmentation
empty_ion_slots = -np.ones(ion_storage_length,dtype=np.int)
current_empty_ion_slot = [(ion_storage_length-n_ions)-1]
empty_ion_slots[0:(current_empty_ion_slot[0]+1)] = range(ion_storage_length-1,n_ions-1,-1)

fig, axes = plt.subplots(nrows=1,ncols=2,figsize=(8,2))
for ax, data in zip(axes,ions):
    n_bins = n_points;
    ax.hist(data[0:n_ions],bins=n_bins, histtype='step')
filename='data.png'
plt.savefig(filename)
IPdisp.Image(filename=filename)

# <codecell>

electron_seed = ion_seed+523
np.random.seed(electron_seed)
mass_ratio = 1./1836.
n_electrons = n_ions
largest_electron_index = [n_electrons-1]
electron_storage_length = int(n_electrons*extra_storage_factor)
electrons = np.zeros([2,electron_storage_length],dtype=np.float32)
electrons[0][0:n_electrons] = np.random.rand(n_electrons)*(z_max-z_min) + z_min # positions
v_th_e = 1./math.sqrt(mass_ratio)
v_d_e = 0
electrons[1][0:n_electrons] = np.random.randn(n_electrons)*v_th_e + v_d_e # velocities
#electrons[2][0:n_electrons] = np.ones(n_ions,dtype=np.float32) # relative weights

# List remaining slots in reverse order to prevent memory fragmentation
empty_electron_slots = -np.ones(electron_storage_length,dtype=np.int)
current_empty_electron_slot = [(electron_storage_length-n_electrons)-1]
empty_electron_slots[0:(current_empty_electron_slot[0]+1)] = range(electron_storage_length-1,n_electrons-1,-1)

fig, axes = plt.subplots(nrows=1,ncols=2,figsize=(8,2))
for ax, data in zip(axes,electrons):
    n_bins = n_points;
    ax.hist(data[0:n_electrons],bins=n_bins, histtype='step')
filename='data.png'
plt.savefig(filename)
IPdisp.Image(filename=filename)

# <codecell>

def move_particles(grid, potential, dt, charge_to_mass, largest_index, particles, density,\
		       empty_slots, current_empty_slot, update_position=True):
    if (update_position and (len(empty_slots)<1 or current_empty_slot[0]<0)):
	print 'move_particles needs list of empty particle slots'
    n_points = len(grid)
    z_min = grid[0]
    z_max = grid[n_points-1]
    dz = grid[1]-grid[0]
    for j in range(n_points):
	density[j] = 0
    for i in range(largest_index[0]):
	within_bounds = (particles[0,i]>z_min and particles[0,i]<z_max)
	if (within_bounds):
	    left_index = (particles[0,i]-z_min)/dz
	    electric_field = (potential[left_index+1]-potential[left_index])/dz
	    accel = charge_to_mass*electric_field
	    particles[1,i] += accel*dt
	    if (update_position):
		particles[0,i] += particles[1,i]*dt
		within_bounds = (particles[0,i]>z_min and particles[0,i]<z_max)
		if not within_bounds:
		    empty_slots[current_empty_slot[0]] = i
		    current_empty_slot[0] += 1
	if (within_bounds):
	    left_index = (particles[0,i]-z_min)/dz
	    fraction_to_left = particles[0,i] % dz
	    density[left_index] += fraction_to_left
	    density[left_index+1] += (1-fraction_to_left)

def accumulate_density(grid, largest_index,  particles, density):
    potential = np.zeros_like(grid)
    move_particles(grid, potential, 0, 1, largest_index, particles, density, [], [-1], update_position=False)

def initialize_mover(grid, potential, dt, chage_to_mass, largest_index, particles):
    density = np.zeros_like(grid)
    move_particles(grid, potential, -dt/2, chage_to_mass, largest_index, \
		       particles, density, [], [-1], update_position=False)

def draw_positive_velocities(n_draw,v_th,v_d=0):
    if (v_d!=0):
	print 'drift not implemented'
    return v_th*np.sqrt(-np.log(np.random.rand(n_draw))*2)

#def draw_negative_velocities(n_draw,v_th,v_d=0):
#    return -draw_positive_velocities(n_draw,v_th,v_d)

def inject_particles(n_inject, grid, dt, v_th, particles, empty_slots, current_empty_slot, largest_index):
    n_points = len(grid)
    z_min = grid[0]
    z_max = grid[n_points-1]
    dz = grid[1]-grid[0]
    partial_dt = dt*np.random.rand(n_inject)
    velocity_sign = np.sign(np.random.rand(n_inject)-0.5)
    positive_velocities = draw_positive_velocities(n_inject,v_th)
    for l in range(n_inject):
	if current_empty_slot[0]<0:
	    print 'no empty slots'
	i = empty_slots[current_empty_slot[0]]
	particles[1,i] = velocity_sign[l]*positive_velocities[l]
	if (velocity_sign[l]<0):
	    particles[0,i] = z_max + partial_dt[l]*particles[1,i]
	else:
	    particles[0,i] = z_min + partial_dt[l]*particles[1,i]
	if (empty_slots[current_empty_slot[0]]>largest_index[0]):
	    largest_index[0] = empty_slots[current_empty_slot[0]]
	empty_slots[current_empty_slot[0]] = -1
	current_empty_slot[0] -= 1

# <codecell>

ion_density = np.zeros_like(grid)
accumulate_density(grid, largest_ion_index, ions, ion_density)
electron_density = np.zeros_like(grid)
accumulate_density(grid, largest_electron_index, electrons, electron_density)
potential = np.zeros_like(grid)
dt = 0.1/v_th_e*10
ion_charge_to_mass = 1
initialize_mover(grid, potential, dt, ion_charge_to_mass, largest_ion_index, ions)
electron_charge_to_mass = -1/mass_ratio
initialize_mover(grid, potential, dt, electron_charge_to_mass, largest_electron_index, electrons)

# <codecell>

n_steps = 50
#injection_seed = 8734
#np.random.seed(injection_seed)
for k in range(n_steps):
    move_particles(grid, potential, dt, ion_charge_to_mass, largest_ion_index, ions, ion_density, \
		       empty_ion_slots, current_empty_ion_slot)
    move_particles(grid, potential, dt, electron_charge_to_mass, largest_electron_index, electrons, electron_density, \
		       empty_electron_slots, current_empty_electron_slot)
    expected_ion_injection = 2*dt*v_th_i/math.sqrt(2*math.pi)*n_ions/(z_max-z_min)
    n_ions_inject = int(expected_ion_injection)
    expected_electron_injection = 2*dt*v_th_e/math.sqrt(2*math.pi)*n_electrons/(z_max-z_min)
    n_electrons_inject = int(expected_electron_injection)
    # If expected injection number is small, need to add randomness to get right average rate
    if (expected_ion_injection-n_ions_inject)>np.random.rand():
	n_ions_inject += 1
    if (expected_ion_injection-n_electrons_inject)>np.random.rand():
	n_electrons_inject += 1
    print current_empty_ion_slot, current_empty_electron_slot, n_ions_inject, n_electrons_inject
    inject_particles(n_ions_inject, grid, dt, v_th_i, ions, empty_ion_slots, current_empty_ion_slot, largest_ion_index)
    inject_particles(n_electrons_inject, grid, dt, v_th_e, electrons, empty_electron_slots, \
			 current_empty_electron_slot, largest_electron_index)
    print current_empty_ion_slot, current_empty_electron_slot, largest_ion_index, largest_electron_index
fig, axes = plt.subplots(nrows=1,ncols=2,figsize=(8,2))
fig, axes = plt.subplots(nrows=1,ncols=2,figsize=(8,2))
for ax, data in zip(axes,electrons):
    n_bins = n_points;
    occupied_slots = (data==data)
    occupied_slots[empty_electron_slots[0:current_empty_electron_slot[0]]] = False
    ax.hist(data[occupied_slots],bins=n_points, histtype='step')
filename='data.png'
plt.savefig(filename)
IPdisp.Image(filename=filename)

# <codecell>

fig, axes = plt.subplots(nrows=1,ncols=2,figsize=(8,2))
for ax, data in zip(axes,electrons):
    n_bins = n_points;
    occupied_slots = (data==data)
    occupied_slots[empty_electron_slots[0:current_empty_electron_slot[0]]] = False
    ax.hist(data[occupied_slots],bins=n_bins, histtype='step')
filename='data.png'
plt.savefig(filename)
IPdisp.Image(filename=filename)

# <codecell>


# <codecell>

