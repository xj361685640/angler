import matplotlib.pylab as plt
from matplotlib.colors import LogNorm
import matplotlib.patches as mpatches
import numpy as np
import copy

from fdfdpy import Simulation
from structures import two_port, three_port

from string import ascii_lowercase
from numpy import in1d

def apply_sublabels(axs, invert_color_inds, x=19, y=-5, size='large', ha='right', va='top', prefix='(', postfix=')'):
    # axs = list of axes
    # invert_color_ind = list of booleans (whether to make sublabels white or black)
    for n, ax in enumerate(axs):
        if invert_color_inds[n]:
            color='w'
        else:
            color='k'
        ax.annotate(prefix + ascii_lowercase[n] + postfix,
                    xy=(0, 1),
                    xytext=(x, y),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size=size,
                    color=color,
                    horizontalalignment=ha,
                    verticalalignment=va)


def gen_fig1(eps):

    lambda0 = 2e-6              # free space wavelength (m)
    c0 = 3e8                    # speed of light in vacuum (m/s)
    omega = 2*np.pi*c0/lambda0  # angular frequency (2pi/s)
    dl = 0.8e-1                 # grid size (L0)
    NPML = [15, 15]             # number of pml grid points on x and y borders
    pol = 'Ez'                  # polarization (either 'Hz' or 'Ez')
    source_amp = 2              # amplitude of modal source (A/L0^2?)    L = 7           # length of box (L0)

    L = 7         # length of box (L0)
    H = 5           # height of box (L0)
    w = .3          # width of waveguides (L0)
    d = H/1.5       # distance between waveguides (L0)
    l = 5           # length of waveguide from PML to box (L0)
    spc = 3         # space between box and PML (L0)

    n_index = 2.44              # refractive index
    eps_m = n_index**2          # relative permittivity
    chi3 = 4.1*1e-19            # Al2S3 from Boyd (m^2/V^2)

    # poor man's binarization
    threshold = 3.7  # (eps_m/2 + 1/2)
    eps = eps_m*(eps > threshold) + 1*(eps <= threshold)

    _, design_region = three_port(L, H, w, d, l, spc, dl, NPML, eps_m)

    (Nx, Ny) = eps.shape

    nx, ny = Nx//2, Ny//2

    # make the simulation
    simulation = Simulation(omega, eps, dl, NPML, pol)
    simulation.add_mode(np.sqrt(eps_m), 'x', [NPML[0]+int(l/2/dl), ny], int(H/2/dl), scale=source_amp)
    simulation.setup_modes()

    # add nonlinearity
    nl_region = copy.deepcopy(design_region)
    simulation.nonlinearity = []  # This is needed in case you re-run this cell, for example (or you can re-initialize simulation every time)
    simulation.add_nl(chi3, nl_region, eps_scale=True, eps_max=eps_m)

    x_range = np.linspace(-Nx/2*dl, Nx/2*dl, Nx)
    y_range = np.linspace(-Ny/2*dl, Ny/2*dl, Ny)

    f, (ax_top, ax_bot) = plt.subplots(2, 2, figsize=(7, 5), constrained_layout=True)

    # empty
    eps_display = copy.deepcopy(eps)
    eps_display[design_region==1] = eps_m
    ax_drawing = ax_top[0]
    im = ax_drawing.pcolormesh(x_range, y_range, eps_display.T, cmap='Greys')
    ax_drawing.set_xlabel('x position ($\mu$m)')
    ax_drawing.set_ylabel('y position ($\mu$m)')
    # ax_drawing.set_title('optimization setup')
    y_dist = 1.6
    base_in = 7
    tip_in = 3
    arrow_in = mpatches.FancyArrowPatch((-base_in, 0), (-tip_in, 0),
                                     mutation_scale=20, facecolor='#cc99ff')
    ax_drawing.add_patch(arrow_in)
    arrow_top = mpatches.FancyArrowPatch((tip_in, y_dist+0.1), (base_in, y_dist+0.1),
                                     mutation_scale=20, facecolor='#3366ff')
    ax_drawing.add_patch(arrow_top)
    arrow_bot = mpatches.FancyArrowPatch((tip_in, -y_dist), (base_in, -y_dist),
                                     mutation_scale=20, facecolor='#ff5050')
    ax_drawing.add_patch(arrow_bot)
    ax_drawing.annotate('design\nregion', (0, 0), xytext=(77, 63),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='w',
                    horizontalalignment='center',
                    verticalalignment='center')
    ax_drawing.annotate('linear', (0, 0), xytext=(107, 70),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='k',
                    horizontalalignment='left',
                    verticalalignment='center')
    ax_drawing.annotate('nonlinear', (0, 0), xytext=(107, 38),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='k',
                    horizontalalignment='left',
                    verticalalignment='center')

    # permittivity
    ax_eps = ax_top[1]
    im = ax_eps.pcolormesh(x_range, y_range, eps.T, cmap='Greys')
    ax_eps.set_xlabel('x position ($\mu$m)')
    ax_eps.set_ylabel('y position ($\mu$m)')
    # ax_eps.set_title('relative permittivity')
    plt.colorbar(im, ax=ax_eps)

    # linear fields
    ax_lin = ax_bot[0]
    (_, _, Ez) = simulation.solve_fields()
    E_lin = np.abs(Ez.T)
    # im = ax_lin.pcolormesh(x_range, y_range, E_lin, cmap='magma', norm=LogNorm(vmin=1, vmax=10))
    im = ax_lin.pcolormesh(x_range, y_range, E_lin, cmap='inferno', norm=LogNorm(vmin=1, vmax=E_lin.max()))
    ax_lin.contour(x_range, y_range, eps.T, levels=2, linewidths=0.2, colors='w')
    ax_lin.set_xlabel('x position ($\mu$m)')
    ax_lin.set_ylabel('y position ($\mu$m)')
    ax_lin.set_title('linear fields')
    plt.colorbar(im, ax=ax_lin)
    ax_lin.annotate('$|E_z|$', (0, 1), xytext=(147, -5),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='large',
                    color='w',
                    horizontalalignment='right',
                    verticalalignment='top')

    # nonlinear fields
    ax_nl = ax_bot[1]
    (_, _, Ez_nl, _) = simulation.solve_fields_nl()
    E_nl = np.abs(Ez_nl.T)
    # im = ax_nl.pcolormesh(x_range, y_range, E_nl, cmap='magma', norm=LogNorm(vmin=1, vmax=10))
    im = ax_nl.pcolormesh(x_range, y_range, E_nl, cmap='inferno', norm=LogNorm(vmin=1, vmax=E_nl.max()))
    ax_nl.contour(x_range, y_range, eps.T, levels=2, linewidths=0.2, colors='w')
    ax_nl.set_xlabel('x position ($\mu$m)')
    ax_nl.set_ylabel('y position ($\mu$m)')
    ax_nl.set_title('nonlinear fields')
    plt.colorbar(im, ax=ax_nl)
    ax_nl.annotate('$|E_z|$', (0, 1), xytext=(147, -5),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='large',
                    color='w',
                    horizontalalignment='right',
                    verticalalignment='top')

    apply_sublabels([ax_drawing, ax_eps, ax_lin, ax_nl], invert_color_inds=[False, False, True, True])

    plt.savefig('data/figs/fig1', dpi=400)



def gen_fig2(eps):

    lambda0 = 2e-6              # free space wavelength (m)
    c0 = 3e8                    # speed of light in vacuum (m/s)
    omega = 2*np.pi*c0/lambda0  # angular frequency (2pi/s)
    dl = 0.8e-1                 # grid size (L0)
    NPML = [15, 15]             # number of pml grid points on x and y borders
    pol = 'Ez'                  # polarization (either 'Hz' or 'Ez')
    source_amp = 1.6            # amplitude of modal source (A/L0^2?)    L = 7           # length of box (L0)

    L = 8         # length of box (L0)
    H = 5         # height of box (L0)
    w = .3        # width of waveguides (L0)
    d = H/2.44    # distance between waveguides (L0)
    l = 4         # length of waveguide from PML to box (L0)
    spc = 3       # space between box and PML (L0)

    n_index = 2.44              # refractive index
    eps_m = n_index**2          # relative permittivity
    chi3 = 4.1*1e-19            # Al2S3 from Boyd (m^2/V^2)

    # poor man's binarization
    # eps = eps_m*(eps > (eps_m/2 + 1/2)) + 1*(eps <= (eps_m/2 + 1/2))

    _, design_region = two_port(L, H, w, l, spc, dl, NPML, eps_m)

    (Nx, Ny) = eps.shape

    nx, ny = Nx//2, Ny//2

    # set the modal source and probes
    simulation = Simulation(omega, eps, dl, NPML, 'Ez')
    simulation.add_mode(np.sqrt(eps_m), 'x', [NPML[0]+int(l/2/dl), ny], int(H/2/dl), scale=source_amp)
    simulation.setup_modes()

    # add nonlinearity
    nl_region = copy.deepcopy(design_region)
    simulation.nonlinearity = []  # This is needed in case you re-run this cell, for example (or you can re-initialize simulation every time)
    simulation.add_nl(chi3, nl_region, eps_scale=True, eps_max=eps_m)

    x_range = np.linspace(-Nx/2*dl, Nx/2*dl, Nx)
    y_range = np.linspace(-Ny/2*dl, Ny/2*dl, Ny)

    f, (ax_top, ax_bot) = plt.subplots(2, 2, figsize=(7, 5), constrained_layout=True)

    # empty
    eps_display = copy.deepcopy(eps)
    eps_display[design_region==1] = eps_m
    ax_drawing = ax_top[0]
    im = ax_drawing.pcolormesh(x_range, y_range, eps_display.T, cmap='Greys')
    ax_drawing.set_xlabel('x position ($\mu$m)')
    ax_drawing.set_ylabel('y position ($\mu$m)')
    # ax_drawing.set_title('optimization setup')
    y_dist = 1.6
    base_in = 7
    tip_in = 3
    arrow_in = mpatches.FancyArrowPatch((-base_in, 0), (-tip_in, 0),
                                     mutation_scale=20, facecolor='#cc99ff')
    ax_drawing.add_patch(arrow_in)
    arrow_top = mpatches.FancyArrowPatch((tip_in, y_dist+0.1), (base_in, y_dist+0.1),
                                     mutation_scale=20, facecolor='#3366ff')
    ax_drawing.add_patch(arrow_top)
    arrow_bot = mpatches.FancyArrowPatch((tip_in, -y_dist), (base_in, -y_dist),
                                     mutation_scale=20, facecolor='#ff5050')
    ax_drawing.add_patch(arrow_bot)
    ax_drawing.annotate('design\nregion', (0, 0), xytext=(77, 63),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='w',
                    horizontalalignment='center',
                    verticalalignment='center')
    ax_drawing.annotate('linear', (0, 0), xytext=(107, 70),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='k',
                    horizontalalignment='left',
                    verticalalignment='center')
    ax_drawing.annotate('nonlinear', (0, 0), xytext=(107, 38),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='small',
                    color='k',
                    horizontalalignment='left',
                    verticalalignment='center')

    # permittivity
    ax_eps = ax_top[1]
    im = ax_eps.pcolormesh(x_range, y_range, eps.T, cmap='Greys')
    ax_eps.set_xlabel('x position ($\mu$m)')
    ax_eps.set_ylabel('y position ($\mu$m)')
    # ax_eps.set_title('relative permittivity')
    plt.colorbar(im, ax=ax_eps)

    # linear fields
    ax_lin = ax_bot[0]
    (_, _, Ez) = simulation.solve_fields()
    E_lin = np.abs(Ez.T)
    # im = ax_lin.pcolormesh(x_range, y_range, E_lin, cmap='magma', norm=LogNorm(vmin=1, vmax=10))
    im = ax_lin.pcolormesh(x_range, y_range, E_lin, cmap='inferno', norm=LogNorm(vmin=1.6, vmax=E_lin.max()))
    ax_lin.contour(x_range, y_range, eps.T, levels=2, linewidths=0.2, colors='w')
    ax_lin.set_xlabel('x position ($\mu$m)')
    ax_lin.set_ylabel('y position ($\mu$m)')
    ax_lin.set_title('linear fields')
    plt.colorbar(im, ax=ax_lin)
    ax_lin.annotate('$|E_z|$', (0, 1), xytext=(147, -5),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='large',
                    color='w',
                    horizontalalignment='right',
                    verticalalignment='top')

    # nonlinear fields
    ax_nl = ax_bot[1]
    (_, _, Ez_nl, _) = simulation.solve_fields_nl()
    E_nl = np.abs(Ez_nl.T)
    # im = ax_nl.pcolormesh(x_range, y_range, E_nl, cmap='magma', norm=LogNorm(vmin=1, vmax=10))
    im = ax_nl.pcolormesh(x_range, y_range, E_nl, cmap='inferno', norm=LogNorm(vmin=1.6, vmax=E_nl.max()))
    ax_nl.contour(x_range, y_range, eps.T, levels=2, linewidths=0.2, colors='w')
    ax_nl.set_xlabel('x position ($\mu$m)')
    ax_nl.set_ylabel('y position ($\mu$m)')
    ax_nl.set_title('nonlinear fields')
    plt.colorbar(im, ax=ax_nl)
    ax_nl.annotate('$|E_z|$', (0, 1), xytext=(147, -5),
                    xycoords='axes fraction',
                    textcoords='offset points',
                    size='large',
                    color='w',
                    horizontalalignment='right',
                    verticalalignment='top')

    apply_sublabels([ax_drawing, ax_eps, ax_lin, ax_nl], invert_color_inds=[False, False, True, True])

    plt.savefig('data/figs/fig2', dpi=400)

if __name__ == '__main__':
    eps_3 = np.load('data/figs/data/3port_eps.npy')
    gen_fig1(eps_3)

    eps_2 = np.load('data/figs/data/2port_eps.npy')
    gen_fig2(eps_2)

