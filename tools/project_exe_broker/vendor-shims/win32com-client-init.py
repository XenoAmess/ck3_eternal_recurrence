"""Broker-only dynamic dispatch; never import generated/cache/pickle code."""
import pythoncom
from . import dynamic
_PyIDispatchType = pythoncom.TypeIIDs[pythoncom.IID_IDispatch]
def Dispatch(dispatch, userName=None, resultCLSID=None, typeinfo=None, clsctx=pythoncom.CLSCTX_SERVER):
    return dynamic.Dispatch(dispatch, userName, createClass=dynamic.CDispatch, typeinfo=typeinfo, clsctx=clsctx)
def GetObject(Pathname=None, Class=None, clsctx=pythoncom.CLSCTX_SERVER):
    if (Pathname is None) == (Class is None):
        raise ValueError("Provide exactly one fixed COM pathname or class")
    if Class is not None:
        return Dispatch(pythoncom.GetActiveObject(Class).QueryInterface(pythoncom.IID_IDispatch))
    moniker, _, bind_context = pythoncom.MkParseDisplayName(Pathname)
    return Dispatch(moniker.BindToObject(bind_context, None, pythoncom.IID_IDispatch))
def _get_good_single_object_(obj, obUserName=None, resultCLSID=None):
    return Dispatch(obj, obUserName, resultCLSID) if isinstance(obj, _PyIDispatchType) else obj
def _get_good_object_(obj, obUserName=None, resultCLSID=None):
    if isinstance(obj, tuple):
        return tuple(_get_good_object_(value, obUserName, resultCLSID) for value in obj)
    return _get_good_single_object_(obj, obUserName, resultCLSID)

class VARIANT:
    def __init__(self, vt, value):
        self.varianttype = vt
        self._value = value

    # 'value' is a property so when set by pythoncom it gets any magic wrapping
    # which normally happens for result objects
    def _get_value(self):
        return self._value

    def _set_value(self, newval):
        self._value = _get_good_object_(newval)

    def _del_value(self):
        del self._value

    value = property(_get_value, _set_value, _del_value)

    def __repr__(self):
        return f"win32com.client.VARIANT({self.varianttype!r}, {self._value!r})"

