package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.presentation.TransportKind;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;

/** Closed physical planes. A mmap or window request is never a Native pipe packet. */
public sealed interface PreparedAction permits PreparedAction.PipeRequest, PreparedAction.MmapRequest, PreparedAction.WindowCaptureRequest {
    String requestId();
    TransportKind transportKind();
    List<ExactRef> preparationEvidence();
    record PipeRequest(String requestId, NativeRequest value) implements PreparedAction {
        public PipeRequest { org.xar.ck3.control.contracts.StrictJson.text(requestId); Objects.requireNonNull(value); }
        public TransportKind transportKind() { return TransportKind.NATIVE_PIPE; }
        public List<ExactRef> preparationEvidence() { return value.preparationEvidence(); }
    }
    record MmapRequest(PresentationRequest value) implements PreparedAction {
        public MmapRequest { Objects.requireNonNull(value); }
        public String requestId() { return value.requestId(); }
        public TransportKind transportKind() { return TransportKind.PRESENTATION_MMAP; }
        public byte[] encode() { return value.encode(); }
        public List<ExactRef> preparationEvidence() { return value.preparationEvidence(); }
    }
    record WindowCaptureRequest(FrontendWindowCaptureRequest value) implements PreparedAction {
        public WindowCaptureRequest { Objects.requireNonNull(value); }
        public String requestId() { return value.requestId(); }
        public TransportKind transportKind() { return TransportKind.WIN32_FRONTEND_CAPTURE; }
        public byte[] encode() { return value.encode(); }
        public List<ExactRef> preparationEvidence() { return value.preparationEvidence(); }
    }
}
