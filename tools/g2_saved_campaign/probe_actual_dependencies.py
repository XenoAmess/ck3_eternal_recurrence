"""Import real recording/overlay dependencies only; never connect or instantiate runtime objects."""
import argparse,importlib,importlib.util,json,os,sys
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--overlay',type=Path,required=True);p.add_argument('--provider',type=Path,required=True)
    p.add_argument('--sdk-source',type=Path,required=True);a=p.parse_args()
    origins={}
    for name in ['PIL.Image','win32gui','win32process','pythoncom','win32com.client','psutil','websocket','obsws_python',
                 'decision_overlay_window','managed_desktop1_placement',
                 'xar_autoplayer.bridge.windows_virtual_desktop','xar_autoplayer.pending_interaction_fallback']:
        module=importlib.import_module(name);origins[name]=getattr(module,'__file__',None)
    actual=Path(origins['xar_autoplayer.pending_interaction_fallback']).resolve()
    assert actual.is_relative_to(a.sdk_source.resolve()),(actual,a.sdk_source)
    for name,path in [('actual_overlay_dependency_probe',a.overlay),('actual_provider_dependency_probe',a.provider)]:
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module)
    print(json.dumps({'status':'GREEN','interpreter':sys.executable,'base_interpreter':sys._base_executable,
                      'origins':origins,'runtime_objects_created':0,'process_or_window_calls':0}))
if __name__=='__main__':main()
