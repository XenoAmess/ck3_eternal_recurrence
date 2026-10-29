package org.xar.ck3.control.contracts;

/** Exact frozen version/SHA pairs. A matching value is not proof that a running process supplied it. */
public enum ExactCk3Build {
    CK3_12004("1.20.0.4", "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518");
    private final String version;
    private final String executableSha256;
    ExactCk3Build(String version, String executableSha256) { this.version = version; this.executableSha256 = executableSha256; }
    public String version() { return version; }
    public String executableSha256() { return executableSha256; }
    public boolean matches(String observedVersion, String observedSha256) {
        return version.equals(observedVersion) && observedSha256 != null && executableSha256.equalsIgnoreCase(observedSha256);
    }
}
