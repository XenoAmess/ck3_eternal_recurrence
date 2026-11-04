"""Native-only first actual isolated validation. Importing this source starts nothing.

One invocation is ONE new mode, with one startup and one real source delta, never a retry.
All outputs are create-only under the exact private D executions root. SourceReady is a
source qualification, not a resource grant; Native supplies and records its fresh reference.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
from http.client import HTTPResponse, HTTPException
import json
import os
import socket
import sys
import threading
import time
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
TEMPLATE_BASE = Path("D:/ck3-state/resume91-root/quarkus-instrumentation-next/owner-revision02/source-frozen01")
FAMILY = ("org/xar/fixture/indexnext/ProbeResource.class",)
NAMES = tuple(name[:-6].replace("/", ".") for name in FAMILY)
FINAL = "Live reload performed via instrumentation, no restart needed"
CAUGHT = "Failed to replace classes via instrumentation"
RESTART = "Restarting quarkus due to changes in"
OLD_NULL = 'Cannot invoke "org.jboss.jandex.ClassInfo.flags()" because "old" is null'

def require(value, message):
    if not value:
        raise RuntimeError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def pin(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def verify_sources(expected_sha):
    ready = HERE / "SOURCE_READY.json"
    require(pin(ready)["sha256"] == expected_sha, "selected SourceReady SHA mismatch")
    document = json.loads(ready.read_text(encoding="utf-8"))
    require(document["state"] == "SOURCE_REVIEW_READY_NOT_EXECUTED", "SourceReady state mismatch")
    for item in document["selected_sources"] + document["readonly_inputs"]:
        actual = pin(item["path"])
        require((actual["bytes"], actual["sha256"]) == (item["bytes"], item["sha256"]), "source/input pin mismatch")
    return document

def free_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as check:
        check.bind(("127.0.0.1", port))
    return True

def http(output, port, nonce, deadline, stop=False):
    remaining = deadline - time.monotonic()
    require(remaining > 0, "phase deadline expired")
    route = "/fixture-index/stop" if stop else "/fixture-index"
    row = {"at_utc": now(), "route": route, "nonce": nonce}
    try:
        # Direct private IPv4 only: no DNS, proxy, redirects or inherited client configuration.
        with socket.create_connection(("127.0.0.1", port), timeout=min(2, remaining)) as connection:
            def deadline_shutdown():
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            timer = threading.Timer(max(0, deadline - time.monotonic()), deadline_shutdown)
            timer.daemon = True
            timer.start()
            try:
                method = "POST" if stop else "GET"
                request = method + " " + route + " HTTP/1.1\r\nHost: 127.0.0.1\r\nX-Fixture-Nonce: " + nonce + "\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
                connection.sendall(request.encode("ascii"))
                with HTTPResponse(connection) as response:
                    response.begin()
                    raw = response.read(131073)
                    require(time.monotonic() <= deadline, "absolute HTTP deadline exceeded")
                    require(len(raw) <= 131072, "private response exceeds bound")
                    row.update(status=response.status, body=raw.decode("utf-8"))
                    if stop:
                        require(response.status == 202, "stop not accepted")
                        return None
                    require(response.status == 200, "probe response not 200; never follow redirects")
                    value = json.loads(row["body"])
                    require(value.get("nonce") == nonce, "wrong fixture nonce; never consume/stop another server")
                    return value
            finally:
                timer.cancel()
    except (OSError, HTTPException, TimeoutError) as error:
        row["error"] = repr(error)
        return None
    finally:
        with (output / "HTTP.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

def text(evidence):
    return "\n".join(path.read_text(encoding="utf-8", errors="replace")
                     for path in (evidence / "stdout.log", evidence / "stderr.log") if path.exists())

def index_rows(directory, nonce, mode):
    rows = []
    for path in directory.glob("index-*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # Java may still be finishing CREATE_NEW write; never accept partial JSON.
        require(value.get("nonce") == nonce and value.get("mode") == mode, "foreign index receipt")
        require(value.get("uses_actual_CombinedIndexBuildItem_getIndex") is True
                and value.get("uses_computing_index") is False, "wrong index capture API")
        require(set(row["name"] for row in value["family"]) == set(NAMES)
                and len(value["family"]) == len(FAMILY), "incomplete/duplicate family receipt")
        rows.append({"file": pin(path), "data": value})
    # UUID filenames do not determine chronology. Initial and later sets are compared by file.
    return rows

def inventory(classes):
    return {str(path.relative_to(classes)).replace("\\", "/"): pin(path)
            for path in classes.rglob("*.class")}

def preserve_classes(classes, output, label):
    # Pins alone cannot let a reviewer independently inspect overwritten BEFORE classes.
    copied = {}
    for source in classes.rglob("*.class"):
        relative = source.relative_to(classes)
        target = output / label / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        require(pin(target)["sha256"] == pin(source)["sha256"], "compiled evidence copy drift")
        copied[str(relative).replace("\\", "/")] = pin(target)
    return copied

def check_probe_identity(value, mode, index_pid=None):
    require(value.get("mode") == mode, "probe mode mismatch")
    require(type(value.get("pid")) is int and value["pid"] > 0, "invalid probe PID")
    require(bool(value.get("start_instant")), "probe birth missing")
    if index_pid is not None:
        require(value["pid"] == index_pid, "probe PID differs from actual augmentation JVM")

def check_probe(value, mode, index_pid=None, expected_body=None, allow_initial_zero=False):
    check_probe_identity(value, mode, index_pid)
    minimum_progress = 0 if allow_initial_zero else 1
    require(value.get("agent_argument") is True and value.get("worker_alive") is True
            and value.get("closed") is False and value.get("failure") is None
            and type(value.get("progress")) is int and value["progress"] >= minimum_progress,
            "unhealthy/uninstrumented fixture probe")
    for key in ("delegate_token", "worker_thread_id", "application_loader_identity",
                "dependency_loader_identity", "enum_loader_identity"):
        require(value.get(key) is not None, "missing probe identity: " + key)
    for key in ("probe_object_identity", "probe_class_identity"):
        require(type(value.get(key)) is int, "integer probe identity required: " + key)
    require(value.get("method_body_value") in ("M7_BODY_V1", "M7_BODY_V2"), "unknown probe body value")
    if expected_body is not None:
        require(value.get("method_body_value") == expected_body, "probe body value mismatch")

def maven_commands(args, output, nonce, indices):
    head = str(output / "repository").replace("\\", "/")
    tails = ",".join(str(path).replace("\\", "/") for path in args.tails)
    common = [args.maven, "-o", "-nsu", "-B", "-ntp", "-s", str(output / "settings.xml"),
              "-gs", str(output / "settings.xml"), "-f", str(output / "reactor/pom.xml"),
              "-Dmaven.repo.local=" + head, "-Dmaven.repo.local.tail=" + tails,
              "-Dmaven.repo.local.tail.ignoreAvailability=false", "-Dmaven.test.skip=true", "-DskipTests=true",
              "-Dquarkus.bootstrap.effective-model-builder=false"]
    # Explicitly compile/package/install the deployment artifact in this NEW private head.
    # No Quarkus augmentation goal is bound to install. It is never counted as a Dev start.
    install = common + ["install"]
    tmp = str(output / "tmp").replace("\\", "/")
    fork = " ".join(["-Xmx512m", "-XX:MaxMetaspaceSize=256m", "-XX:ActiveProcessorCount=1",
                     "-Djava.io.tmpdir=" + tmp, "-Duser.home=" + str(output / "home").replace("\\", "/"),
                     "-Dfixture.nonce=" + nonce,
                     "-Dfixture.mode=" + args.mode, "-Dfixture.base=" + str(output).replace("\\", "/"),
                     "-Dfixture.evidence=" + str(indices).replace("\\", "/"),
                     "-Dmaven.repo.local=" + head, "-Dmaven.repo.local.tail=" + tails,
                     "-Dmaven.repo.local.tail.ignoreAvailability=false"])
    dev = common + ["-pl", "host", "-am", "-DnoDeps=false", "-Ddebug=false",
                    "-Dquarkus.console.enabled=false", "-Dquarkus.test.continuous-testing=disabled",
                    "-Dquarkus.analytics.disabled=true", "-Dquarkus.live-reload.instrumentation=true",
                    "-Dquarkus.http.host=127.0.0.1", "-Dquarkus.http.port=" + str(args.port),
                    "-Djvm.args=" + fork, "compile", "io.quarkus.platform:quarkus-maven-plugin:3.40.1.1:dev"]
    return install, dev

def packaged(output):
    reactor = output / "reactor"
    for module, member, expected in (
        ("diagnostic-runtime", "META-INF/quarkus-extension.properties", TEMPLATE_BASE / "diagnostic-runtime/src/main/resources/META-INF/quarkus-extension.properties"),
        ("diagnostic-deployment", "META-INF/quarkus-build-steps.list", TEMPLATE_BASE / "diagnostic-deployment/src/main/resources/META-INF/quarkus-build-steps.list")):
        jar = reactor / module / "target" / (module + "-1.0.0.jar")
        with zipfile.ZipFile(jar) as archive:
            require(archive.read(member) == expected.read_bytes(), "packaged extension registration drift")
    return [pin(reactor / module / "target" / (module + "-1.0.0.jar"))
            for module in ("diagnostic-runtime", "diagnostic-deployment")]

def snapshot_watched(output):
    reactor = (output / "reactor").resolve()
    modules = ("contracts", "diagnostic-runtime", "diagnostic-deployment", "host")
    paths = {reactor / "pom.xml", reactor / ".mvn/jvm.config", reactor / ".mvn/maven.config"}
    entries = 0
    for module in modules:
        root = reactor / module
        paths.add(root / "pom.xml")
        for resource_root in (root / "src/main/resources", root / "target/classes"):
            if not resource_root.exists():
                continue
            for path in resource_root.rglob("*"):
                entries += 1
                require(entries <= 512, "bounded watched resource traversal required")
                if path.is_file() and not (resource_root.name == "classes" and path.suffix == ".class"):
                    paths.add(path)
    require(len(paths) <= 256, "bounded watched resource count required")
    watched = {}
    total = 0
    for path in sorted(paths):
        require(path.resolve().is_relative_to(reactor), "watched resource escaped private reactor")
        first = path.stat(follow_symlinks=False)
        require(not path.is_symlink() and not (getattr(first, "st_file_attributes", 0) & 0x400),
                "watched resource reparse entry rejected")
        with path.open("rb") as stream:
            data = stream.read(8 * 1024 * 1024 + 1)
        require(len(data) <= 8 * 1024 * 1024, "bounded watched resource bytes required")
        total += len(data)
        require(total <= 16 * 1024 * 1024, "bounded total watched resources required")
        last = path.stat(follow_symlinks=False)
        require((first.st_size, first.st_mtime_ns) == (last.st_size, last.st_mtime_ns)
                and len(data) == last.st_size, "watched resource changed during observation")
        watched[path.relative_to(reactor).as_posix()] = {
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "mtime_ns": last.st_mtime_ns}
    return watched

def literal_payload(raw, target):
    from class_metadata import Reader
    r = Reader(raw)
    require(r.u4() == 0xcafebabe, "UNQUALIFIED: target literal input is not a class")
    r.u2(); r.u2()
    count = r.u2()
    hits = []
    index = 1
    while index < count:
        tag = r.u1()
        if tag == 1:
            length = r.u2()
            offset = r.at
            if r.take(length) == target:
                hits.append([index, offset, length])
        elif tag in (3, 4):
            r.take(4)
        elif tag in (5, 6):
            r.take(8); index += 1
        elif tag in (7, 8, 16, 19, 20):
            r.u2()
        elif tag in (9, 10, 11, 12, 17, 18):
            r.u2(); r.u2()
        elif tag == 15:
            r.u1(); r.u2()
        else:
            raise RuntimeError("UNQUALIFIED: unsupported target constant pool tag " + str(tag))
        index += 1
    require(len(hits) == 1, "UNQUALIFIED: exactly one selected CP UTF8 literal payload required")
    return hits[0]

def validate_class_delta(before, after, classes, old_guards):
    require(set(before) == set(after) and all(name in after for name in FAMILY),
            "UNQUALIFIED: class added/deleted or family missing")
    changed = {name for name in before if before[name]["sha256"] != after[name]["sha256"]}
    require(changed == set(FAMILY), "UNQUALIFIED: unexpected auxiliary change or absent target delta")
    name = FAMILY[0]
    preserved = old_guards[name]["preserved_pin"]
    require(pin(preserved["path"]) == preserved, "preserved BEFORE class drift")
    require((preserved["bytes"], preserved["sha256"]) == (before[name]["bytes"], before[name]["sha256"]),
            "BEFORE inventory and preserved bytes disagree")
    old_raw = Path(preserved["path"]).read_bytes()
    new_raw = (classes / name).read_bytes()
    old_lit = literal_payload(old_raw, b"M7_BODY_V1")
    new_lit = literal_payload(new_raw, b"M7_BODY_V2")
    require(old_lit == old_guards[name]["literal"] and old_lit == new_lit,
            "UNQUALIFIED: literal CP index/offset/length mismatch")
    offset, length = old_lit[1], old_lit[2]
    require(len(b"M7_BODY_V1") == len(b"M7_BODY_V2") == length,
            "UNQUALIFIED: equal literal length required")
    require(old_raw[:offset] + b"M7_BODY_V2" + old_raw[offset + length:] == new_raw,
            "UNQUALIFIED: class differs outside the one CP UTF8 payload")
    return {"changed": sorted(changed), "literal_guard": True, "old_literal": old_lit,
            "new_literal": new_lit, "all_other_class_bytes_exact": True,
            "not_actual_Quarkus_comparator_or_loaded_bytes": True}

def run(args):
    require(sys.flags.isolated and sys.flags.no_site, "Native entry must use Python -I -S before script startup")
    selected = verify_sources(args.source_ready_sha)
    # -I excludes the script directory. Add only this selected, hashed helper directory
    # after verification; -S has prevented .pth/sitecustomize execution at interpreter startup.
    sys.path.insert(0, str(TEMPLATE_BASE))
    sys.path.insert(0, str(HERE))
    from materialize import stage, no_reparse_parents, private_output
    from owned_process import OwnedProcess
    from class_metadata import Reader
    require(os.name == "nt", "Windows Native fixture only")
    require(8100 <= args.port <= 8999 and args.port not in (8089, 8099), "invalid private port")
    require(Path(args.maven).is_file() and Path(args.maven).resolve() == Path("C:/apache-maven/bin/mvn.cmd").resolve(), "exact held Maven entry required")
    require(args.tails and len(args.tails) <= 8, "explicit read-only tails required")
    for path in args.tails:
        require(path.is_dir() and path.drive.lower() == "d:" and not any(char in str(path) for char in ',&|<>^%!()"\r\n '), "invalid explicit D tail")
    require(Path(args.resource_reference).is_file() and Path(args.resource_reference).drive.lower() == "d:", "existing Native fresh-resource reference required")
    # Qualified recipe uses whitespace-free D paths within -Djvm.args and cmd.exe.
    require(not any(char in str(args.output) + args.maven for char in '&|<>^%!()"\r\n '), "unsupported shell/path character")
    started = time.monotonic()
    output = private_output(args.output)
    report = {"schema": "xar.quarkus-index-next.actual-isolated-mode/v1", "mode": args.mode,
              "begin_utc": now(), "selected_source_ready": pin(HERE / "SOURCE_READY.json"),
              "resource_reference": pin(Path(args.resource_reference)), "selected_source_state": selected["state"],
              "limits": {"startup_including_install_s": 180, "scan_s": 90, "cleanup_s": 30, "mode_s": 300},
              "status": "RUNNING", "production_config_or_Game_changed": False}
    nonce = str(uuid.uuid4())
    report["nonce"] = nonce
    # No inherited option/config/RC/proxy/CLASSPATH lanes. Only Windows necessities survive.
    environment = {"SystemRoot": "C:/Windows", "WINDIR": "C:/Windows", "SystemDrive": "C:",
                   "OS": "Windows_NT", "PROCESSOR_ARCHITECTURE": "AMD64", "NUMBER_OF_PROCESSORS": "1"}
    environment.update(PATH="C:/jdk-21/bin;C:/Windows/System32;C:/Windows", PATHEXT=".COM;.EXE;.BAT;.CMD",
                       JAVA_HOME="C:/jdk-21", QUARKUS_LOCAL_REPO=str(output / "repository"), MAVEN_SKIP_RC="1",
                       MAVEN_BASEDIR=str(output / "reactor"), MAVEN_USER_HOME=str(output / "home/.m2"),
                       USERPROFILE=str(output / "home"), HOMEDRIVE="D:", HOMEPATH=str(output / "home")[2:],
                       APPDATA=str(output / "home/AppData/Roaming"), LOCALAPPDATA=str(output / "home/AppData/Local"),
                       MAVEN_OPTS="-Xmx512m -XX:ActiveProcessorCount=1 -Djava.io.tmpdir=" + str(output / "tmp") + " -Duser.home=" + str(output / "home"),
                       # The exact held mvn.cmd also invokes java -version without MAVEN_OPTS.
                       # This newly constructed launcher lane constrains that JVM as well; no inherited value survives.
                       JDK_JAVA_OPTIONS="-Xmx512m -XX:MaxMetaspaceSize=256m -XX:ActiveProcessorCount=1 -Djava.io.tmpdir=" + str(output / "tmp") + " -Duser.home=" + str(output / "home"),
                       TEMP=str(output / "tmp"), TMP=str(output / "tmp"))
    report["launch_environment"] = environment
    process = None
    baseline = None
    cleanup_owner = None
    observed = None
    main_error = None
    startup_end = started + 180
    try:
        stage(output, args.mode)
        indices = output / "indices"
        indices.mkdir()
        (output / "repository").mkdir()
        (output / "tmp").mkdir()
        for relative in ("home", "home/AppData/Roaming", "home/AppData/Local"):
            (output / relative).mkdir(parents=True, exist_ok=True)
        for directory in (output, indices, output / "repository", output / "tmp", output / "home"):
            no_reparse_parents(directory)
        install, dev = maven_commands(args, output, nonce, indices)
        free_port(args.port)
        install_evidence = output / "install"
        install_evidence.mkdir()
        save(install_evidence / "BEGIN.json", {"at_utc": now(), "command": install, "repo_head": str(output / "repository"), "tails": [str(path) for path in args.tails]})
        process = OwnedProcess(install, output / "reactor", environment, install_evidence, str(uuid.uuid4()), startup_end)
        while process.poll() is None and time.monotonic() < startup_end:
            time.sleep(0.1)
        require(process.poll() == 0, "SOURCE_STOP: private offline install failed or startup budget exhausted")
        save(install_evidence / "END.json", {"at_utc": now(), "exit_code": process.poll(), "cleanup": process.close(2)})
        process = None
        require(not list(indices.iterdir()), "unexpected augmentation during ordinary install")
        report["packaged_registration"] = packaged(output)
        require(time.monotonic() < startup_end, "SOURCE_STOP: startup budget exhausted before new Dev launch")
        dev_evidence = output / "dev"
        dev_evidence.mkdir()
        save(dev_evidence / "BEGIN.json", {"at_utc": now(), "command": dev, "nonce": nonce, "port": args.port})
        process = OwnedProcess(dev, output / "reactor", environment, dev_evidence, nonce, startup_end)
        initial = None
        while time.monotonic() < startup_end:
            require(process.poll() is None, "SOURCE_STOP: Dev exited before ready")
            rows = index_rows(indices, nonce, args.mode)
            require(len(rows) <= 1, "multiple augmentations before the single source delta")
            if rows and "Profile dev activated." in text(dev_evidence):
                value = http(output, args.port, nonce, startup_end)
                if value:
                    check_probe_identity(value, args.mode, rows[0]["data"]["pid"])
                    cleanup_owner = value  # Cleanup identity grants no baseline or progress credit.
                    check_probe(value, args.mode, rows[0]["data"]["pid"], "M7_BODY_V1", allow_initial_zero=True)
                    if value["progress"] > 0:
                        initial, baseline = rows[0], value
                        break
            time.sleep(min(0.25, max(0, startup_end - time.monotonic())))
        require(initial is not None, "SOURCE_STOP: no actual Dev index+owned healthy delegate before deadline")
        present = [row["present"] is True for row in initial["data"]["family"]]
        require(all(present), "initial index invalidates positive mode; never fabricate missing entries")
        report.update(initial_index=initial, baseline=baseline)
        classes = output / "reactor/host/target/classes"
        before = inventory(classes)
        require(all(name in before for name in FAMILY), "initial compiled family absent")
        preserved_before = preserve_classes(classes, output, "compiled-before")
        old_guards = {name: {"preserved_pin": preserved_before[name],
                            "literal": literal_payload(Path(preserved_before[name]["path"]).read_bytes(), b"M7_BODY_V1")}
                      for name in FAMILY}
        source = output / "reactor/host/src/main/java/org/xar/fixture/indexnext/ProbeResource.java"
        candidate = output / "delta/ProbeResource.body-delta.java"
        require(pin(source)["sha256"] == pin(HERE / "ProbeResource.java")["sha256"], "source-before drift")
        require(pin(candidate)["sha256"] == pin(HERE / "ProbeResource.body-delta.java")["sha256"], "candidate drift")
        source_before = source.read_bytes()
        delta_source = candidate.read_bytes()
        require(source_before.count(b"M7_BODY_V1") == 1 and b"M7_BODY_V2" not in source_before
                and source_before.replace(b"M7_BODY_V1", b"M7_BODY_V2") == delta_source,
                "only the selected one-literal source delta is admitted")
        save(output / "BEFORE.json", {"at_utc": now(), "classes": before,
                                      "preserved_classes": preserved_before,
                                      "literal_class_guard_baseline": old_guards, "source": pin(source)})
        log_before_delta = text(dev_evidence)
        require(FINAL not in log_before_delta and RESTART not in log_before_delta and CAUGHT not in log_before_delta,
                "unexpected reload before the single declared source delta")
        # Snapshot watched resources before delta
        watched_before = snapshot_watched(output)
        save(output / "WATCHED-BEFORE.json", {"at_utc": now(), "resources": watched_before})
        source.write_bytes(delta_source)
        os.utime(source, None)
        save(output / "SOURCE-DELTA.json", {"at_utc": now(), "source": pin(source), "mtime_ns": source.stat().st_mtime_ns})
        scan_end = min(time.monotonic() + 90, started + 270)
        while time.monotonic() < scan_end:
            require(process.poll() is None, "Dev exited during scan")
            value = http(output, args.port, nonce, scan_end)
            if value:
                check_probe(value, args.mode, baseline["pid"])
                require(value["start_instant"] == baseline["start_instant"], "scan probe host birth changed")
            log = text(dev_evidence)
            rows = index_rows(indices, nonce, args.mode)
            if FINAL in log:
                if value and value["method_body_value"] == "M7_BODY_V2" and value["progress"] > baseline["progress"]:
                    observed = value
                    break
            time.sleep(min(0.25, max(0, scan_end - time.monotonic())))
        require(observed is not None, "scan deadline without qualified after delegate")
        require(observed["pid"] == baseline["pid"] and observed["start_instant"] == baseline["start_instant"], "host PID/birth changed")
        check_probe(observed, args.mode, baseline["pid"], "M7_BODY_V2")
        after = inventory(classes)
        report["class_delta"] = validate_class_delta(before, after, classes, old_guards)
        report["compiled_after"] = after
        report["preserved_compiled_after"] = preserve_classes(classes, output, "compiled-after")
        report["after"] = observed
        log = text(dev_evidence)
        rows = index_rows(indices, nonce, args.mode)
        report["index_receipts"] = rows
        # Verify watched resources unchanged
        watched_after = snapshot_watched(output)
        save(output / "WATCHED-AFTER.json", {"at_utc": now(), "resources": watched_after})
        require(watched_before == watched_after, "UNQUALIFIED: watched resource bytes/mtime changed")
        report["watched_resources"] = {"before": watched_before, "after": watched_after}
        identities = ("application_loader_identity", "dependency_loader_identity", "enum_loader_identity", "delegate_token", "worker_thread_id", "probe_object_identity", "probe_class_identity")
        require(FINAL in log and RESTART not in log and CAUGHT not in log and "INDEX_NEXT_DELEGATE_CLOSED" not in log, "positive restart/failure/close or missing final instrumentation")
        require(len(rows) == 1 and rows[0]["file"] == initial["file"], "positive old CombinedIndex was replaced")
        require(all(observed[key] == baseline[key] for key in identities), "positive identity changed")
        require(log.count("INDEX_NEXT_DELEGATE_CREATED token=" + baseline["delegate_token"]) == 1, "positive delegate creation count")
        report["outcome"] = "ACTUAL_DEV_POSITIVE_BODY_RETURN_AND_OBSERVABLE_IDENTITY_INSTRUMENTATION"
        save(output / "OBSERVATION.json", {"at_utc": now(), "outcome": report["outcome"], "baseline": baseline, "after": observed})
        report["status"] = "OBSERVED_PENDING_CLEANUP"
    except BaseException as error:
        main_error = error
        report["status"] = ("SOURCE_STOP" if "SOURCE_STOP" in str(error) else
                            "UNQUALIFIED" if isinstance(error, RuntimeError) and str(error).startswith("UNQUALIFIED:") else
                            "FAILED")
        report["first_error"] = {"type": type(error).__name__, "message": str(error), "at_utc": now(),
                                 "notes": [str(note)[:8192] for note in getattr(error, "__notes__", ())[:16]]}
    finally:
        cleanup_started = time.monotonic()
        cleanup_end = min(cleanup_started + 30, started + 300)
        cleanup = {"begin_utc": now()}
        try:
            if process:
                cleanup_identity = baseline if baseline is not None else cleanup_owner
                if cleanup_identity is not None:
                    current = http(output, args.port, nonce, min(cleanup_end, time.monotonic() + 2))
                    if current:
                        check_probe_identity(current, args.mode, cleanup_identity["pid"])
                        require(current["start_instant"] == cleanup_identity["start_instant"], "cleanup ownership changed")
                        http(output, args.port, nonce, min(cleanup_end, time.monotonic() + 2), stop=True)
                        while process.poll() is None and time.monotonic() < min(cleanup_end - 4, cleanup_started + 8):
                            time.sleep(0.1)
        except BaseException as error:
            cleanup["graceful_error"] = repr(error)
        finally:
            try:
                if process:
                    cleanup["contained_process"] = process.close(max(0.1, min(4, cleanup_end - time.monotonic())))
                free_port(args.port)
                cleanup["private_port_free"] = True
                if observed:
                    final_log = text(output / "dev")
                    cleanup["last_delegate_closed_exactly_once"] = final_log.count("INDEX_NEXT_DELEGATE_CLOSED token=" + observed["delegate_token"]) == 1
                    require(cleanup["last_delegate_closed_exactly_once"], "last owned delegate close was not observed exactly once")
                require(time.monotonic() <= started + 300, "mode total budget exceeded")
            except BaseException as error:
                cleanup["error"] = repr(error)
                report["status"] = "FAILED_CLEANUP"
            cleanup.update(end_utc=now(), seconds=time.monotonic() - cleanup_started)
            report.update(cleanup=cleanup, end_utc=now(), total_wall_seconds=time.monotonic() - started,
                          actual_Java_or_Dev_instrumentation_credit_only_from_this_receipt=True,
                          production_missing_FQN_and_loaded_hash="UNKNOWN")
            if report["status"] == "OBSERVED_PENDING_CLEANUP":
                report["status"] = "OBSERVED_THIS_MODE_AND_CLEANED"
            if output.is_dir():
                save(output / "TERMINAL.json", report)
            else:
                print(json.dumps(report))  # Native outer receipt preserves pre-materialization failure.
    print(json.dumps({"terminal": pin(output / "TERMINAL.json") if (output / "TERMINAL.json").is_file() else None, "status": report["status"]}))
    return 0 if report["status"] == "OBSERVED_THIS_MODE_AND_CLEANED" and main_error is None else 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("positive",), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maven", required=True)
    parser.add_argument("--tail", dest="tails", action="append", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--source-ready-sha", required=True)
    parser.add_argument("--resource-reference", required=True)
    return run(parser.parse_args())

if __name__ == "__main__":
    raise SystemExit(main())
