import numpy as np
# Case Params
r = 0
q = 0
real_vol = 0.2
vol_time = np.concatenate(
    (np.arange(149,151), np.arange(299,301), np.arange(449,451)))
rng_time = np.concatenate(
    (np.arange(75,150), np.arange(225, 300), np.arange(375, 450)))

c2p_dict = {
    'RTM45C' : 'RTM45P', 'RTM46C' : 'RTM46P', 'RTM47C' : 'RTM47P',
    'RTM48C' : 'RTM48P', 'RTM49C' : 'RTM49P', 'RTM50C' : 'RTM50P',
    'RTM51C' : 'RTM51P', 'RTM52C' : 'RTM52P', 'RTM53C' : 'RTM53P',
    'RTM54C' : 'RTM54P',
}
p2c_dict = {
    'RTM45P' : 'RTM45C', 'RTM46P' : 'RTM46C', 'RTM47P' : 'RTM47C',
    'RTM48P' : 'RTM48C', 'RTM49P' : 'RTM49C', 'RTM50P' : 'RTM50C',
    'RTM51P' : 'RTM51C', 'RTM52P' : 'RTM52C', 'RTM53P' : 'RTM53C',
    'RTM54P' : 'RTM54C',
}

ava_ticker = [
    'RTM45P', 'RTM45C', 'RTM46P', 'RTM46C', 'RTM47P', 'RTM47C',
    'RTM48P', 'RTM48C', 'RTM49P', 'RTM49C', 'RTM50P', 'RTM50C',
    'RTM51P', 'RTM51C', 'RTM52P', 'RTM52C', 'RTM53P', 'RTM53C',
    'RTM54P', 'RTM54C',
]
