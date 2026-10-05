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
