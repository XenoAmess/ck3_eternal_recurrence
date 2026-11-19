package org.xar.ck3.control.contracts;

/** Exact frozen version/SHA pairs. A matching value is not proof that a running process supplied it. */
public enum ExactCk3Build {
    CK3_12004("1.20.0.4", "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"),
    CK3_1210("1.21.0", "2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc"),
    CK3_1210_STEAM_26757580("1.21.0", "bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79");
    private final String version;
    private final String executableSha256;
    ExactCk3Build(String version, String executableSha256) { this.version = version; this.executableSha256 = executableSha256; }
    public String version() { return version; }
    public String executableSha256() { return executableSha256; }
    /** Exact identity DATA for the two separately reviewed Florin Core/Full profiles; no other capability is admitted. */
    public static java.util.Optional<ExactCk3Build> florinCoreFullBuild(String version,String sha256) {
        for(var build:java.util.List.of(CK3_1210,CK3_1210_STEAM_26757580))
            if(build.matches(version,sha256))return java.util.Optional.of(build);
        return java.util.Optional.empty();
    }
    public String coreFullAdapterId() {
        return this==CK3_1210_STEAM_26757580?"ck3-1.21.0-26757580-msvc-x64":"ck3-"+version+"-msvc-x64";
    }
    public boolean matches(String observedVersion, String observedSha256) {
        return version.equals(observedVersion) && observedSha256 != null && executableSha256.equalsIgnoreCase(observedSha256);
    }
}
