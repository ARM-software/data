# Machine-readable data

## pmu

This repository contains JSON descriptions of hardware performance events for Arm cores.
 
### PMU data schema
  
The JSON schema is in pmu/pmu-schema.json. Briefly, each JSON file contains a list of events,
each event being described by a JSON object:

```
        {
            "code": 1,
            "name": "L1I_CACHE_REFILL",
            "architectural": false,
            "type": "UEVT",
            "subtype": "REFILL",
            "component": "L1I",
            "event_bits": 1,
            "event_lsb": 0,
            "trace_lsb": 1,
            "description": "Level 1 instruction cache refill"
        },
```

The "type" field classfies the event:

| type  | meaning                                                  |
|-------|----------------------------------------------------------|
| INS   | Instruction of a certain type executed                   |
| UEVT  | Microarchitectural event                                 |
| CYCLE | Counts number of cycles during which a condition is true |
| EXC   | Exception of a certain type                              |

For microarchitectural events the "component" field indicates the core component
that the event relates to:

|        | component          |
|--------|--------------------|
| L1I    | L1 I-cache         |
| L1D    | L1 D-cache         |
| L2     | L2 cache           |
| BPU    | Branch predictor   |
| L1ITLB | L1 instruction TLB |
| L1DTLB | L1 data TLB        |
| BUS    | Core bus interface |

The "subtype" field may be present to classify the event further, e.g. into READ,
WRITE, ACCESS and REFILL cache events.

For events exported on the external event bus, and/or to the ETM,
the position of the event on the bus is shown.
