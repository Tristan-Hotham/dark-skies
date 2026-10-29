"""Sky glow model shared by the world (2.5 arc minute) and UK (30 arc second) runs.

Artificial zenith sky brightness at a place is modelled as the sum, over every lit grid cell within R_MAX km, of the
cell's upward light (VIIRS annual radiance x lit area) times a distance kernel:

    B(x) = k * sum_j E_j * f(d_xj),   f(d) = (d^2 + d0^2)^(-alpha/2) * exp(-d / L)

alpha (how fast glow fades with distance, Walker's law gives about 2.5), L (extra extinction over long distances) and
k (scale, in micro candela per square metre per unit of light) are fitted to Globe at Night Sky Quality Meter
readings (code/03_model.py). d0 = 1 km keeps the kernel finite next to a source.

The convolution runs on latitude bands with FFTs; within a band the east-west cell width uses the band's central
latitude. For coarse grids, the kernel weight between two cells is the mean of f over 5 x 5 sub-points in each, so a
cell's value is its average brightness, not the brightness at its centre.
"""
import numpy as np
from scipy.signal import fftconvolve

KM_PER_DEG = 111.195
D0 = 1.0
R_MAX = 250.0
NATURAL = 174.0          # micro cd/m2, Falchi et al. 2016: 22.0 mag/arcsec2
THRESH = {"pristine": 1.74, "polluted": 13.9, "nat_lost": 87.0, "milky_way": 688.0, "no_dark_adapt": 3000.0}


def kernel_band(lat_c, cell_deg, alpha, L, sub=5):
    """Kernel on the cell grid for a band centred at lat_c. Returns (ky, kx) half sizes and the 2D array."""
    dy = cell_deg * KM_PER_DEG
    dx = cell_deg * KM_PER_DEG * np.cos(np.radians(lat_c))
    ny = int(np.ceil(R_MAX / dy)); nx = int(min(np.ceil(R_MAX / dx), 2000))
    iy = np.arange(-ny, ny + 1)[:, None]; ix = np.arange(-nx, nx + 1)[None, :]
    if sub > 1:
        o = (np.arange(sub) + .5) / sub - .5
        oy = (o[:, None] - o[None, :]).ravel(); ox = oy  # offsets between sub-points of the two cells
        acc = np.zeros((2 * ny + 1, 2 * nx + 1))
        # mean over all pairs of sub-points: use the distribution of differences (sub*sub values per axis)
        for a in np.unique(np.round(oy, 6)):
            wa = np.mean(np.isclose(oy, a))
            for b in np.unique(np.round(ox, 6)):
                wb = np.mean(np.isclose(ox, b))
                d = np.hypot((iy + a) * dy, (ix + b) * dx)
                acc += wa * wb * f(d, alpha, L)
        k = acc
    else:
        d = np.hypot(iy * dy, ix * dx); k = f(d, alpha, L)
    d = np.hypot(iy * dy, ix * dx)
    k[d > R_MAX + max(dx, dy)] = 0
    return ny, nx, k


def f(d, alpha, L):
    out = (d * d + D0 * D0) ** (-alpha / 2)
    if L: out = out * np.exp(-d / L)
    return out


def convolve(E, lat_top, cell_deg, alpha, L, band_rows=48, sub=5, wrap=False, rows=None):
    """E: emission grid (rows from lat_top southwards). Returns unscaled glow S with the same shape."""
    H, W = E.shape
    S = np.zeros_like(E, dtype=np.float64)
    r_lo, r_hi = rows if rows else (0, H)
    for r0 in range(r_lo, r_hi, band_rows):
        r1 = min(r0 + band_rows, r_hi)
        lat_c = lat_top - (r0 + r1) / 2 * cell_deg
        ny, nx, K = kernel_band(lat_c, cell_deg, alpha, L, sub)
        a0, a1 = max(0, r0 - ny), min(H, r1 + ny)
        blk = E[a0:a1]
        if not blk.any():
            continue
        if wrap:
            blk = np.concatenate([blk[:, -nx:], blk, blk[:, :nx]], axis=1)
            out = fftconvolve(blk, K, mode="same")[:, nx:nx + W]
        else:
            out = fftconvolve(blk, K, mode="same")
        S[r0:r1] = out[r0 - a0:r1 - a0]
    S[S < 0] = 0
    return S


def cell_area_km2(lat, cell_deg):
    return (cell_deg * KM_PER_DEG) ** 2 * np.cos(np.radians(lat))


def to_mag(b_art):
    """Total zenith brightness in mag/arcsec2 from artificial brightness in micro cd/m2 (natural sky 22.0 added)."""
    return 22.0 - 2.5 * np.log10((np.asarray(b_art) + NATURAL) / NATURAL)


def from_mag(m):
    return NATURAL * 10 ** (-0.4 * (np.asarray(m) - 22.0))


def f16_coarse(a, drop_bits=3):
    """float16 with the lowest mantissa bits cleared (relative precision about 1%), so that it compresses well."""
    h = np.asarray(a, dtype=np.float16).copy()
    v = h.view(np.uint16); v &= np.uint16(0xFFFF ^ ((1 << drop_bits) - 1))
    return h
