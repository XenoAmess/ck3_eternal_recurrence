"""A read-only Win32 overlay that never requests keyboard or mouse focus."""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
import os


class NativeOverlay:
    def __init__(self):
        self.user = c.WinDLL("user32", use_last_error=True)
        self.gdi = c.WinDLL("gdi32", use_last_error=True)
        kernel = c.WinDLL("kernel32", use_last_error=True)
        kernel.GetModuleHandleW.argtypes = [w.LPCWSTR]
        kernel.GetModuleHandleW.restype = w.HMODULE
        self.instance = kernel.GetModuleHandleW(None)
        callback = c.WINFUNCTYPE(c.c_ssize_t, w.HWND, w.UINT, w.WPARAM, w.LPARAM)

        class WindowClass(c.Structure):
            _fields_ = [("style", w.UINT), ("procedure", callback), ("class_extra", c.c_int),
                        ("window_extra", c.c_int), ("instance", w.HINSTANCE), ("icon", w.HICON),
                        ("cursor", w.HANDLE), ("background", w.HBRUSH), ("menu", w.LPCWSTR),
                        ("name", w.LPCWSTR)]

        class Paint(c.Structure):
            _fields_ = [("dc", w.HDC), ("erase", w.BOOL), ("rect", w.RECT),
                        ("restore", w.BOOL), ("update", w.BOOL), ("reserved", c.c_byte * 32)]

        self.Paint = Paint
        signatures = {
            "RegisterClassW": ([c.POINTER(WindowClass)], w.ATOM),
            "UnregisterClassW": ([w.LPCWSTR, w.HINSTANCE], w.BOOL),
            "CreateWindowExW": ([w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, c.c_int, c.c_int,
                                 c.c_int, c.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID], w.HWND),
            "DefWindowProcW": ([w.HWND, w.UINT, w.WPARAM, w.LPARAM], c.c_ssize_t),
            "BeginPaint": ([w.HWND, c.POINTER(Paint)], w.HDC),
            "EndPaint": ([w.HWND, c.POINTER(Paint)], w.BOOL),
            "FillRect": ([w.HDC, c.POINTER(w.RECT), w.HBRUSH], c.c_int),
            "DrawTextW": ([w.HDC, w.LPCWSTR, c.c_int, c.POINTER(w.RECT), w.UINT], c.c_int),
            "GetClientRect": ([w.HWND, c.POINTER(w.RECT)], w.BOOL),
            "GetDC": ([w.HWND], w.HDC),
            "ReleaseDC": ([w.HWND, w.HDC], c.c_int),
            "InvalidateRect": ([w.HWND, c.POINTER(w.RECT), w.BOOL], w.BOOL),
            "DestroyWindow": ([w.HWND], w.BOOL),
            "IsWindow": ([w.HWND], w.BOOL),
            "SetLayeredWindowAttributes": ([w.HWND, w.DWORD, w.BYTE, w.DWORD], w.BOOL),
            "ShowWindow": ([w.HWND, c.c_int], w.BOOL),
            "SetWindowPos": ([w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT], w.BOOL),
            "SetTimer": ([w.HWND, c.c_size_t, w.UINT, c.c_void_p], c.c_size_t),
            "KillTimer": ([w.HWND, c.c_size_t], w.BOOL),
            "GetMessageW": ([c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT], w.BOOL),
            "TranslateMessage": ([c.POINTER(w.MSG)], w.BOOL),
            "DispatchMessageW": ([c.POINTER(w.MSG)], c.c_ssize_t),
            "PostQuitMessage": ([c.c_int], None),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.user, name)
            function.argtypes, function.restype = args, result
        for name, args, result in (
            ("CreateSolidBrush", [w.DWORD], w.HBRUSH),
            ("DeleteObject", [w.HANDLE], w.BOOL),
            ("SelectObject", [w.HDC, w.HANDLE], w.HANDLE),
            ("SetBkMode", [w.HDC, c.c_int], c.c_int),
            ("SetTextColor", [w.HDC, w.DWORD], w.DWORD),
            ("GetTextExtentPoint32W", [w.HDC, w.LPCWSTR, c.c_int, c.POINTER(w.SIZE)], w.BOOL),
            ("CreateFontW", [c.c_int] * 5 + [w.DWORD] * 8 + [w.LPCWSTR], w.HANDLE),
        ):
            function = getattr(self.gdi, name)
            function.argtypes, function.restype = args, result
        self.title, self.body, self.tick = "智能体 · 实时决策", "等待实际规划结果", None
        self.brush = self.gdi.CreateSolidBrush(0x281B11)
        self.title_font = self.gdi.CreateFontW(-24, 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 5, 0, "Microsoft YaHei")
        self.body_font = self.gdi.CreateFontW(-20, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, "Microsoft YaHei")
        if not all((self.brush, self.title_font, self.body_font)):
            raise c.WinError(c.get_last_error())

        def procedure(hwnd, message, first, second):
            if message == 0x84:  # WM_NCHITTEST: no controls or gameplay inputs.
                return -1
            if message == 0x21:  # WM_MOUSEACTIVATE
                return 3
            if message == 0x14:  # WM_ERASEBKGND
                return 1
            if message == 0xF:
                paint = Paint()
                dc = self.user.BeginPaint(hwnd, c.byref(paint))
                rect = w.RECT()
                self.user.GetClientRect(hwnd, c.byref(rect))
                self.user.FillRect(dc, c.byref(rect), self.brush)
                self.gdi.SetBkMode(dc, 1)
                old_font = self.gdi.SelectObject(dc, self.title_font)
                self.gdi.SetTextColor(dc, 0xFFD665)
                title_rect = w.RECT(16, 12, rect.right - 16, 48)
                self.user.DrawTextW(dc, self.title, -1, c.byref(title_rect), 0x804)
                self.gdi.SelectObject(dc, self.body_font)
                self.gdi.SetTextColor(dc, 0xF8EFE8)
                body_rect = w.RECT(16, 60, rect.right - 16, rect.bottom - 12)
                self.user.DrawTextW(dc, self.body, -1, c.byref(body_rect), 0x804)
                self.gdi.SelectObject(dc, old_font)
                self.user.EndPaint(hwnd, c.byref(paint))
                return 0
            if message == 0x113 and self.tick:
                try:
                    self.tick()
                except Exception as error:
                    self.update("实时数据读取失败：" + type(error).__name__)
                return 0
            if message == 2:
                self.user.PostQuitMessage(0)
                return 0
            return self.user.DefWindowProcW(hwnd, message, first, second)

        self.callback = callback(procedure)
        self.name = f"XARG2DecisionOverlay_{os.getpid()}"
        window_class = WindowClass(0, self.callback, 0, 0, self.instance, None, None, None, None, self.name)
        if not self.user.RegisterClassW(c.byref(window_class)):
            raise c.WinError(c.get_last_error())
        width = min(760, max(500, int(self.user.GetSystemMetrics(0) * .30)))
        height = min(760, max(440, int(self.user.GetSystemMetrics(1) * .45)))
        # NOACTIVATE, LAYERED, TRANSPARENT, TOOLWINDOW, TOPMOST are present before creation.
        self.hwnd = self.user.CreateWindowExW(0x080800A8, self.name, self.title, 0x80000000,
                                              24, 88, width, height, None, None, self.instance, None)
        if not self.hwnd or not self.user.SetLayeredWindowAttributes(self.hwnd, 0, 240, 2):
            raise c.WinError(c.get_last_error())
        self.user.ShowWindow(self.hwnd, 4)
        if not self.user.SetWindowPos(self.hwnd, c.c_void_p(-1), 0, 0, 0, 0, 0x53):
            raise c.WinError(c.get_last_error())

    def update(self, body, title="智能体 · 实时决策"):
        # DrawText's word wrapping can leave long unspaced Chinese lines clipped.
        dc = self.user.GetDC(self.hwnd)
        old_font = self.gdi.SelectObject(dc, self.body_font)
        rect = w.RECT()
        self.user.GetClientRect(self.hwnd, c.byref(rect))
        lines = []
        try:
            for paragraph in body.split("\n"):
                if not paragraph:
                    lines.append("")
                    continue
                while paragraph:
                    lower, upper = 1, len(paragraph)
                    fit = 1
                    while lower <= upper:
                        count = (lower + upper) // 2
                        part = paragraph[:count]
                        size = w.SIZE()
                        units = len(part.encode("utf-16-le")) // 2
                        if not self.gdi.GetTextExtentPoint32W(dc, part, units, c.byref(size)):
                            raise c.WinError(c.get_last_error())
                        if size.cx <= rect.right - 32:
                            fit, lower = count, count + 1
                        else:
                            upper = count - 1
                    lines.append(paragraph[:fit])
                    paragraph = paragraph[fit:]
        finally:
            self.gdi.SelectObject(dc, old_font)
            self.user.ReleaseDC(self.hwnd, dc)
        body = "\n".join(lines)
        if (body, title) != (self.body, self.title):
            self.body, self.title = body, title
            self.user.InvalidateRect(self.hwnd, None, False)

    def destroy(self):
        self.user.DestroyWindow(self.hwnd)

    def run(self, tick):
        self.tick = tick
        if not self.user.SetTimer(self.hwnd, 1, 350, None):
            raise c.WinError(c.get_last_error())
        message = w.MSG()
        try:
            while True:
                result = self.user.GetMessageW(c.byref(message), None, 0, 0)
                if result == -1:
                    raise c.WinError(c.get_last_error())
                if not result:
                    break
                self.user.TranslateMessage(c.byref(message))
                self.user.DispatchMessageW(c.byref(message))
        finally:
            if self.user.IsWindow(self.hwnd):
                self.user.KillTimer(self.hwnd, 1)
                self.user.DestroyWindow(self.hwnd)
            for resource in (self.title_font, self.body_font, self.brush):
                self.gdi.DeleteObject(resource)
            self.user.UnregisterClassW(self.name, self.instance)
