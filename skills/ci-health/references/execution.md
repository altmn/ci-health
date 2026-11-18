# Execution diagnosis and remedies

Read the relevant group after locating the slow interval. Each row is a hypothesis: preserve matched inputs, establish the cause, apply one mechanism, and compare whole-job time, occupied runner-seconds, cost and reliability. A shorter test phase does not establish a faster or cheaper workflow.

## Navigation

| Suspected cause | Read |
|---|---|
| Setup, downloads, caches, containers | [E01–E13](#setup-dependencies-caches-and-containers-e01e13) |
| Sharding, resource pressure, hangs, isolation | [E14–E24](#parallelism-resources-and-runtime-e14e24) |
| Flakes, assertions, affected tests | [E25–E34](#test-signal-and-selection-e25e34) |
| Compilation, services, reports, environment | [E35–E43](#builds-services-and-reporting-e35e43) |
| Mobile, signing, scarce hardware, migrations, benchmarks | [E44–E48](#specialized-environments-e44e48) |
| Tool-specific profiling | [Profiling](#profiling-entry-points) |
| Permission to omit execution or reuse results | [Selection and reuse](selection-and-reuse.md) |

Keep diagnostic profiling separate from ordinary timing samples. Capture the actual command, tested revision, inventory, toolchain/image, resource limits, cache state, seed, exit status and all attempts. Missing telemetry is unknown, not zero. Compare cold/warm and successful/failed/cancelled work separately without excluding their resource cost.

## Setup, dependencies, caches and containers: E01–E13

| ID / symptom | Establish cause; reject misleading explanations | Remedy and validation |
|---|---|---|
| **E01 Setup dominates** | Time boot, checkout, restore, resolution/download, extraction, scripts and test startup; include post-job cache saves. | Batch compatible tiny checks or share preparation only when producer/transfer/consumer cost wins. Preserve verdicts and isolation; compare critical path and total service. |
| **E02 Repeated setup after splitting** | Sum preparation across the complete matrix at equal coverage. A shared prerequisite can create a new delay. | Group compatible trust/platform/dependency work; build once where useful. Measure producer + upload + every download + residual work. |
| **E03 Checkout/fetch is expensive** | Measure bytes, history, LFS, submodules and repeated fetches; identify history-dependent jobs. | Reduce material only while preserving merge-base analysis, versioning and generators. Missing history must trigger broader execution or block, never an empty diff. |
| **E04 Install remains slow on a cache hit** | Distinguish downloaded packages from installed trees; time restore, resolution, linking, scripts and native compilation. | Freeze lockfile/package manager and retain integrity checks. A download-cache hit does not justify skipping installation; `npm ci` removes existing `node_modules` and rejects manifest/lock mismatch. [npm](https://docs.npmjs.com/cli/v11/commands/npm-ci/) |
| **E05 Repeated downloads** | Inspect registry/auth/DNS/TLS failures, retries, rates, eviction and lock churn. Missing platform binaries may cause source builds. | Repair connectivity, use an authorized proxy/store and bounded backoff. Preserve TLS/integrity and verify cold installation. |
| **E06 Cache costs more than rebuilding** | Measure lookup, transfer, compression/extraction, save, validation, residual work and avoided work; include misses. | Shrink/partition entries or remove unhelpful caches. Weight complete hit/miss paths by realistic churn; include storage/request costs without double-counting runner time. |
| **E07 Poor hit rate or thrashing** | Inspect actual keys, branch scope, versions, architecture, eviction and concurrent writers. Relevant input changes should miss. | Remove irrelevant entropy, not true inputs; bound size and retention. GitHub exact hits and prefix restores differ. [GitHub caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) |
| **E08 Stale/poisoned output** | Compare clean output with restoration; perturb config, environment, generated inputs, toolchain and ABI. A successful cache action is insufficient. | Declare complete inputs/outputs, restrict trusted writers and validate provenance. Maintain clean canaries. [Bazel remote caching](https://bazel.build/remote/caching); [reuse qualification](selection-and-reuse.md#cache-and-result-reuse) |
| **E09 Logs restored, outputs missing** | Restore into an empty output directory; local leftovers can hide omitted output globs. | Declare outputs and environment inputs. Verify a clean consumer works; Turborepo assumes determinism for known inputs. [Turborepo](https://turborepo.dev/docs/crafting-your-repository/caching) |
| **E10 Cache trust mistaken for correctness** | Map read/write access for forks and privileged consumers; inspect cached credentials. Hash identity alone is not producer trust. | Exclude secrets, separate untrusted writers from privileged reuse, invalidate suspect entries. GitHub fork PRs can access base-branch caches. [GitHub caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) |
| **E11 Container dependencies rebuild on every edit** | Inspect layer hit status and context bytes; verify early `COPY` changes invalidate expensive descendants. | Put stable dependency manifests before changing source; use suitable cache mounts/external cache and `.dockerignore`. Confirm excluded files are not build inputs. [Docker caching](https://docs.docker.com/build/cache/optimize/) |
| **E12 Image pull/export is slow** | Separate download, unpack, build, compression, push and registry waits. Compressed size alone misses extraction/file-count cost. | Reduce unnecessary content and tune compression. Include prebuilt-image preparation, patching, transfer and storage cost. |
| **E13 Foreign-architecture builds are slow** | Record host/target architecture and emulation. Cross-compiling does not execute target behavior. | Compare native builders/cross-compilation; retain target runtime tests. QEMU can be expensive for compilation and compression. [Docker platforms](https://docs.docker.com/build/building/multi-platform/) |

Cache timing model: `hit = lookup + transfer + extraction + validation + residual work`; `miss = lookup + normal work + save`. Compare their observed weighted mean against uncached execution. A high hit percentage is not itself a performance benefit.

## Parallelism, resources and runtime: E14–E24

| ID / symptom | Establish cause; reject misleading explanations | Remedy and validation |
|---|---|---|
| **E14 Too many shards** | Sum setup and useful work across shards, queue and billing rounding. Tiny/empty shards can waste capacity. | Sweep shard counts at equal coverage; compare required-verdict latency and aggregate cost under actual slot limits. |
| **E15 Stragglers** | Compare useful work excluding queue/setup; inspect historical durations, retries and longest indivisible test/file. Equal counts do not imply balance. | Use fresh compatible timing weights and new-test fallbacks; split long serial work where safe. Playwright file-level versus `fullyParallel` test-level allocation differs. [Sharding](https://playwright.dev/docs/test-sharding) |
| **E16 Incomplete/duplicate shards** | Reconcile discovered, planned and reported IDs per configuration; test missing reports and new/renamed tests. | Fail absent required entries and unintended duplicates. Check pairwise disjointness and complete unions; merge reports without overwrites. [Inventory rules](selection-and-reuse.md#inventory-and-shard-invariants) |
| **E17 Nested oversubscription** | Count co-resident jobs × workers × child/native threads; include browser/DB services. Separate fleet-wide contention from per-machine CPU demand. | Sweep worker limits, reserve service memory/CPU, cap native pools and examine shared DB/API contention. Host core count may exceed the job quota. |
| **E18 CPU throttling** | Inspect cgroup quotas and `cpu.stat` deltas plus profiles. Low average CPU may conceal one saturated thread or bursts. | Align quotas and pools, optimize measured hotspots. [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) |
| **E19 OOM, swap or GC pressure** | Inspect peak memory, cgroup events, GC, swap and termination reason. Exit 137 alone does not prove OOM. | Reduce workers, fix retention/leaks, partition heavy work or raise memory with evidence. A larger language heap cannot bypass container limits; test worst-case workloads. |
| **E20 More cores do not help** | Separate serial CPU, synchronization, I/O and network waits. Runner types also differ in disk, memory and single-core speed. | Optimize the limiting resource; compare repeated whole-job measurements and rates, not core counts. |
| **E21 Slow/full storage** | Inspect bytes, inode count, latency, IOPS, scratch/cache growth and space. Idle CPU can mean I/O waiting. | Reduce writes/unpacking, use suitable scratch storage and bounded retention. Cleanup must not remove another job's files. |
| **E22 Job never exits** | Capture processes, open handles, thread/goroutine dumps, sockets, locks, pending tasks and last progress. | Await work; close resources and children in teardown; use bounded phase/job timeouts with diagnostics. Forced exit alone can hide leaks or lose reports. |
| **E23 Imports/environment dominate tests** | Profile discovery, transforms, imports, setup and assertions separately. Parallel phase sums can exceed wall time. | Narrow broad imports, redundant startup and unnecessary DOM environments. Confirm the same behavior remains tested. [Vitest performance](https://vitest.dev/guide/improving-performance.html) |
| **E24 Isolation removal appears faster** | Run files alone, randomized order, serial and parallel; inspect globals, mocks, timers, env, modules and filesystem state. | First remove redundant setup without weakening isolation. Relax isolation only for qualified subsets; retain isolated audits. One green run is insufficient. |

For divisible work `W`, setup `s`, `n` equal shards and `c` usable slots: service is approximately `n*s + W`; ideal suite wall is `ceil(n/c)*(s + W/n)`. Real queueing, imbalance, retries and merge overhead add to this. More shards may improve latency while increasing resource demand, or worsen both when slots are scarce.

## Test signal and selection: E25–E34

| ID / symptom | Establish cause; reject misleading explanations | Remedy and validation |
|---|---|---|
| **E25 Flakes/retry tax** | Preserve original failure; hold code/environment fixed and vary order, seed, workers or external state. Classify product, test, infrastructure or unknown. | Repair isolation, synchronization and cleanup; bound and count retries. A nondeterministic product defect is not a false alarm. [pytest causes](https://docs.pytest.org/en/stable/explanation/flaky.html) |
| **E26 Sleeps/brittle UI waits** | Inspect readiness transitions and network/locator behavior. Differentiate insufficient timeout from a wrong assertion or broken app. | Use observable readiness and stable locators, isolate data. Blanket timeout growth can only postpone diagnosis. |
| **E27 Retry hides a regression** | Track first-pass separately from final success and preserve failure signatures. Retry success does not identify the cause. | Surface flaky outcomes; repair or use an owned, expiring quarantine with continued execution. [Playwright outcomes](https://playwright.dev/docs/test-retries) |
| **E28 Trace misses first failure** | Check which attempt produced it: `on-first-retry` captures the retry. | Use a supported original-failure retention mode when needed; measure overhead and control artifact access. [Trace options](https://playwright.dev/docs/api/class-testoptions) |
| **E29 Duplicate/weak tests** | Map contract, partitions, errors, platforms and integration boundaries. Names, LOC and covered lines do not prove redundancy. | Consolidate overlap while retaining independent guards; demonstrate realistic fault detection. [Removal evidence](selection-and-reuse.md#test-removal-and-quarantine) |
| **E30 Misleading mutation score** | Inspect survivors, equivalent/invalid mutants, timeouts and denominator changes. Artificial faults need not represent real bugs. | Combine targeted mutations with historical regressions; no deletion quota or universal score threshold. [Stryker outcomes](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/) |
| **E31 Wrong comparison base** | Record base/head and actual tested tree; do not forget changes after a failed prior run. | Fetch required history; choose the base for the event/contract. Nx recommends last successful main validation for its affected CI. [Nx](https://nx.dev/docs/features/ci-features/affected) |
| **E32 Missing dependency edges** | Challenge imports with runtime reads, plugins, fixtures, schemas, generators, config and cross-package consumers. | Add explicit ownership/global invalidators and transitive consumers; uncertainty means broader validation or block. [Selector trials](selection-and-reuse.md#qualify-affected-selection) |
| **E33 Overbroad selection** | Explain each selected owner; a root/lockfile change can legitimately affect nearly everything. | Refine boundaries only with demonstrated independence and shadow evidence. A passing selected test is not inherently irrelevant. |
| **E34 Zero tests reports success** | Inspect discovery, globs, working directory, tags, platform and planner errors. Verified no-op differs from failure. | Validate plan schema/reason/count; broaden or block uncertainty. Do not mask discovery failures with blanket allow-empty options. |

## Builds, services and reporting: E35–E43

| ID / symptom | Establish cause; reject misleading explanations | Remedy and validation |
|---|---|---|
| **E35 Slow types/lint** | Profile the standalone tool, file inclusion, resolution and complex types; distinguish startup from checking. | Fix scope/project boundaries and incremental inputs. Benchmark alternative tools for diagnostic/rule parity; do not silently disable checks. [TypeScript diagnostics](https://github.com/microsoft/TypeScript/wiki/Performance) |
| **E36 Stale incremental state** | Compare clean/incremental outputs after branch, compiler, configuration and dependency changes. | Key compatibility inputs and restore required outputs; retain clean canaries. TypeScript `.tsbuildinfo` is disposable graph state. [TypeScript incremental](https://www.typescriptlang.org/tsconfig/incremental.html) |
| **E37 Repeated compilation** | Inspect DAG, changed inputs, timestamped generators, target/configuration differences and build-before-test/publish duplication. | Declare deterministic inputs/outputs and share exact compatible artifacts; retain all required feature/platform configurations. |
| **E38 Service startup/migrations dominate** | Separate pull, boot, readiness, schema, seed and transactions; inspect locks/pools. | Use immutable templates with isolated per-test state and readiness checks. Preserve migration tests; shared mutable DBs can produce false speedups. |
| **E39 External APIs bottleneck** | Record sanitized endpoint timing, status, retry headers, quota and concurrent callers; distinguish outage from regression. | Use controlled contract tests plus necessary live integration checks; bound concurrency/retries. Do not remove real integration proof without a replacement. |
| **E40 Instrumentation/logging overhead** | Compare matched instrumented/uninstrumented work and output bytes; logging can cause backpressure. | Avoid duplicate coverage for equivalent configurations; sample profiles, retain failure evidence and label diagnostic runs. |
| **E41 Artifact cost/delay** | Time collection, compression, upload/download and retries; measure byte-days. | Scope paths, tune compression and retention by artifact purpose. Keep required release/provenance and failure evidence. |
| **E42 Environment drift** | Compare image, OS, locale/time zone, tools, services, flags and mutable inputs. | Record resolved versions/digests, refresh deliberately and test upgrades. Do not attribute environmental shifts to a code optimization. |
| **E43 Costs moved elsewhere** | Inventory remote builds, cache/registry, image maintenance, developer work and full audits. | Compare all recurring resources and maintenance, preserving detection/latency obligations. Moving a charge does not eliminate it. |

## Specialized environments: E44–E48

| ID / symptom | Establish cause; reject misleading explanations | Remedy and validation |
|---|---|---|
| **E44 Simulator/emulator fanout** | Time image download, boot, install and tests; record devices × shards, memory and `emulator -accel-check`. Allocation failure is not an app failure. | Bound devices, preserve snapshot clean-state behavior; reuse compatible Xcode build-for-testing outputs with test-without-building. Preserve destination/configuration identity. [Android devices](https://developer.android.com/studio/test/gradle-managed-devices), [acceleration](https://developer.android.com/studio/run/emulator-acceleration), [Apple testing](https://developer.apple.com/library/archive/technotes/tn2339/_index.html) |
| **E45 Apple signing/provisioning** | Separate compile, keychain, provisioning and export failures; inspect certificate/profile validity and entitlements before rerunning compilation. | Use appropriate trusted signing lanes and temporary keychains; clean persistent credentials. Simulator success does not qualify release signing. [GitHub Xcode signing](https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications) |
| **E46 GPU/device/license scarcity** | Record request, lease, execution and release; inspect drivers, compatibility and stale leases. Idle CPU may be waiting on scarce hardware. | Admit against inventory, acquire near use, release on cancellation, enforce fair sharing. License constraints are vendor-specific. [Kubernetes GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/), [Jenkins locks](https://plugins.jenkins.io/lockable-resources/) |
| **E47 Migration tests miss upgrades or overload DBs** | Separate locks, setup/data and migration; empty-schema success does not prove supported upgrades or realistic locking. | Use isolated clones and prior schemas; retain invariants and concurrency cases. Universal transaction wrapping is invalid for operations such as PostgreSQL `CREATE INDEX CONCURRENTLY`. [PostgreSQL](https://www.postgresql.org/docs/current/sql-createindex.html) |
| **E48 Benchmark false alarms** | Record hardware, power/thermal/frequency state, load, warmup, cache and instrumentation; repeat matched measurements. Many unadjusted gates amplify false alarms. | Use stable representative environments, practical thresholds and bounded confirmation; label inconclusive data. Android recommends physical devices for CI performance measurement. [Benchmark CI](https://developer.android.com/topic/performance/benchmarking/benchmarking-in-ci), [consistency](https://developer.android.com/topic/performance/benchmarking/microbenchmark-overview) |

## Profiling entry points

Use installed-version options; source documentation can describe a newer release.

| Stack | Start with | Interpretation |
|---|---|---|
| JS/TS | Vitest phases, worker CPU/heap profiles and separate main-thread profile | Main thread and workers explain different work; `--prof` has worker-thread restrictions. [Vitest](https://vitest.dev/guide/profiling-test-performance.html) |
| Python | `pytest --durations=20 --durations-min=0.1`; collect-only manifest | Include fixture setup/teardown; repeat in fresh processes. [pytest](https://docs.pytest.org/en/stable/how-to/usage.html) |
| JVM/Android | Local Gradle profile or appropriately authorized Build Scan | Separate configuration, dependencies and task execution; verify configuration-cache compatibility. [Gradle](https://docs.gradle.org/current/userguide/performance.html) |
| Go | `go test` CPU/heap profiles, pprof and runtime traces | CPU profiles omit waiting; profiling modes can interfere. [Go](https://go.dev/doc/diagnostics) |
| Rust | `cargo build --timings` | Inspect critical-path crates, build scripts, duplicate versions/features and waiting units. [Cargo](https://doc.rust-lang.org/cargo/reference/timings.html) |
| .NET | Diagnostic `-bl:build.binlog` | Binary logs expose inputs/properties and add overhead; redact before sharing. [MSBuild](https://learn.microsoft.com/en-us/visualstudio/msbuild/obtaining-build-logs-with-msbuild?view=vs-2022) |
| Browser | Test timing, original-failure traces, worker sweep | Browser, server and DB share resources; choose measured capacity. [Playwright CI](https://playwright.dev/docs/ci) |

Record each finding as: **ID → observed signal → evidence → rejected alternatives → controlled change → correctness checks → before/after metrics → decision/rollback**. Do not promote a suspected issue to confirmed solely because its suggested fix is common.
