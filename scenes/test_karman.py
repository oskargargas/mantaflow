from manta import *

new_BC     = True
dim        = 2
#res        = 124
res        = 64
gs         = vec3(2*res,res,res)
if (dim==2): gs.z = 1
s          = FluidSolver(name='main', gridSize = gs, dim=dim)
s.timestep = 1.
timings    = Timings()

flags     = s.create(FlagGrid)
vel       = s.create(MACGrid)
pressure  = s.create(RealGrid)
fractions = s.create(MACGrid)
density   = s.create(RealGrid)
phiWalls  = s.create(LevelsetGrid)

flags.initDomain(inflow="xX", phiWalls=phiWalls, boundaryWidth=0)

sphere  = s.create(Sphere, center=gs*vec3(0.25,0.5,0.5), radius=res*0.2)
phiObs = sphere.computeLevelset()

phiObs.join(phiWalls)
updateFractions( flags=flags, phiObs=phiObs, fractions=fractions)
setObstacleFlags(flags=flags, phiObs=phiObs, fractions=fractions)
flags.fillGrid()

velInflow = vec3(0.5,0,0)
vel.setConst(velInflow)

# optionally randomize y component
if 0:
	noise = s.create(NoiseField, loadFromFile=True)
	noise.posScale = vec3(75)
	noise.clamp    = True
	noise.clampNeg = -1.
	noise.clampPos =  1.
	testall = s.create(RealGrid); testall.setConst(-1.);
	addNoise(flags=flags, density=density, noise=noise, sdf=testall, scale=1 )

setComponent(target=vel, source=density, component=1)
density.setConst(0.)

# cg solver params
acc = 1e-04
cgiter = 5

if (GUI):
	gui = Gui()
	gui.show()
	gui.pause()

#main loop
for t in range(25000):

	applyDensAtObstacle(phiObs=phiObs, dens=density)

	advectSemiLagrange(flags=flags, vel=vel, grid=density, order=2, orderSpace=1)  
	advectSemiLagrange(flags=flags, vel=vel, grid=vel    , order=2, strength=1.0)

	if(new_BC):
		extrapolateMACSimple( flags=flags, vel=vel, distance=2 , intoObs=True);
		setWallBcs(flags=flags, vel=vel, fractions=fractions, phiObs=phiObs)

		setInflowBcs(vel=vel,dir='xX',value=velInflow)
		solvePressure( flags=flags, vel=vel, pressure=pressure, fractions=fractions, cgAccuracy=acc, cgMaxIterFac=cgiter)

		extrapolateMACSimple( flags=flags, vel=vel, distance=5 , intoObs=True);
		setWallBcs(flags=flags, vel=vel, fractions=fractions, phiObs=phiObs)
	else:
		setWallBcs(flags=flags, vel=vel)
		setInflowBcs(vel=vel,dir='xX',value=velInflow)
		solvePressure( flags=flags, vel=vel, pressure=pressure, cgAccuracy=acc, cgMaxIterFac=cgiter ) 
		setWallBcs(flags=flags, vel=vel)

	setInflowBcs(vel=vel,dir='xX',value=velInflow)

	timings.display()
	s.step()

	inter = 10
	if 0 and (t % inter == 0):
		if(new_BC):
			gui.screenshot( 'newbc_%04d.png' % int(t/inter) );
		else:
			gui.screenshot( 'oldbc_%04d.png' % int(t/inter) );
			

