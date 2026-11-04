def gaussian(image):
    return po.models.Gaussian(image.shape[-1] // 4, cache_filt=True)

def other_gaussian():
    return po.models.Gaussian(4, cache_filt=True)
