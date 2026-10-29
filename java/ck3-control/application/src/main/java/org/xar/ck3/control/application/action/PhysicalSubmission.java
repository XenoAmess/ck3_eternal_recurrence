package org.xar.ck3.control.application.action;

/** Only the single canonical coordinator constructs one of these private permits after durable SUBMITTING. */
public sealed interface PhysicalSubmission permits PresentationPermit, FrontendWindowCapturePermit { }
