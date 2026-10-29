package org.xar.ck3.control.application.action;

/** Durable identity DATA; only the identical installed source preparer may admit an explicit protocol ID. */
public sealed interface ProtocolRequestIdentity permits ProtocolRequestIdentity.BodyDerived, ExplicitOriginalProtocolId {
    enum BodyDerived implements ProtocolRequestIdentity { INSTANCE }
}
