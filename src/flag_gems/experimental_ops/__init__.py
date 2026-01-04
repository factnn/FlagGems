try:
    from flag_gems.experimental_ops.rmsnorm import rmsnorm
    __all__ = ["rmsnorm"]
except ImportError:
    # rmsnorm module not found, skip it
    __all__ = []
