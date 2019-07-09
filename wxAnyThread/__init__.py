from future.utils import raise_with_traceback
import wx
import sys
import threading

_EVT_INVOKE_METHOD = wx.NewId()

class MethodInvocationEvent(wx.PyEvent):
    """Event fired to the GUI thread indicating a method invocation."""

    def __init__(self, func, args, kwds):
        wx.PyEvent.__init__(self)
        self.SetEventType(_EVT_INVOKE_METHOD)
        self.func = func
        self.args = args
        self.kwds = kwds
        self.event = threading.Event()

    def invoke(self):
        """Invoke the method, blocking until the main thread handles it."""
        wx.PostEvent(self.args[0],self)
        self.event.wait()
        try:
            return self.result
        except AttributeError:
            tb = self.traceback
            del self.traceback
            e = type(self.exception)(self.exception)
            raise_with_traceback(e, tb)

    def process(self):
        """Execute the method and signal that it is ready."""
        try:
            self.result = self.func(*self.args, **self.kwds)
        except Exception:
            _, self.exception, self.traceback = sys.exc_info()
        self.event.set()


def handler(evt):
    """Simple event handler to register for invocation events."""
    evt.process()


def anythread(func):
    """Method decorator allowing call from any thread.

    The method is replaced by one that posts a MethodInvocationEvent to the
    object, then blocks waiting for it to be completed.  The target object
    is automatically connected to the _EVT_INVOKE_METHOD event if it wasn't
    alread connected.

    When invoked from the main thread, the function is executed immediately.
    """
    def invoker(*args, **kwds):
        if wx.Thread_IsMain():
            return func(*args, **kwds)
        else:
            self = args[0]
            if not hasattr(self,"_AnyThread__connected"):
                self.Connect(-1, -1, _EVT_INVOKE_METHOD, handler)
                self._AnyThread__connected = True
            evt = MethodInvocationEvent(func, args, kwds)
            return evt.invoke()
    invoker.__name__ = func.__name__
    invoker.__doc__ = func.__doc__
    return invoker
