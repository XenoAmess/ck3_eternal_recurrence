"""Pre-resume MEM_IMAGE observation only; never a loaded-module identity DTO."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PreloadImageV1:
    allocation_base: int
    mapped_nt_path: str


@dataclass(frozen=True)
class RegionV1:
    returned_bytes: int
    base: int
    size: int
    state: int
    allocation_base: int
    kind: int


def _need(ok, reason):
    if not ok:
        raise ValueError("incomplete pre-resume image mappings: " + reason)


def validate_image_v1(value):
    _need(type(value) is PreloadImageV1 and type(value.allocation_base) is int
          and 0 < value.allocation_base < 2**64, "typed allocation base")
    path = value.mapped_nt_path
    _need(isinstance(path, str) and path.startswith("\\Device\\")
          and "\0" not in path and "/" not in path and len(path) < 32767
          and all(p not in ("", ".", "..") for p in path[1:].split("\\")),
          "canonical kernel mapped NT path")
    return value


def _walk(reader, bounds):
    minimum, maximum, page, bits = bounds
    _need(all(type(v) is int for v in bounds) and bits == 64
          and 0 < minimum <= maximum < 2**64 - 1 and page > 0
          and page & (page - 1) == 0 and minimum % page == 0
          and (maximum + 1) % page == 0, "system user-address bounds")
    pos, images, regions = minimum, {}, 0
    while pos <= maximum:
        regions += 1
        _need(regions <= 65536, "region cap")
        row = reader.query(pos)  # Every OS error, including ERROR87, rejects.
        _need(type(row) is RegionV1 and row.returned_bytes == 48
              and all(type(v) is int for v in (row.base, row.size, row.state))
              and 0 <= row.base <= pos and row.size > 0, "complete MBI region")
        end = row.base + row.size
        _need(pos < end <= 2**64
              and row.base % page == 0 and row.size % page == 0,
              "bounded positive region advance")
        _need(row.state in (0x1000, 0x2000, 0x10000), "known MBI state")
        # MEM_FREE has undefined Type/AllocationBase/Protect; never read them.
        if row.state != 0x10000:
            _need(type(row.kind) is int and row.kind in (0x20000, 0x40000, 0x1000000),
                  "defined mapped allocation type")
            if row.kind == 0x1000000:
                base = row.allocation_base
                _need(type(base) is int and minimum <= base <= row.base
                      and base % page == 0, "MEM_IMAGE allocation base")
                if base not in images:
                    _need(len(images) < 4096, "image cap")
                    images[base] = validate_image_v1(PreloadImageV1(base, reader.mapped_name(base)))
        pos = end
    _need(pos > maximum and images, "complete nonempty user-address image walk")
    reader.last_walk_regions = regions
    return tuple(images[base] for base in sorted(images))


def stable_preload_images_v1(reader):
    bounds = reader.bounds()
    first = _walk(reader, bounds)
    _need(reader.bounds() == bounds, "system bounds changed")
    second = _walk(reader, bounds)
    _need(first == second, "mapped image roster changed")
    return first


class Win32PreloadMapReaderV1:
    """Uses the same held-process read handle and already loaded Win32 facade."""
    def __init__(self, api, process_handle):
        c, w = api.c, api.w
        _need(c.sizeof(c.c_void_p) == 8, "x64 reader required")
        class SystemInfo(c.Structure):
            _fields_ = [("architecture", w.DWORD), ("page", w.DWORD),
                ("minimum", c.c_void_p), ("maximum", c.c_void_p),
                ("mask", c.c_size_t), ("processors", w.DWORD),
                ("processor_type", w.DWORD), ("granularity", w.DWORD),
                ("level", w.WORD), ("revision", w.WORD)]
        class MBI(c.Structure):
            _fields_ = [("base", c.c_void_p), ("allocation", c.c_void_p),
                ("allocation_protect", w.DWORD), ("partition", w.WORD),
                ("size", c.c_size_t), ("state", w.DWORD),
                ("protect", w.DWORD), ("kind", w.DWORD)]
        _need(c.sizeof(SystemInfo) == 48 and c.sizeof(MBI) == 48,
              "native system/MBI layout")
        self.api, self.handle, self.SI, self.MBI = api, process_handle, SystemInfo, MBI
        self.system = api.k.GetNativeSystemInfo
        self.system.argtypes, self.system.restype = [c.POINTER(SystemInfo)], None
        self.query_api = api.k.VirtualQueryEx
        self.query_api.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(MBI), c.c_size_t]
        self.query_api.restype = c.c_size_t
        self.last_walk_regions = 0

    def bounds(self):
        info = self.SI()
        self.system(self.api.c.byref(info))
        return int(info.minimum or 0), int(info.maximum or 0), int(info.page), 64

    def query(self, address):
        info = self.MBI()
        c = self.api.c
        count = int(self.query_api(self.api._handle(self.handle), address,
                                  c.byref(info), c.sizeof(info)))
        if count == 0:
            raise c.WinError(c.get_last_error(), "VirtualQueryEx(pre-resume)")
        return RegionV1(count, int(info.base or 0), int(info.size), int(info.state),
                        int(info.allocation or 0), int(info.kind))

    def mapped_name(self, allocation_base):
        return self.api.mapped_file_name(self.handle, allocation_base)
