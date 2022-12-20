#!/usr/bin/python

"""
SPDX-License-Identifier: Apache-2.0

Copyright (C) Arm Ltd. 2022

Generate C header source for libpfm4
"""

from __future__ import print_function

import os, sys, json

o_verbose = 0

def cpu_name_c(s):
    """
    Transform a CPU name e.g. "Cortex-A57", "Neoverse N1", into a valid C identifier.
    """
    s = s.lower().replace(' ','_').replace('-','_')
    return s


def short_desc(desc):
    """
    Take the full event description and return a single-sentence summary,
    minus the trailing full stop.
    """
    ix = desc.find('.')
    if ix >= 0:
        desc = desc[:ix]
    return desc


def gen_header_from_json(j, ofn, include_alternates=True):
    arch_version = int(j["architecture"][4])
    assert 6 <= arch_version and arch_version <= 9
    if "cpu" in j:
        is_cpu_specific = True
        cpu_name = j["cpu"]
    else:
        is_cpu_specific = False
        cpu_name = "generic ARMv%u" % arch_version
    c_name = "arm_" + cpu_name_c(j["cpu"])
    old_stdout = sys.stdout
    if ofn is not None:
        if os.path.isdir(ofn):
            ofn = os.path.join(ofn, "%s_events.h" % c_name)
        if o_verbose:
            print("writing to %s..." % ofn, file=sys.stderr)
        sys.stdout = open(ofn, "w")
    print("/*")
    print(" * %s Event Table" % cpu_name)
    print(" */")
    print("static const arm_entry_t %s_pe[]={" % c_name)
    for e in j["events"]:
        if "code" not in e:
            # Bus-only event: not applicable to libpfm4/PAPI
            if o_verbose:
                print("%s ignoring bus-only event" % cpu_name, file=sys.stderr)
            continue
        if e["code"] == 0x1e:
            assert e["name"] == "CHAIN"
            # libpfm4 does not directly expose the CHAIN event, since it is designed
            # for use by the event collection mechanism itself.
            continue
        if "name" in e:
            names = [e["name"]]
        else:
            # Unusual: some of the older TRMs have unnamed IMP DEF events. E.g. Cortex-A7.
            names = ["EVENT_%04X" % e["code"]]
            if o_verbose:
                print("%s event 0x%x is unnamed, calling it %s" % (cpu_name, e["code"], names[0]), file=sys.stderr)
        if include_alternates and "trm_name" in e:
            # Sometimes the TRM names don't agree with the ones standardized in the architecture.
            # We can put out the extra names as aliases using the ".equiv" field.
            names.append(e["trm_name"])
        if o_verbose >= 2:
            print("  %s 0x%x %s" % (cpu_name, e["code"], names), file=sys.stderr)
        for (i, name) in enumerate(names):
            print('\t{.name = "%s",' % name)
            if arch_version >= 8:
                print('\t .modmsk = ARMV8_ATTRS,')   # there is no ARMV9_ATTRS
            if i == 1:
                print('\t .equiv = "%s",' % names[0])
            print('\t .code = 0x%02x,' % e["code"])
            print('\t .desc = "%s"' % short_desc(e["description"]))
            print('\t},')
    if is_cpu_specific:
        print("\t/* END %s specific events */" % cpu_name)
    print("};")
    sys.stdout = old_stdout


def gen_header_from_file(ifn, ofn, include_alternates=True):
    with open(ifn) as f:
        j = json.load(f)
    gen_header_from_json(j, ofn, include_alternates=include_alternates)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="generate event header for libpfm4")
    parser.add_argument("-i", "--input", type=str, help="input event JSON file")
    parser.add_argument("-o", "--output", type=str, help="output C header file")
    parser.add_argument("--standard-names-only", action="store_true", help="use architecturally standard event names only")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="increase verbosity")
    opts = parser.parse_args()
    o_verbose = opts.verbose
    gen_header_from_file(opts.input, opts.output, include_alternates=(not opts.standard_names_only))
