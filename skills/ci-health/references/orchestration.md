# Orchestration and capacity investigations

Load this reference when work starts too often, queues grow, capacity sits idle, required checks behave incorrectly, or feedback arrives late. Treat O1–O18 as hypotheses. Record evidence, rejected explanations, remedy, and validation under the relevant ID. A symptom does not establish a defect.

## Find the constrained stage

Trace: source event → admission → prerequisites/approval → eligible queue → allocation → setup → useful work → reports → valid verdict. Keep PR, merge-group, scheduled and release work distinct.

For each compatible runner pool, collect arrivals/completions per interval, eligible backlog and oldest age, usable/idle/offline slots, occupied seconds/job, retries, cancellation stage, and required-verdict p50/p95. Completed jobs alone hide unfinished work.

For an approximately homogeneous pool, `offered load ≈ arrival rate × mean occupied seconds / usable slots`, with consistent units. Sustained demand above capacity cannot drain without demand reduction or capacity recovery. Idle workers of another OS, architecture or trust class are not interchangeable capacity. Near-full utilization offers little headroom for bursts; average utilization is not a latency guarantee.

| Observation | Read first |
|---|---|
| More work per revision | O1, O3, O5, O16 |
| Growing eligible queue, idle machines | O13, O14, O15 |
| Long elapsed time, little execution | O7, O17 |
| Missing checks or unexpected green | O2, O4, O8, O18 |
| Stale or inconsistent evidence | O6, O9, O11 |
| Failures after configuration/trust changes | O10, O12 |

## O1. Duplicate events and workflow families

- **Prove:** group by repository, tested tree, head/base, workflow hash, event, PR, matrix and attempt; compare commands and contracts. Trace bots, API dispatch and reusable-workflow callers.
- **Disprove:** PR-head, synthetic-merge, merge-group and release checks can prove different facts despite similar inputs.
- **Resolve:** give each contract an event owner; gate redundant work before allocation. Reuse reviews only with matching diff/base/context/policy/tool identity and freshness.
- **Validate:** branch, PR update, base update, fork, tag, queue, schedule and manual cases produce every expected check. GitLab specifically documents push/MR duplication from broad rules. [GitLab rules](https://docs.gitlab.com/ci/jobs/job_rules/)

## O2. Required checks missing or falsely green

- **Prove:** inspect live rulesets, check names/app identity, trigger event, tested SHA, `needs`, and every prerequisite outcome.
- **Disprove:** a workflow-level skip and a job-level skip have different semantics. GitHub can leave a skipped workflow pending while a conditional job skip reports success. Manual-dispatch workflow-job checks can be ineligible for PR rules; external App checks differ. [Required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
- **Resolve:** stable aggregate explicitly validates required results or authorized, evidenced not-applicable states. Missing planner output/report is not success.
- **Validate:** failing test, crashed planner, cancelled prerequisite, absent shard and unintended zero discovery must prevent a valid green gate.

## O3. Incomplete path filters or impact selection

- **Prove:** retain base/head, complete diff, selector version, selected/omitted manifests and reasons. Inspect pagination, renames/deletions, global config, lockfiles, schemas, fixtures and dynamic imports.
- **Disprove:** empty diff can mean missing history/query failure; documentation can be executable input.
- **Resolve:** conservative fallback or block on uncertainty; explicit global invalidators; shadow before enforcement.
- **Validate:** historical faults, boundary mutations and full/selected comparisons. Recheck provider diff limits; never assume an API returned every changed file. [GitHub path-filter semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#git-diff-comparisons)

## O4. Merge queue checks the wrong tree or rebuilds excessively

- **Prove:** map group SHA, base and constituent PRs; verify checkout; classify invalidations from reorder, failure, timeout and base movement.
- **Disprove:** combined-tree testing is distinct from PR-head testing; merge-queue wait is not necessarily runner wait.
- **Resolve:** configure required GitHub Actions checks for `merge_group`; handle queue refs with external CI. Tune group size/concurrency and limit unnecessary queue jumps.
- **Validate:** individually passing but conflicting changes fail combined validation on the group SHA. [Merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

## O5. Cancellation churn or cross-cancellation

- **Prove:** evaluate concurrency keys and trace request → termination → release → external cleanup; inspect workflow/job/caller scopes.
- **Disprove:** cancelled work already consumed resources; safely superseded PR work differs from a noninterruptible migration.
- **Resolve:** scope groups by purpose and PR/ref; cancel only safe obsolete work; separate promotion serialization; expire resource leases.
- **Validate:** rapid pushes, unrelated PRs, reruns and cancellation during setup/test/upload. Include debounce delay in feedback time. Recheck queue/replacement behavior and case-insensitive keys. [Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)

## O6. Scheduled validation loses freshness

- **Prove:** record latest fully qualified revision, oldest unvalidated change, missed runs, detection latency and owner.
- **Disprove:** unchanged source does not imply unchanged scanner policy, intelligence or external services; configured cron is not guaranteed execution.
- **Resolve:** separate pre-merge/post-merge/pre-release obligations; immutable result identity; freshness deadline, independent watchdog and fallback.
- **Validate:** missed schedule, tool/policy change and stale release evidence are detected. GitHub schedules may be delayed/dropped and execute on the default branch. [Schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

## O7. Unnecessary DAG edges or held resources

- **Prove:** reconstruct prerequisites, readiness, approvals, allocation, service readiness and lock intervals.
- **Disprove:** an edge may protect artifact consistency, authorization, exclusive services or scarce hardware.
- **Resolve:** remove only nonsemantic edges; put approvals before allocation where supported; acquire resources near use; compare verified artifact transfer with rebuilding.
- **Validate:** concurrent isolation and critical-path improvement without increased total demand. Jenkins supports evaluating conditions before agent allocation; timeout scope depends on placement. [Jenkins syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)

## O8. Retries, fail-fast, timeouts or exit codes distort outcomes

- **Prove:** preserve first exit status and all attempts; inspect logging pipelines, `continue-on-error`, `|| true`, child processes and report freshness.
- **Disprove:** network retry is not necessarily test flakiness; fail-fast durations are censored; legitimate scope growth can change timeout needs.
- **Resolve:** propagate failures, await children, bound classified retries and phase timeouts; collect a non-fail-fast diagnostic sample when needed.
- **Validate:** nonzero exit through logging, crash, hanging child, missing report and failed matrix cell remain nonpassing. GitHub step outputs are strings; handle `false` explicitly. [Expressions](https://docs.github.com/en/actions/reference/workflows-and-actions/expressions)

## O9. Stale result or artifact reuse

- **Prove:** reconstruct source/dependency/toolchain/platform/flags/environment/policy/producer identity, digest, age and completion.
- **Disprove:** same SHA does not guarantee equal external inputs; provenance does not prove test sufficiency.
- **Resolve:** immutable addressing, explicit validity policy, deterministic declared inputs and separated trust domains; rerun on unverifiable evidence.
- **Validate:** relevant lockfile, compiler, image, schema, policy and producer changes invalidate reuse. Verify attestation identity/signature, not merely its existence. [Attestation verification](https://docs.github.com/en/rest/orgs/attestations)

## O10. Convenience changes cross a trust boundary

- **Prove:** identify which revision supplies every executed script/action/hook/config; trace tokens, secrets, cache writes, persistent runners and downloaded artifacts.
- **Disprove:** trusted metadata-only privileged workflows differ from privileged execution of untrusted PR content.
- **Resolve:** isolate unprivileged builds; trusted promotion consumes validated inputs; scope permissions; pass untrusted text as data.
- **Validate:** fork scripts, poisoned artifacts/caches and expression injection cannot obtain secrets or persistent control. [Secure privileged events](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)

## O11. Persistent environment contamination

- **Prove:** compare identical inputs in clean/persistent environments; inventory files, processes, credentials, volumes and services before/after.
- **Disprove:** faster warm runs alone demonstrate cache warmth, not contamination.
- **Resolve:** predictable images, controlled caches, separate workspaces, per-run resources and verified cleanup.
- **Validate:** A/B/A runs with different generated files/resources match clean results. [Workspace isolation guidance](https://www.jenkins.io/doc/book/pipeline/pipeline-best-practices/)

## O12. Valid YAML, wrong pipeline behavior

- **Prove:** inspect expanded configuration and realized DAGs for event/branch/flag/permission cases; check types, contexts and shells.
- **Disprove:** lint success does not prove routing, protection wiring or runtime access; linters can lag provider syntax.
- **Resolve:** provider validation plus static checks and limited event canaries. GitLab's documented UI simulation covers a default-branch push, not all events. [CI Lint](https://docs.gitlab.com/ci/yaml/lint/)
- **Validate:** fork, queue, schedule, manual, failure and cancellation cases; negative gates before skipping/reuse enforcement.

## O13. Idle capacity cannot serve queued jobs

- **Prove:** correlate eligible ages with compatible idle workers; inspect labels/groups, architecture, account ceilings, repository access and registration.
- **Disprove:** wrong OS/trust class is not spare capacity; dependency-blocked work is not eligible demand.
- **Resolve:** repair routing/registration/access; reduce unjustified fragmentation; raise actual ceilings only when downstream services support it.
- **Validate:** pool canaries, representative bursts and runner-loss recovery improve valid verdicts, not merely registered-worker count.

## O14. Slow or failed autoscaling

- **Prove:** correlate demand, scale request, VM ready, registration, first start, shutdown and failed boots; inspect quotas/images/interruptions.
- **Disprove:** service time is not provisioning; larger maxima cannot fix an invalid image or unreachable control plane.
- **Resolve:** predictable images, suitable warm capacity, bounded scaling, independent readiness/queue watchdogs and orphan cleanup.
- **Validate:** normal/peak traces and interruptions; measure recovery, failed starts, throughput and idle cost. Preserve ephemeral-worker logs externally. [Self-hosted runners](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)

## O15. Priority starvation

- **Prove:** compare age, demand and completions by priority/pool; inspect synchronized schedules and scarce-device occupancy.
- **Disprove:** a permissible low-priority wait differs from a missed security/release deadline.
- **Resolve:** reserve or fairly share capacity, stagger bulk jobs, set freshness deadlines and bound per-bot/repository admission.
- **Validate:** sustained urgent load still permits required broad validation; check downstream congestion after rescheduling. [Backlog management](https://aws.amazon.com/builders-library/avoiding-insurmountable-queue-backlogs/)

## O16. Retry and agent feedback loops amplify overload

- **Prove:** trace test retries → jobs → workflows → bot pushes/reviews; count physical attempts and demand per valid candidate decision.
- **Disprove:** distinct revisions are not retries of one input; transient recovery differs from repeating deterministic failure.
- **Resolve:** one retry owner per failure class, attempt/demand caps, backoff/jitter for transient operations and no unchanged deterministic resubmission. Surface first useful diagnosis.
- **Validate:** bounded dependency outage stays within retry budget and drains after recovery. [Overload guidance](https://sre.google/sre-book/handling-overload/)

## O17. Reporting becomes the final bottleneck

- **Prove:** measure substantive-check finish → required-gate publication; inspect polling, report merges, downloads, gate allocation and API limits.
- **Disprove:** required evidence cannot be dropped because it appears late.
- **Resolve:** small manifests, batched reads, bounded polling and conditional bulky diagnostics; preserve candidate/run/attempt identity.
- **Validate:** absent/duplicate/delayed/failed reports yield correct status; measure reporting demand and verdict latency separately.

## O18. Work disappears before entering the queue

- **Prove:** reconcile source events → creation → admission → publication; inspect provider limits, disabled workflows, token restrictions, fork approval and webhook errors.
- **Disprove:** intentional no-op differs from missing required proof; a smaller queue may mean rejected work.
- **Resolve:** expected-versus-observed monitoring, repaired control-plane paths and bounded catch-up of still-relevant work.
- **Validate:** each trigger and controlled admission failure; missing proof remains visible and nonpassing. [GitHub Actions limits](https://docs.github.com/en/actions/reference/limits)

## Close the investigation

Record no-issue findings too. Prioritize removed unjustified demand, repeated setup and retry amplification before buying capacity. Use [experiments.md](experiments.md) to distinguish capacity relief from changed traffic, early failure or reduced validation. Provider-specific behavior above was researched on 2026-11-17; recheck exact limits and features against the deployed version.
