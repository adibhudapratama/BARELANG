# Cargo-Lift Robot: Autonomous Mecanum–Scissor Lift Robot for Loose-Baggage Handling in Narrow-Body Aircraft Cargo Holds

<div align="center">

[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic%20(gz--sim8)-orange?logo=gazebo)](https://gazebosim.org/docs/harmonic/install_ubuntu/)
[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy%20Jalisco-blue?logo=ros)](https://docs.ros.org/en/jazzy/)
[![CAD](https://img.shields.io/badge/CAD-STEP%20AP214%20(mm)-informational)](#-cad--media-deliverables)
[![Status](https://img.shields.io/badge/Status-Detailed%20Concept%20Design-yellow)](#-design-checks--what-is-and-is-not-verified)
[![Hackathon](https://img.shields.io/badge/Barelang-Hackathon-red)](#-team-information)
[![Hold](https://img.shields.io/badge/Hold-Generic%20Bulk%20Compartment%20(1.2%20m)-informational)](#-the-cargo-hold-challenge)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**A compact mecanum mobile robot that receives a bag from an external conveyor at the aircraft side door, drives into a low bulk hold (1.2 m ceiling), and stacks it directly on the floor or on a lower bag, then unloads it again top-down.**

[Overview](#-overview) • [Demonstrations](#-key-demonstrations) • [Architecture](#-system-architecture) • [Handling Sequence](#-handling-sequence) • [Quickstart](#-quickstart--gazebo-replay) • [Design Checks](#-design-checks--what-is-and-is-not-verified) • [Team](#-team-information) • [License](#-license)

---

![Cargo-Lift Robot](assets/images/fig_hero_robot.png)
*Figure 1. Cargo-Lift robot in its home configuration: mecanum base, twin scissor lift, main conveyor and the open portal transfer head (1195 x 791 x 805 mm).*

</div>

---

## 🚀 Overview

Narrow-body aircraft have lower-deck bulk holds with a very low ceiling (about **1.2 m** in the reference model). Ramp workers must load, lift and stack 20 to 32 kg suitcases while crouching or kneeling, which means slow turnarounds and a high risk of musculoskeletal injury.

**Cargo-Lift** removes that manual handling. An external feeder conveyor ends at the side door. The robot docks at the door, takes one bag at a time, retreats into a reserved turning bay, rotates its whole base, drives to the target lane, lifts and extends its head, and places the bag directly on the floor or on a lower bag. Unloading reverses the sequence and removes the top bag first.

### 🌟 Key Highlights

- **32 kg design payload** (20 to 32 kg range) with a rated rigid, aligned bag of up to 800 x 500 x 320 mm.
- **Low profile:** 805 mm home height, and a maximum-height configuration of 1150 mm, leaving 50 mm under the 1200 mm reference ceiling.
- **Open portal head:** outboard columns and overhead drives keep all transverse mechanisms above the bag path, so the transfer corridor and the working aisle stay clear.
- **Direct placement:** no second handover. The robot stacks and unloads the bag itself, with a 2-stage Z head, two compliant jaws and a retractable support blade.
- **14 actuators:** 4 mecanum drives + 10 handling axes (A01 to A14), 3800 W total nameplate power on a 48 V / 30 Ah reference pack.
- **Honest scope:** every number is labelled as a CAD value, an engineering budget, or a geometric check. See [Design Checks](#-design-checks--what-is-and-is-not-verified).

---

## 🎬 Key Demonstrations

| Hold scene with 30 bags | Open-portal assemblies |
| :---: | :---: |
| ![Cargo hold scene](assets/images/fig_cargo_hold_scene.jpg) | ![Assemblies](assets/images/fig_assemblies.png) |
| *Robot docked at the side door of the generic hold, with the external feeder and the 30-bag storage bays.* | *CAD key: chassis, wheel modules, scissor module, conveyor deck, open portal, hanging jaws and outboard actuators.* |

| End-effector actuation | Hold plan view |
| :---: | :---: |
| ![End effector](assets/images/fig_end_effector.png) | ![Hold plan](assets/images/fig_hold_plan.png) |
| *Nose belt, jaws, micro-lift and retractable support blade (A10 to A14).* | *4.50 x 2.20 m floor: reserved turning bay, active bag bays (1 + 2) and eight 3-bag footprints.* |

---

## ✈️ The Cargo-Hold Challenge

The demo uses a **generic bulk compartment**, not an Airbus or Boeing OEM model.

```
Top view (not to scale) — hold floor 4.50 m x 2.20 m, ceiling 1.20 m

 +-----------------------------------------------------------------+
 | Reserved turning / docking bay        [1+2]    [ 3 ]  [ 3 ]     |
 |  +---------------------+                                        |
 |  |     Robot home      |                       [ 3 ]  [ 3 ]     |
 |  |  (1195 x 791 mm)    |                                        |
 |  +----------+----------+                       [ 3 ]  [ 3 ]     |
 |             ^                                                   |
 |             |                       [1+2]      [ 3 ]  [ 3 ]     |
 +-------------|---------------------------------------------------+
        [ side door 1300 x 1050 mm ]
               |
        [ external feeder ]

 [3]   = footprint with 3 stacked background bags
 [1+2] = footprint that receives the active bags
```

| Parameter | Scene value |
| :--- | :--- |
| Interior reference dimensions | 4500 mm length, 2200 mm floor width, 1200 mm height |
| Side-door clear opening | 1300 mm wide x 1050 mm high (door shown open) |
| Bag count (initial / max / final) | 26 / 30 / 26 |
| Active bag size | 650 x 360 x 260 mm |
| Storage pattern | Eight footprints of three bags at x = 3.40 / 4.15 m; two front footprints receive the four active bags |
| Construction detail | Floor panels, recessed tie-down rails, curved liners, formers/rivets, bulkheads, removable roof, lights, door frame and hinges |

> **What "filled" means:** the designated storage bays hold 30 bags while the working aisle and turning bay stay clear. Four bags are unloaded from that state and the 26 background bags stay in place. The scene does not represent filling every part of the hold volume.

---

## 🏗️ System Architecture

### Mechanical subsystems

| Subsystem | Function in the operating cycle |
| :--- | :--- |
| **Mecanum mobile base** | Longitudinal travel, lateral docking and whole-base rotation inside the reserved turning bay |
| **Twin scissor lift** | Raises the conveyor and head assembly to the required stacking level |
| **Open portal transfer head** | Outboard columns, overhead drives, telescoping Z stages, two jaws and a retractable support blade |
| **Main and nose conveyors** | Receive or return a bag through the open corridor at the side door |
| **External ground equipment** | Feeder terminates at the door; a level service platform is used only for robot entry/exit and parks away during transfer |

### Control and power layers (proposed hardware architecture)

```
+-------------------------------------------------------------------------+
|  PERCEPTION / SUPERVISION                                               |
|  Industrial PC or Jetson-class computer                                 |
|  Bag pose, job queue, paths, operator interface                         |
+-------------------------------------------------------------------------+
|  SENSORS                                                                |
|  RGB-D camera • 2D LiDAR • IMU • photoeyes • wheel encoders             |
|  Jaw load sensing • home / limit switches                               |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|  MOTION CONTROLLER + ISOLATED CANopen                                   |
|  Axis homing • synchronous commands • force caps                        |
|  Transfer-ready logic • watchdog                                        |
+-------------------------------------------------------------------------+
        |                                         |
        v                                         v
+-----------------------------+   +-----------------------------------------+
|  48 V POWER BRANCH          |   |  DRIVES / LOCAL FEEDBACK                |
|  Battery • fuse • pre-charge|   |  Integrated servo drives and brakes     |
|  contactor • 24/12/5 V DC/DC|   |  4 traction drives + 10 handling axes   |
+-----------------------------+   +-----------------------------------------+
```

| Device or signal | Purpose / proposed arrangement |
| :--- | :--- |
| 2D LiDAR + IMU + wheel encoders | Estimate base motion and check reserved-space clearance (validate near reflective liners and feature-poor surfaces) |
| RGB-D camera | Estimate bag dimensions, grasp region and top surface; detect an unsuitable placement |
| Entry / exit photoeyes + height gate | Confirm a bag is inside the transfer corridor and within the planned envelope before belt motion |
| Jaw load sensing + motor feedback | Limit clamp force, detect loss of grip; belt current/position monitoring identifies a jam |
| Dual end limits / position feedback | Homing, hard stops and position plausibility for lift, extension, blade and telescopic stages |
| Independent stop / retention | Hardwired stop chain, power contactor, mechanically retained vertical axes. Do not assume the candidate drive provides a certified STO function |

> This is an implementation proposal, not a final wiring schematic. Autonomous functions (perception, navigation, packing, fault recovery) are development work.

### Mechanical specification

| Parameter | Design value |
| :--- | :--- |
| Home envelope (L x W x H) | 1195 x 791 x 805 mm |
| Reference extended pose | 1635 x 791 x 1071.5 mm (a defined pose, not the full swept envelope) |
| Chassis / wheelbase / track | 980 x 660 mm chassis; 720 mm wheelbase; 580 mm track |
| Mass (empty / loaded) | 196 kg / 228 kg at the 32 kg design payload (estimate) |
| Mecanum wheels | 150 mm diameter, 12 rollers per wheel, 45 degree nominal roller angle |
| Travel speed / acceleration | Empty 0.30 m/s, loaded 0.15 m/s; acceleration limit 0.25 m/s2 |
| Scissor lift | 650 mm bars; scissor height 120 – 430 mm; 310 mm vertical travel |
| Transfer belt height | 366 mm home, 676 mm with the main lift fully raised |
| Head extension / Z | 440 mm horizontal; 345 mm Z travel in two 172.5 mm stages |
| Support blade / micro-lift | 560 mm blade retraction; 35 mm jaw micro-lift |
| Jaw aperture / stroke | 600 mm pad-to-pad opening; 220 mm travel per side |
| Rated bag / passage | Rigid aligned bag up to 800 x 500 x 320 mm; minimum passage width 560 mm |
| CAD size | 1771 named components, 2181 solid bodies; motion model with 71 links and 70 joints |

**Vertical clearance:** the lowest overhead member is 366.5 mm above the belt, so the 320 mm reference bag has 46.5 mm nominal head clearance. A maximum-height configuration reaches 1150 mm, leaving 50 mm under the 1200 mm reference ceiling. The passage check includes a +/-10 mm lateral pose allowance and 10 mm extra top allowance, and models a rigid aligned bag only.

### Actuator budget (A01 – A14)

| Axis | Qty | Motor reference | Transmission / design requirement |
| :--- | :---: | :--- | :--- |
| A01 – A04 Mecanum drives | 4 | 200 W, 48 V (iSV2-CAN6020V48G candidate) | 20:1 planetary + 1:1 belt; ~10.9 N.m continuous per wheel; holding brake |
| A05 Scissor lift | 1 | 750 W, 48 V (iSV2-CAN8075V48G) | 6:1 + 25 x 5 mm ballscrew; thrust supports for at least 15 kN |
| A06 Head Z | 1 | 750 W, 48 V (iSV2-CAN8075V48G) | 20:1 + overhead sync shaft + 2:1 telescopic cascade; 345 mm; 1219 N theoretical lift |
| A07 Head yaw | 1 | 100 W servo/BLDC class (SKU pending) | 150:1 total + slew bearing; at least 39 N.m; +/-30 degrees loaded reference |
| A08 Extension | 1 | 200 W class | 10:1 + rack/pinion (20 mm radius); 440 mm stroke; force cap 200 N |
| A09 Main belt | 1 | 200 W (iSV2-CAN6020V48H) | 20:1 + 50 mm roller; 0.20 m/s nominal; transfer force cap 180 N |
| A10 Nose belt | 1 | 200 W (iSV2-CAN6020V48H) | 20:1 + 2:1 speed increase; 16 mm roller; force cap 180 N |
| A11 Jaw micro-lift | 1 | 200 W class | 2:1 + bevel + 16 x 5 mm ballscrew; 35 mm; holding brake and catcher |
| A12 – A13 Jaws | 2 | 200 W class each | 16 x 5 mm screws; 220 mm stroke each; 450 N per jaw with load feedback |
| A14 Support blade | 1 | 200 W class | 10:1 + 12 mm rack/pinion; 560 mm stroke; initial loaded pull limit 60 N |

The 14-actuator budget totals **3800 W mechanical nameplate power**. This is the sum of design motor classes, not the expected battery draw.

> ⚠️ **Catalog discrepancy:** the Leadshine 6020V48G page lists 200 W / 0.64 N.m in its feature list but 400 W / 1.27 N.m in its technical table. The design keeps the conservative 200 W class. Get a consistent manufacturer datasheet before ordering the G variant.

---

## 🔄 Handling Sequence

**Loading**

| Step | Action and interlock |
| :--- | :--- |
| 1. Enter | Head stored, lift low, service platform level with the hold floor. Enter through the open side door, then park the platform away before the feeder approaches |
| 2. Receive | Dock facing the door. Base stationary, jaws open, extension and head Z home, path clear. Run belts only after transfer-ready verification |
| 3. Secure and shuttle | Stop belts, grip the bag with load feedback, confirm support. Retreat into the turning bay, rotate the base 90 degrees, travel toward the target lane |
| 4. Place | Stop the base. Lift to the stack level, extend, retract the blade and release the bag onto the support below |
| 5. Clear and return | Keep lift height while retracting the head. Lower only after the portal has cleared the placed bag, then return to the side-door dock |

**Unloading:** approach the top accessible bag with the base stopped, align the open jaws, apply a force-limited grip, raise the micro-lift by up to 35 mm and insert the support blade. Retract from the stack before lowering. Return to the door, stop, open the transfer corridor and reverse the belts to the external feeder. Work from the top down, in reverse placement order.

**Operating limits carried into the proposed controller**

- Keep the base **stopped** during extension, placement and upper-stack pickup.
- **Retract the head** before whole-base turning, and rotate the loaded base only in the reserved bay.
- A **90-degree loaded head-yaw** manoeuvre with full extension and a raised lift is excluded: the static edge-moment ratio falls below 1 in that configuration.

| Condition | Required response in the proposed hardware |
| :--- | :--- |
| Bag exceeds the envelope or straps enter a gap | Stop transfer, retain the bag, request operator recovery |
| Grip, encoder or jam check fails | Stop the current phase; no blind lift or extension retries |
| Obstacle enters the reserved path | Hold the job until the path is revalidated |
| Upper-layer placement complete | Retract at the current height before lowering the lift |
| Exit requested | Park the external feeder, return the level service platform, leave with the head stored |

> These interlocks describe the intended physical controller. The supplied animation follows predetermined successful poses and **does not** demonstrate sensor-driven fault recovery.

---

## 🎮 Quickstart & Gazebo Replay

The Gazebo package replays the original 1101-second trajectory (196 keyframes) in the generic hold.

### 1. Prerequisites

- **OS:** Ubuntu 24.04
- **Simulator:** Gazebo Harmonic (gz-sim8). ROS 2 is **not** required for the main mode
- **Package:** `Cargo_Hold_v6_Gazebo_Full.zip`, extracted to `simulation/cargo_hold_v6/`

### 2. Run

```bash
git clone https://github.com/[adibhudapratama]/[BARELANG].git
cd [BARELANG]/simulation/cargo_hold_v6

sudo bash install_dependencies.sh
bash run_gazebo.sh --speed 10      # about 110 s at a real-time factor near 1
```

> The replay prescribes poses and intentionally omits the Physics system, so it is a visual and kinematic check, not a dynamics simulation. The 120 s MP4 is a separate presentation export and does not replace the Gazebo motion files.

---

## 📊 Design Checks & What Is and Is Not Verified

### Analytical sizing (engineering budgets)

| Mechanism | Required (design) | Available (reference) | Capacity / required |
| :--- | :--- | :--- | :---: |
| Wheel drive (228 kg, 0.04 rolling resistance, 2 degree slope, 0.25 m/s2, 0.65 efficiency, 1.5 factor) | 9.72 N.m per wheel | 10.94 N.m | 1.13 |
| Main scissor (115.5 kg supported, minimum scissor angle 10.64 degrees) | 10.41 kN | 13.79 kN | 1.32 |
| Head Z cascade (74.2 kg effective) | 1092 N | 1219 N | 1.12 |
| Main conveyor (180 N cap, 25 mm roller) | 5.29 N.m | 11.52 N.m | 2.18 |
| Jaw friction grip (450 N per jaw, mu = 0.60) | 314 N (32 kg bag weight) | 540 N friction capacity | 1.72 |
| Extended stability (head forward, full extension, raised lift, 60 N pull) | — | Edge moment ratio ≈ 1.30 | limited static case only |
| Chassis floor pressure | — | ≈ 350 kg/m2 (228 kg over 0.65 m2) | wheel point loads still to confirm |

### Digital package checks

| Check | Result and scope |
| :--- | :--- |
| STEP round-trip | All four STEP files re-imported through OpenCascade; every solid has valid BRep geometry and positive volume (499 / 2181 / 3250 / 3129 solids) |
| Gazebo source compilation | `ScenarioReplay` and `CargoHandling` compiled with Gazebo Harmonic 8.15.0, GCC 13 and CMake |
| Core replay execution | 77 tracks, 11011 trajectory samples, 2203 core test updates; source-checkpoint maximum position error 0.0 m |
| Structure and assets | 886 SDF / asset / code / trajectory checks passed |
| Discrete geometry check | 2203 sampled CAD-part AABB comparisons against other bags found no intersections (carried bag excluded). Not a continuous collision or full self-collision proof |

### Not yet verified

- End-to-end Gazebo Server/GUI execution was blocked by environment socket restrictions, so core tests are not a substitute for a full GUI run.
- Contact forces, mecanum traction, bag deformation, navigation/SLAM and autonomous packing are **not** validated (the replay has no Physics system).
- Structural fatigue life, brake stopping performance and floor-panel compatibility are not established.
- Soft bags, loose straps, tilted oversize items and real bag friction or grip damage still need trials.
- The design is for a **generic** hold. Aircraft-specific door, sill, liner and floor-load data are needed before any compatibility claim.

---

## 🔋 Battery & Endurance

![Endurance](assets/images/fig_endurance_chart.png)

| Quantity | Reference value |
| :--- | :--- |
| Nominal stored energy | 48 V x 30 Ah = 1440 Wh |
| Operating energy budget | 1440 x 0.80 capacity x 0.94 distribution x 0.85 before reserve = 920.45 Wh |
| Reference loading cycle | 30 s; 20.3 Wh; average bus power 610 W |
| Reference endurance | 920.45 Wh / 610 W = **1.51 h** (1.21 h with 20% capacity ageing) |
| BMS / charging start point | 125 A continuous, 200 A peak; 10 A charging ≈ 2.9 h for an 80% refill plus allowance |

Endurance is a design estimate from assumed duty-cycle power, not a discharge test or a motor-current result.

### 📈 Throughput Transparency

- One reference cycle takes *30 s per bag**, about **2 bags/min** for a single robot.
- A 12 bags/min (5 s per bag) target would need roughly **6 robots** working in parallel, or a redesign of the transfer concept. Multi-robot traffic, shared docking and feeder logistics are not analysed here.

---

## 📁 CAD & Media Deliverables

| File | Contents |
| :--- | :--- |
| `cad/Cargo_Lift_Robot.step` | Robot alone, home configuration, detailed neutral solid geometry |
| `cad/Aircraft_Cargo_Hold.step` | Empty cargo hold with the side door open |
| `cad/Robot_and_Cargo_Hold.step` | Robot + complete hold + 30 reference bags (static snapshot) |
| `cad/Robot_and_Cargo_Hold_Cutaway.step` | Inspection version with selected enclosure panels removed |
| `media/Cargo_Robot_Simulation_120s.mp4` | Clean 120 s presentation video |
| `docs/Cargo_Robot_Technical_Report.pdf` | Self-contained English design and technical report |

STEP units are millimetres. Each file is a multibody AP214 solid model with no native SolidWorks feature history or motion mates. URDF/SDF and mesh units in the Gazebo package are metres.

---

## 📂 Repository Structure

```
[repo-name]/
├── README.md
├── LICENSE
├── .gitignore
├── assets/
│   └── images/                       # Renders used in this README
├── cad/                              # STEP models (robot, hold, combined, cutaway)
├── media/
│   └── Cargo_Robot_Simulation_120s.mp4
├── docs/
│   ├── Cargo_Robot_Technical_Report.pdf
│   └── Hackathon_Presentation.pdf    # 8-slide submission deck
├── simulation/
│   └── cargo_hold_v6/                # Gazebo Harmonic replay package
│       ├── install_dependencies.sh
│       └── run_gazebo.sh
└── tools/                            # Report / video / CAD export scripts (optional)
```

---

## 👥 Team Information

**Team Name:** BARELANG  
**Affiliation:** Batam State Polytechnic (Politeknik Negeri Batam), Indonesia  
**Submission Category:** SUTD ROAR Lab Open Hackathon 2026 (Item No. 3_Report_BARELANG_Adib.PDF)

| Role | Name | Email |
| :--- | :--- | :--- |
| **Team Lead** | **Adib Huda Pratama** | `adibhudapratama@gmail.com` |
| **Member** | **Ibnu Rasydin** | `ibnurasydin@gmail.com` |
| **Member** | **Muhammad Rasyid Prasetyo** | `mrasyiidp@gmail.com` |
| **Member** | **Rajiv Tajusa David** | `rendymahaputra010@gmail.com` |
| **Member** | **Rendy Mahaputra** | `rajivcream@gmail.com` |

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**. See the [LICENSE](LICENSE) file for the full license text.

Copyright © 2026 **BARELANG** (Adib Huda Pratama, Ibnu Rasydin, Muhammad Rasyid Prasetyo, Rendy Mahaputra, Rajiv Tajusa David) — Batam State Polytechnic.

---

## 📚 References & Acknowledgments

1. **SUTD ROAR Lab:** *Open Hackathon Guidelines for Conceptual Design Submission and Judging Criteria*, Robotics and Automation Research Lab, Singapore University of Technology and Design, Oct 2026.
2. **Leadshine:** iSV2-CAN6020V48H integrated servo motor — https://www.leadshine.com/product-detail/iSV2-CAN6020V48H.html
3. **Leadshine:** iSV2-CAN8075V48G integrated servo motor — https://www.leadshine.com/network-detail/fieldbus/CANopen/c-integrated-servo-motors/iSV2-CAN8075V48G.html
4. **Open Robotics:** *ROS 2 Jazzy & Gazebo Harmonic Simulation Architecture*, IEEE Robotics & Automation, 2024.
5. **Gazebo:** Harmonic architecture (systems vs. pose updates) — https://gazebosim.org/docs/harmonic/architecture/

> Detailed geometry, analytical sizing and deterministic animation support design review. They do not constitute aircraft approval, a manufacturing drawing set or measured prototype performance.
