def _private_choice():
    return torch.rand(1, 1, 16, 16)

def einstein():
    return po.process.blur_downsample(po.data.einstein(), 4)

def curie():
    return po.process.blur_downsample(po.data.curie(), 4)

def rand():
    return _private_choice()
