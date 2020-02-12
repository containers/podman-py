def normalize_platform(platform, engine_info):
    if platform is None:
        platform = {}
    if 'os' not in platform:
        platform['os'] = engine_info['Os']
    if 'architecture' not in platform:
        platform['architecture'] = engine_info['Arch']
    return platform
