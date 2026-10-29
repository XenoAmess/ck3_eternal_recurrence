package org.xar.ck3.control.contracts.projection;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import org.xar.ck3.control.build.ProjectionArtifactAuthority.Context;
import org.xar.ck3.control.build.ProjectionArtifactAuthority.Lease;
import org.xar.ck3.control.build.ProjectionArtifactAuthority.Scope;

/** Compatibility entrypoints delegate to the sole primitive authority codec; no second field inventory. */
public final class ProjectionArtifactInputCodec {
    private ProjectionArtifactInputCodec() { }
    public static Scope decodeScope(byte[] raw) { return ProjectionArtifactAuthority.decodeScope(raw); }
    public static Lease decodeLease(byte[] raw) { return ProjectionArtifactAuthority.decodeLease(raw); }
    public static Context decodeContext(byte[] raw) { return ProjectionArtifactAuthority.decodeContext(raw); }
    public static byte[] encodeScope(Scope scope) { return ProjectionArtifactAuthority.encodeScope(scope); }
    public static byte[] encodeLease(Lease lease) { return ProjectionArtifactAuthority.encodeLease(lease); }
    public static byte[] encodeContext(Context context) { return ProjectionArtifactAuthority.encodeContext(context); }
    public static ObjectNode scope(Scope scope) { return ProjectionArtifactAuthority.scope(scope); }
}
