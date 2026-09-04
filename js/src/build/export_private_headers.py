# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Export the engine's private headers and compile configuration for an
# external compiler tier (--enable-external-compiler-hooks): mirrors js/src
# (source and generated headers) under dist/include-private and records the
# flags libjs was compiled with in dist/include-private/js-build-config.json.

import json
import os
import shutil

import buildconfig

SKIP_DIRS = {
    "ctypes",
    "devtools",
    "doc",
    "editline",
    "fuzz-tests",
    "gdb",
    "jit-test",
    "jsapi-tests",
    "octane",
    "rust",
    "tests",
    "__pycache__",
}


def copy_tree(
    src_root, dst_root, suffixes=(".h", ".msg", ".inc", ".def"), skip_dirs=SKIP_DIRS
):
    copied = []
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        rel = os.path.relpath(dirpath, src_root)
        for name in sorted(filenames):
            if not name.endswith(suffixes):
                continue
            src = os.path.join(dirpath, name)
            dst = (
                os.path.join(dst_root, rel, name)
                if rel != "."
                else os.path.join(dst_root, name)
            )
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                shutil.copy2(src, dst)
            copied.append(dst)
    return copied


def subst(name, default=None):
    value = buildconfig.substs.get(name)
    return default if value is None else value


def main(output, *inputs):
    topsrcdir = buildconfig.topsrcdir
    topobjdir = buildconfig.topobjdir
    dist = os.path.join(topobjdir, "dist")
    out = os.path.join(dist, "include-private")
    os.makedirs(out, exist_ok=True)

    copied = []
    copied += copy_tree(os.path.join(topsrcdir, "js", "src"), out)
    # Generated headers live in the objdir mirror of js/src; js-confdefs.h is
    # the force-included configuration header every engine TU sees.
    copied += copy_tree(
        os.path.join(topobjdir, "js", "src"), out, skip_dirs=SKIP_DIRS | {"build"}
    )
    for extra in ("config/gcc_hidden.h",):
        src = os.path.join(topsrcdir, extra)
        dst = os.path.join(out, os.path.basename(extra))
        shutil.copy2(src, dst)
        copied.append(dst)

    config = {
        "topsrcdir": topsrcdir,
        "topobjdir": topobjdir,
        "cxx": subst("CXX", []),
        "cc": subst("CC", []),
        "ar": subst("AR", ""),
        "cxx_base_flags": subst("CXX_BASE_FLAGS", []),
        "os_cxxflags": subst("OS_CXXFLAGS", []),
        "optimize_flags": (
            subst("MOZ_OPTIMIZE_FLAGS", []) if subst("MOZ_OPTIMIZE") else []
        ),
        "debug_flags": subst("MOZ_DEBUG_FLAGS", []) if subst("MOZ_DEBUG") else [],
        "warnings_cxxflags": subst("WARNINGS_CXXFLAGS", []),
        "debug_defines": subst("MOZ_DEBUG_DEFINES", []),
        "extra_cxxflags": ["-fno-strict-aliasing", "-ffp-contract=off"],
        "library_defines": [
            "MOZILLA_CLIENT",
            "EXPORT_JS_API",
            "MOZ_HAS_MOZGLUE",
            "MOZ_SUPPORT_LEAKCHECKING",
        ],
        "force_includes": ["gcc_hidden.h", "js-confdefs.h"],
        "include_dirs": ["include-private", "include", "system_wrappers"],
        "os_ldflags": subst("OS_LDFLAGS", []),
        "rust_target": subst("RUST_TARGET", ""),
        "os_arch": subst("OS_ARCH", ""),
        "moz_debug": bool(subst("MOZ_DEBUG")),
        "js_shell_wizer": bool(subst("JS_SHELL_WIZER")),
        "libraries": [
            "lib/libjsshell.a",
            "lib/libjs_static.a",
            "lib/libjsrust.a",
            "lib/libpure_virtual.a",
        ],
    }
    with open(os.path.join(out, "js-build-config.json"), "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)

    output.write("%d headers\n" % len(copied))
    return 0
