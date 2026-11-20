package org.xar.ck3.control.contracts;

/** Exact frozen version/SHA pairs. A matching value is not proof that a running process supplied it. */
public enum ExactCk3Build {
    CK3_12004("1.20.0.4", "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"),
    CK3_1210("1.21.0", "2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc"),
    CK3_1210_STEAM_26757580("1.21.0", "bb3fef106240e95ecdb6f1532982e89e9432c92a99d33db623521572f06e6f79"),
    CK3_121003_STEAM_26785313("1.21.0.3", "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28"),
    /** Independent Full111 profile DATA. The matching executable alone never selects this profile or grants a live source. */
    CK3_121003_STEAM_26785313_FULL111("1.21.0.3", "859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28");
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
    /** Explicit complete tuple DATA. The legacy two-argument selector deliberately does not admit Full111. */
    public static java.util.Optional<ExactCk3Build> florinCoreFullBuild(String version,String sha256,String adapterId) {
        for(var build:java.util.List.of(CK3_1210,CK3_1210_STEAM_26757580,CK3_121003_STEAM_26785313_FULL111))
            if(build.matches(version,sha256)&&build.coreFullAdapterId().equals(adapterId))return java.util.Optional.of(build);
        return java.util.Optional.empty();
    }
    /** Core DATA identity only. Full/clock/domain callers must keep using florinCoreFullBuild. */
    public static java.util.Optional<ExactCk3Build> florinCoreFrameBuild(String version,String sha256) {
        if(CK3_121003_STEAM_26785313.matches(version,sha256))
            return java.util.Optional.of(CK3_121003_STEAM_26785313);
        return florinCoreFullBuild(version,sha256);
    }
    /** A Core result remains partial even when its exact producer is the independent Full111 profile. */
    public static java.util.Optional<ExactCk3Build> florinCoreFrameBuild(String version,String sha256,String adapterId) {
        var full=florinCoreFullBuild(version,sha256,adapterId);
        if(full.isPresent())return full;
        return florinCoreFrameBuild(version,sha256).filter(build->build.coreFrameAdapterId().equals(adapterId));
    }
    public String coreFrameAdapterId() {
        return this==CK3_121003_STEAM_26785313?"ck3-1.21.0.3-26785313-msvc-x64":coreFullAdapterId();
    }
    public String coreFullAdapterId() {
        if(this==CK3_121003_STEAM_26785313)throw new IllegalStateException("26785313 has only a partial Core profile");
        if(this==CK3_121003_STEAM_26785313_FULL111)return "ck3-1.21.0.3-26785313-full111-msvc-x64";
        return this==CK3_1210_STEAM_26757580?"ck3-1.21.0-26757580-msvc-x64":"ck3-"+version+"-msvc-x64";
    }
    public String coreFullBackend() {
        coreFullAdapterId(); // A Core-only identity cannot supply a Full tuple.
        return "ck3-"+version+"-native-headless-main-thread";
    }
    public boolean matches(String observedVersion, String observedSha256) {
        return version.equals(observedVersion) && observedSha256 != null && executableSha256.equalsIgnoreCase(observedSha256);
    }
}
