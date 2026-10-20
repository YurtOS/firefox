# Global instructions
Limit the amount of comments you put in the code to a strict minimum. You should almost never add comments, except sometimes on non-trivial code, function definitions if the arguments aren't self-explanatory, and class definitions and their members.

The Firefox repository is very big and so it isn't advised to blindly run grep or rg commands without specifying a narrow set of directories to search. There are tools available to help, see next section.

## Tooling for Firefox work
- Some tools useful for Firefox work are available in the `moz` MCP server
- Firefox is a very large repository, and it isn't efficient to search with usual tooling. When working on Firefox, you MUST use the `searchfox-cli` tool if you want to know about something. Its `--help` flag will show the options, but you probably want:
```
searchfox-cli --define 'AudioContext::AudioContext' # get function impl
searchfox-cli --define 'AudioSink' # get class definition
searchfox-cli -q blob --path ipdl # search for a string, restrict on path
searchfox-cli --id AudioSink -l 150 --cpp # search for identifier audio sink in C++ code, 150 results max
```
- Use the `searchfox-cli` tool except if you suspect that you need to find information about something that has changed locally, in which case use `rg` or the usual tools, since `searchfox.org` only indexes public (merged) code
- If you can't find something easily, it is better to ask than to search aimlessly
- `./mach` is the main interface to the Mozilla build system and common developer tasks. Important commands are listed here, and you can run `./mach help` for a full list of commands. If you want additional details for a given command, you can run `./mach COMMAND --help`
- `./mach lint`: Run linters. Run it without additional parameters to lint all the files you have modified
- `./mach format`: Format code. Run it without additional parameters to format all the files you have modified
- `./mach build`: Build the project
- `./mach test --auto`: Run tests
- `./mach run`: Run the project
- `treeherder-check`: Pull CI results for a try push
- Use the MCP resource `@moz:bugzilla://bug/{bug_id}` to retrieve a bug
- Use the MCP resource `@moz:phabricator://revision/D{revision_id}` to retrieve a Phabricator revision

## Fixing review comments
Use `@moz:phabricator://revision/D{revision_id}` to retrieve the revision and its comments.

You can find the review identifier by inspecting the commit log with:

- `jj log -T builtin_log_detailed` if using `jj`
- `git log -v -l 10` if using git

## Code Style
- Our style guide forbids the use of emoji.

## Workflow
- After making code changes, ensure the code is formatted by using `./mach format`, linted by using `./mach lint`, and build it using `./mach build`. If there are no errors, you can use `mach run` to ensure the browser still runs. Occasionally run `./mach clang-format -p path/to/modifiedfile path/to/othermodifiedfile` to format C++, `./mach lint --fix path/to/file` for most other files.
- You can run tests by using `./mach test --auto`. Once you are satisfied with the tests you run locally, use `mach try auto` to run tests in CI
- Ask if you should run a test. If you do, you probably want to run the test with `--headless`
- Do not perform commits yourself, ever
- It's better to just run `./mach build` without subdirectory, the build system is well optimized
- Always build normally, never use subdirectories, e.g. `./mach build` is the only command to run
- Never build with a subdirectory. Always simply do `./mach build`

# YurtOS fork

Everything above is Mozilla's guidance and stays as is, to keep upstream syncs
clean. This section applies to YurtOS/firefox. Read
[docs/agents/org.md](docs/agents/org.md) first; it is a verbatim copy of YurtOS's
shared policy, so change the canonical kernel copy before syncing it. If it
disagrees with Mozilla's text above, stop and tell the user, except as stated
here.

**Commits.** Mozilla's "Do not perform commits yourself, ever" does not apply in
this fork. The org rules require committing the failing test before the fix and
adding follow-up commits to a PR branch, so agents commit and push as
`docs/agents/org.md` describes.

## Purpose and layout

This is the SpiderMonkey engine fork used by Nightmonkey, the ahead-of-time
JavaScript-to-WebAssembly compiler in YurtOS/nightmonkey. The default branch is
`yurt`; start work and PRs from it. Only `js/` and its build matter here. The
supported configuration is the WASI SpiderMonkey shell built by Nightmonkey's
`scripts/build-spidermonkey.sh` with its `spidermonkey/mozconfig` (which enables
`--enable-external-compiler-hooks` and `--disable-jit`); Nightmonkey's `configs/`
holds benchmark-lane variants only. A native
`wasm32-yurt-linux-musl` mozbuild target is tracked in YurtOS/firefox#1; do not
add compiler wrappers or temporary target configuration to work around it.

Engine hooks that an external compiler depends on live in
`js/public/ExternalCompilerHooks.h` and `js/src/vm/ExternalCompilerHooks.cpp`.
Their tables, layout constants and offsets are mirrored in Nightmonkey. Change
both sides together: land the engine change as its own PR here, then pin the
matching revision in Nightmonkey. Record the exact engine SHA with any build,
test result or timing.

## Verification

For engine changes run, from the repository root, `./mach format`, `./mach lint`
and `./mach build` as above. Then run the tests that cover the change:

- Regressions in `js/src/jit-test/tests/`: run the file with the built shell
  (a WASI shell runs under Wasmtime), or through `js/src/jit-test/jit_test.py`.
  A passing run exits 0; a nonzero exit is a failure.
- Harness changes (once `js/src/tests/lib/test_jittests.py` exists, added by
  YurtOS/firefox#3): `cd js/src/tests && python3 -m unittest lib.test_jittests`.
  Do not pass `-I`; it removes the working directory from the import path and
  the module will not load.
- Running these tests needs no extra approval, despite "Ask if you should run a
  test" above.
- Affected language semantics: scoped `jit-test` and `jstests` runs with the
  filter, executed and passing counts stated. A zero-test run, a selected-count
  summary or an interrupted run is not evidence.

A test or gate that cannot fail is not evidence. Add the red test first, show it
fails for the intended reason on the base, and for guard or notification code
show that disabling the code makes the test fail. Report skipped lanes,
exclusions and failures reproduced on the base explicitly.

Native JIT paths are not execution-qualified in the supported configuration.
Say so rather than claiming coverage for them.

Changes to `.github/workflows/` require approval from the Mozilla GitHub
Enterprise Administrators Team (see `.github/workflows/README`); do not edit
them as part of ordinary work. Check live branch protection before describing
any hosted job as required; at the time of writing `yurt` has none.

## Engine rules

- Preserve JavaScript semantics, exception behavior, evaluation order and GC
  safety. Keep rooting, barriers and shape/property-map invariants at their
  owners; copying a property map must preserve its flags (for example `HasEnumerable`,
  and `PermutedSlots` once YurtOS/firefox#3 adds it).
- Hook callers are trusted engine code in the same process. Keep existing
  assertions; do not add a second validation layer for a caller that violates a
  documented contract. Input that crosses a trust boundary is different and must
  stay validated.
- Optimise only on evidence: a benchmark against the same engine revision,
  program and options.
- Keep fork changes to upstream Mozilla files small and separate from
  Yurt-specific files, so upstream merges stay reviewable.

## Skills and discovery

The shared workflows live in `.agents/skills/`; `.claude/skills` links to that
directory. Use issue-to-mergeable-pr, drive-pr-to-mergeable, drive-pr-stack and
drive-doc-to-approved for their named workflows. Global plugins and CLIs are
prerequisites, not vendored dependencies; report unavailable reviewers rather
than claiming their approval. Use `searchfox-cli` for code discovery as
described above, and never copy local permission grants, credentials or
machine-specific paths from another repository.
