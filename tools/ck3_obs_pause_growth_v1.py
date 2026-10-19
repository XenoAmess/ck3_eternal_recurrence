"""Pure file-growth deadline accounting after a verified owned OBS read.

This grants no ownership. Callers must retain/check their OBS generation and
bind the WS profile/output before reading status, then check generation again.
Only strict active+paused observations suspend the growth deadline.
"""
def advance_growth_deadline_v1(previous, changed, was_paused, *, current, now,
                               output_active, output_paused, error_message):
    import math
    if (type(previous) is not int or previous < 0 or type(current) is not int
            or current < 0 or type(was_paused) is not bool
            or type(changed) not in (int, float) or type(now) not in (int, float)
            or not math.isfinite(changed) or not math.isfinite(now) or now < changed):
        raise ValueError('owned recording growth observation is incomplete')
    if output_active is not True:
        raise RuntimeError('owned recording ended before its bound')
    if current > previous:
        previous, changed = current, now
    if current == previous and output_paused is True:
        # A legal pause stops file growth. A regressed/disappeared file does
        # not gain this exemption and retains the original deadline.
        changed, was_paused = now, True
    elif current >= previous and output_paused is False and was_paused:
        # Resume is a fresh observation, not backdated to an assumed time.
        changed, was_paused = now, False
    if now - changed > 30:
        raise RuntimeError(error_message)
    return previous, changed, was_paused
