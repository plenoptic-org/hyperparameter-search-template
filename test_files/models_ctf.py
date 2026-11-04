class SimpleCTF(po.models.Gaussian):
    def __init__(self):
        super().__init__(4, cache_filt=True)
        self.scales = [0, 1]
    def forward(self, x, scales=[]):
        rep = super().forward(x)
        if 0 in scales:
            rep = rep[..., 1:]
        if 1 in scales:
            rep = rep[..., :-4]
        return rep


class AnotherSimpleCTF(po.models.Gaussian):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scales = [0, 1]
    def forward(self, x, scales=[]):
        rep = super().forward(x)
        if 0 in scales:
            rep = rep[..., 1:]
        if 1 in scales:
            rep = rep[..., :-4]
        return rep


def another_simple_ctf(image):
    return AnotherSimpleCTF(image.shape[-1] // 4, cache_filt=True)


def simple_ctf():
    return SimpleCTF()
