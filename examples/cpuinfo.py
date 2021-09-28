#!/usr/bin/python

"""
SPDX-License-Identifier: Apache-2.0

Copyright (C) Arm Ltd. 2021

Read /proc/cpuinfo and match against the CPU JSON file.

The CPU JSON file is read from a local copy if available,
otherwise it is retrieved from github.com.
"""

from __future__ import print_function

import os, sys, json
try:
    from urllib.parse import quote   # Python3
    from urllib.request import urlopen
except:
    from urllib import quote, urlopen       # Python2

data_url = "https://raw.githubusercontent.com/ARM-software/data/master"


def read_proc_cpuinfo():
    """
    Read /proc/cpuinfo, returning a series of (CPU number, description) pairs.
    We cope with two basic styles of /proc/cpuinfo:

      style A:
         processor : 0
         key1      : ...
         key2      : ...

         processor : 1
         key1      : ...
         key2      : ...

      style B:
         processor : 0
         processor : 1
         key1      : ...
         key2      : ...

    This routine is architecture-neutral. See System.spec_from_keys for how
    this is translated into a processor code for Intel or Arm.
    """
    f = open("/proc/cpuinfo")
    cpus = []
    keys = {}
    last_cpu_number = None
    for r in f:
        cix = r.find(':')
        if cix < 0:
            for c in cpus:
                yield (c, keys)
            cpus = []
            keys = {}
        if r.startswith("processor"):
            # the CPU number on this system, as seen by Linux
            cpuno = int(r[cix+2:-1])
            if last_cpu_number is not None:
                assert cpuno > last_cpu_number
                if cpuno != last_cpu_number + 1:
                    print("** /proc/cpuinfo is missing CPU(s) %u..%u" % (last_cpu_number+1, cpuno-1), file=sys.stderr)
            last_cpu_number = cpuno
            cpus.append(cpuno)
        elif cpus:
            # only start collecting keys when we've got at least one CPU
            key = r[:cix].strip()
            keys[key] = r[cix+2:-1]
    f.close()
    for c in cpus:
        yield (c, keys)


def get_json_data(fn):
    cache = os.path.expanduser("~") + "/.cache/arm-data"
    cache_fn = os.path.join(cache, fn)
    if os.path.exists(cache_fn):
        with open(cache_fn) as f:
            j = json.load(f)
    else:
        url = data_url + "/" + fn
        # If not found: Python2 succeeds with 404, Python3 throws HTTPError.
        try:
            not_found = False
            session = urlopen(url)
        except Exception:
            not_found = True
        if not_found or session.getcode() != 200:
            print("cannot load %s" % (url), file=sys.stderr)
            return None
        raw = session.read().decode()
        j = json.loads(raw)
        os.makedirs(os.path.dirname(cache_fn))
        with open(cache_fn, "w") as f:
            f.write(raw)
    return j


j_cpus = get_json_data("cpus.json")

def get_pmu_events(cpu_name):
    return get_json_data("pmu/" + cpu_name + ".json")


def read_system_cpu_list():
    """
    Use the CPU identifiers from /proc/cpuinfo to return a list of
    the current system's CPUs, with their product names.
    """
    for (cpu_number, keys) in read_proc_cpuinfo():
        imp     = int(keys["CPU implementer"], 16)
        part    = int(keys["CPU part"], 16)
        variant = int(keys["CPU variant"], 16)
        rev     = int(keys["CPU revision"])
        # Form a CPUID to match the JSON, most significant bytes first.
        # (In the MIDR, the fields are in a different, less useful, order.)
        cpuid   = "0x%02x%03x%1x%1x" % (imp, part, variant, rev)
        the_cpu = None
        for cpu in j_cpus["cpus"]:
            if "cpuid" in cpu:
                if cpuid.startswith(cpu["cpuid"].lower()):
                    the_cpu = cpu
            elif "cpuids" in cpu:
                for id in cpu["cpuids"]:
                    if cpuid.startswith(id.lower()):
                        the_cpu = cpu
                        break
            if the_cpu is not None:
                break
        if the_cpu is not None:
            # Put the CPU name into the form in which it's used by tools
            cpu_name = cpu["name"].lower().replace(' ','-')
        else:
            print("CPU #%3u: CPU ID 0x%s not in table" % (cpu_number, cpuid), file=sys.stderr)
            cpu_name = None
        yield (cpu_number, cpu_name, cpu["arch"])


if __name__ == "__main__":
    for (cpu_number, cpu_name, cpu_arch) in read_system_cpu_list():
        print("CPU #%3u: -march=%s" % (cpu_number, cpu_arch), end="")
        if cpu_name is not None:
            print(" -mcpu=%s" % (cpu_name), end="")
            pmu = get_pmu_events(cpu_name)
            if pmu is not None:
                n_counters = pmu["counters"]
                n_events = len(pmu["events"])
                print(": %u counters, %u events" % (n_counters, n_events), end="")
        print()

