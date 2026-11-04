"""Create-only source preparation. No process, import of the runner, socket or HTTP."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
TEMPLATE_BASE = Path("D:/ck3-state/resume91-root/quarkus-instrumentation-next/owner-revision02/source-frozen01")
ROOT = Path("D:/ck3-state/resume91-root/quarkus-instrumentation-next")
EXECUTIONS = ROOT / "native-executions"
PINNED_INPUTS = {
    "inputs/07-BEFORE.java": (6355, "973077d9405701c497d86528b9c8dacbe322f3f2bfd269a667de87659ab88c50"),
    "fulljson-support/StrictJson.java": (14844, "a6c185770b920e45107e046235ee0dcb098ab538b532e3f49e94d9e8f93f79d2"),
    "fulljson-support/DecimalTokenNode.java": (3400, "dcfaa1f41e5dba568e21d61103197827c26704e3e386da48077a8a159812b9df"),
    "fulljson-support/ContractViolationException.java": (348, "ed14dfab6bf95bf2c0b0361f8302de520179e02788e60a6ba4b3d2ad3e04ddd9"),
}
TEMPLATES = ["pom.xml", "contracts/pom.xml", "diagnostic-runtime/pom.xml",
             "diagnostic-deployment/pom.xml", "host/pom.xml",
             "diagnostic-runtime/src/main/resources/META-INF/quarkus-extension.properties",
             "diagnostic-deployment/src/main/resources/META-INF/quarkus-build-steps.list"]

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def pin(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def input_bytes(relative):
    path = ROOT / relative
    actual = pin(path)
    require((actual["bytes"], actual["sha256"]) == PINNED_INPUTS[relative], "input pin mismatch: " + relative)
    return path.read_bytes()

def private_output(path):
    requested = Path(path).absolute()
    require(requested.drive.lower() == "d:" and requested.is_relative_to(EXECUTIONS.absolute())
            and requested != EXECUTIONS.absolute(), "lexical private D output required")
    no_reparse_parents(requested)
    actual = requested.resolve()
    require(actual.drive.lower() == "d:" and actual.is_relative_to(EXECUTIONS.resolve())
            and actual != EXECUTIONS.resolve(), "output must be a new child of the exact private D executions root")
    require(not actual.exists(), "output already exists; no retries or overwritten evidence")
    return actual

def no_reparse_parents(path):
    for ancestor in [*Path(path).parents, Path(path)]:
        if ancestor.exists():
            attributes = getattr(ancestor.stat(follow_symlinks=False), "st_file_attributes", 0)
            require(not ancestor.is_symlink() and not (attributes & 0x400), "reparse/symlink parent forbidden: " + str(ancestor))

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    require(path.read_bytes() == data, "post-copy byte drift")
    return pin(path)

def stage(output, mode):
    require(mode == "positive", "only positive mode supported")
    output = private_output(output)
    # Validate every original before making the first output leaf.
    originals = {name: input_bytes(name) for name in PINNED_INPUTS}
    baseline = (HERE / "ProbeResource.java").read_bytes()
    delta = (HERE / "ProbeResource.body-delta.java").read_bytes()
    require(baseline.count(b"M7_BODY_V1") == 1 and b"M7_BODY_V2" not in baseline
            and baseline.replace(b"M7_BODY_V1", b"M7_BODY_V2") == delta,
            "only the selected one-literal source delta is admitted")
    output.mkdir(parents=True, exist_ok=False)
    no_reparse_parents(output)
    reactor = output / "reactor"
    copied = []
    for name in TEMPLATES:
        template = (TEMPLATE_BASE / name).read_bytes()
        if name == "host/pom.xml":
            require(template.count(b"</project>\n") == 1, "exact host POM closing tag required")
            template = template.replace(b"</project>\n", b'  <build><plugins>\n    <plugin>\n      <groupId>io.quarkus.platform</groupId>\n      <artifactId>quarkus-maven-plugin</artifactId>\n      <version>3.40.1.1</version>\n      <configuration><enforceBuildGoal>false</enforceBuildGoal></configuration>\n    </plugin>\n  </plugins></build>\n</project>\n')
        copied.append(put(reactor / name, template))
    copied.append(put(reactor / "host/src/main/resources/application.properties",
                      (TEMPLATE_BASE / "application-positive.properties").read_bytes()))
    # Prevent mvn.cmd's ancestor search and Maven's user configuration from escaping this fixture.
    copied.append(put(reactor / ".mvn/jvm.config", b""))
    copied.append(put(reactor / ".mvn/maven.config", b""))
    copied.append(put(output / "settings.xml", b'<settings xmlns="http://maven.apache.org/SETTINGS/1.2.0"/>\n'))
    package = "src/main/java/org/xar/ck3/control/contracts/"
    for name in ("StrictJson.java", "DecimalTokenNode.java", "ContractViolationException.java"):
        copied.append(put(reactor / "contracts" / package / name, originals["fulljson-support/" + name]))
    copied.append(put(reactor / "contracts" / package / "FullJsonTree.java", originals["inputs/07-BEFORE.java"]))
    copied.append(put(reactor / "diagnostic-deployment/src/main/java/org/xar/fixture/indexnext/IndexCapture.java",
                      (HERE / "IndexCapture.java").read_bytes()))
    copied.append(put(reactor / "host/src/main/java/org/xar/fixture/indexnext/ProbeResource.java",
                      (HERE / "ProbeResource.java").read_bytes()))
    copied.append(put(output / "delta/ProbeResource.body-delta.java",
                      (HERE / "ProbeResource.body-delta.java").read_bytes()))
    put(output / "MATERIALIZED.json", (json.dumps({"mode": mode, "copied": copied}, indent=2) + "\n").encode())
    return output
