package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import org.xar.ck3.control.contracts.presentation.TransportKind;

/** Physical custody only. Posted and a window activation result never imply Game or rendered completion. */
public sealed interface PhysicalOutcome permits PhysicalOutcome.PipeOutcome, PhysicalOutcome.MmapOutcome, PhysicalOutcome.WindowCaptureOutcome {
    String requestId();
    TransportKind transportKind();
    record PipeOutcome(NativeActionPort.DispatchOutcome value) implements PhysicalOutcome {
        public PipeOutcome { Objects.requireNonNull(value); }
        public String requestId() { return value.requestId(); }
        public TransportKind transportKind() { return TransportKind.NATIVE_PIPE; }
    }
    record MmapOutcome(OriginalOutcome value) implements PhysicalOutcome {
        public MmapOutcome { Objects.requireNonNull(value); }
        public String requestId() { return value.request().requestId(); }
        public TransportKind transportKind() { return TransportKind.PRESENTATION_MMAP; }
    }
    record WindowCaptureOutcome(FrontendWindowCaptureOutcome value) implements PhysicalOutcome {
        public WindowCaptureOutcome { Objects.requireNonNull(value); }
        public String requestId() { return value.requestId(); }
        public TransportKind transportKind() { return TransportKind.WIN32_FRONTEND_CAPTURE; }
    }
}
