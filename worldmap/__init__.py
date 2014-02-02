__version__= (1, 2, 0, 'beta', 0)

def get_version():
    import worldmap.utils
    return worldmap.utils.get_version(__version__)
