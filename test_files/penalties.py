def penalty():
    return po.regularize.penalize_range

def other_penalty():
    return lambda x: po.regularize.penalize_range(x, (-0.5, 0.5))
