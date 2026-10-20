"""Source26 finite startup transport projection; all outputs remain in RAM.

The caller supplies the complete exact Source25 predecessors. No SDK, runtime,
Task, Game, process, pipe, or storage admission is created by this producer.
"""
import hashlib

SDK_IO='xar_autoplayer/bridge/native_loaded_provider_origin_io_v1.py'
SDK_ORIGIN='xar_autoplayer/bridge/native_loaded_provider_origin_v1.py'
SDK_PINS={SDK_IO:(6755,'9b0e5e3528f68777979afd1742cd4d525051ad0e9b16225d7175d4a29474827e'),
    SDK_ORIGIN:(15954,'3b8bd840df7b3d6af7326f388363729e909c88355d0649f892189d70ae390695')}
HOST_PIN=(15181,'54475da0a10dce93fe306880df502e977cd41c056195b3a429bd7465e79a1ef4')
OUTER_PIN=(18711,'11f4879e6c9be2a5cf1ab8578ab5e8b84d159c1c0261fbde752a169cfe2095ac')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def checked(raw,pin):
    if type(raw) is not bytes or (len(raw),sha(raw))!=pin:
        raise ValueError('exact complete Source25/A04 predecessor required')
    return raw


def swap(raw,before,after,count=1):
    before=before.encode();after=after.encode()
    if raw.count(before)!=count:raise ValueError('startup projection seam changed: '+before.decode())
    return raw.replace(before,after)


def compose_sdk(inputs):
    """Return exactly the two SDK-relative outputs, preserving all other bytes."""
    if set(inputs)!=set(SDK_PINS):raise ValueError('exact two complete SDK inputs required')
    io=checked(inputs[SDK_IO],SDK_PINS[SDK_IO])
    io=swap(io,'enabled=False, timeout=10.0):','enabled=False, timeout=10.0, startup_timeout=10.0):')
    io=swap(io,'        self.facade,self.api,self.timeout=facade,facade._os(),timeout',
        '        contract._require(type(startup_timeout) in (int,float) and 0<startup_timeout<=300,\n'
        '                          "bounded private startup timeout required")\n'
        '        self.facade,self.api,self.timeout=facade,facade._os(),timeout\n'
        '        self.startup_timeout=startup_timeout')
    io=swap(io,'deadline=time.monotonic()+self.timeout\n        while True:',
        'deadline=time.monotonic()+self.startup_timeout\n        while True:',2)
    io=swap(io,'    def recv(self,handle):\n        deadline=time.monotonic()+self.timeout;raw=self.rx.get(handle,b"")',
        '    def recv(self,handle,*,startup=False):\n'
        '        contract._require(type(startup) is bool,"explicit startup phase required")\n'
        '        budget=self.startup_timeout if startup else self.timeout\n'
        '        deadline=time.monotonic()+budget;raw=self.rx.get(handle,b"")')
    origin=checked(inputs[SDK_ORIGIN],SDK_PINS[SDK_ORIGIN])
    origin=swap(origin,'hello=io.recv(control)','hello=io.recv(control,startup=True)')
    origin=swap(origin,'message=io.recv(edge.control)','message=io.recv(edge.control,startup=True)')
    origin=swap(origin,'self.ready.wait(self.io.timeout)','self.ready.wait(self.io.startup_timeout)')
    origin=swap(origin,'def prepare_canonical_origin_v1(*,custody,enabled=False):',
        'def prepare_canonical_origin_v1(*,custody,enabled=False,startup_timeout=10.0):')
    origin=swap(origin,'io=OriginKernelIOV1(custody.facade,enabled=True)',
        'io=OriginKernelIOV1(custody.facade,enabled=True,startup_timeout=startup_timeout)')
    origin=swap(origin,'def attach_received_origin_v1(result,*,origin_handle,origin_pipe,enabled=False):',
        'def attach_received_origin_v1(result,*,origin_handle,origin_pipe,enabled=False,startup_timeout=10.0):')
    origin=swap(origin,'io=OriginKernelIOV1(holder.facade,enabled=True)',
        'io=OriginKernelIOV1(holder.facade,enabled=True,startup_timeout=startup_timeout)')
    result={SDK_IO:io,SDK_ORIGIN:origin}
    for name,raw in result.items():compile(raw,name,'exec')
    return result


def compose_host(raw):
    """New frozen creator helper; not an in-place repository/runtime edit."""
    raw=checked(raw,HOST_PIN)
    raw=swap(raw,'entry_source_pins=(),enabled=False):','entry_source_pins=(),enabled=False,startup_timeout=10.0):')
    raw=swap(raw,'        self.entry_source_pins=entry_source_pins',
        '        contract._require(type(startup_timeout) in (int,float) and 0<startup_timeout<=300,\n'
        '                          "bounded private startup timeout required")\n'
        '        self.startup_timeout=startup_timeout\n'
        '        self.entry_source_pins=entry_source_pins')
    raw=swap(raw,'prepare_canonical_origin_v1(custody=self.holder,enabled=True)',
        'prepare_canonical_origin_v1(custody=self.holder,enabled=True,startup_timeout=self.startup_timeout)')
    raw=swap(raw,'def receive_child_bootstrap_v1(hints,*,facade,enabled=False):',
        'def receive_child_bootstrap_v1(hints,*,facade,enabled=False,startup_timeout=10.0):')
    raw=swap(raw,'io=OriginKernelIOV1(facade,enabled=True)',
        'io=OriginKernelIOV1(facade,enabled=True,startup_timeout=startup_timeout)')
    raw=swap(raw,'io.recv(control)=={"kind":"parent_accepted"',
        'io.recv(control,startup=True)=={"kind":"parent_accepted"')
    raw=swap(raw,'def install_received_provider_bootstrap_v1(service,result,*,enabled=False):',
        'def install_received_provider_bootstrap_v1(service,result,*,enabled=False,startup_timeout=10.0):')
    raw=swap(raw,'io=OriginKernelIOV1(holder.facade,enabled=True)',
        'io=OriginKernelIOV1(holder.facade,enabled=True,startup_timeout=startup_timeout)')
    compile(raw,'Source26-frozen-canonical-native-provider-chain','exec')
    return raw


def compose_outer(raw,host_raw):
    """Actual production callers explicitly opt into 120 seconds once only."""
    raw=checked(raw,OUTER_PIN)
    raw=swap(raw,HOST_PIN[1],sha(host_raw))
    raw=swap(raw,'entry_source_pins=entries, enabled=True)',
        'entry_source_pins=entries, enabled=True, startup_timeout=120.0)')
    raw=swap(raw,'hints, facade=WindowsNativeCustodyFacadeV1(enabled=True), enabled=True)',
        'hints, facade=WindowsNativeCustodyFacadeV1(enabled=True), enabled=True, startup_timeout=120.0)')
    raw=swap(raw,'install_received_provider_bootstrap_v1(service, self.result, enabled=True)',
        'install_received_provider_bootstrap_v1(service, self.result, enabled=True, startup_timeout=120.0)')
    compile(raw,'Source26-future-outer-caller','exec')
    return raw
