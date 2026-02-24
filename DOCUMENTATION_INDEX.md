# MPC Controller Documentation Index - FSAI 2026

## 📍 You Are Here

This index helps you navigate all the documentation for the MPC Controller.

---

## 📚 Documentation Files (Read in This Order)

### 🚀 **START HERE** - For First Time Users

1. **[QUICKSTART_GUIDE.md](./src/mpc_controller/QUICKSTART_GUIDE.md)**
   - ⏱️ Time: 30 minutes
   - 📝 Content: Overview, 5-minute setup, key concepts
   - 🎯 Goal: Get up and running immediately
   - ✅ Best for: First-time users, quick reference

### 📖 **MAIN REFERENCE** - For Learning & Tuning

2. **[DOCUMENTATION_GUIDE.md](./src/mpc_controller/DOCUMENTATION_GUIDE.md)**
   - ⏱️ Time: 2-4 hours (read in sections)
   - 📝 Content: 40+ pages, complete technical guide
   - 🎯 Goal: Deep understanding of every component
   - ✅ Best for: In-depth learning, troubleshooting, tuning

3. **[DOCUMENTATION_COMPLETE.md](./DOCUMENTATION_COMPLETE.md)**
   - ⏱️ Time: 15 minutes
   - 📝 Content: Summary of all documentation
   - 🎯 Goal: Understand documentation structure
   - ✅ Best for: Navigation guide

---

## 💻 Code-Embedded Documentation

Each source file contains extensive comments explaining implementation:

### Header Files (Most Important - Read These!)

#### **config.h** - Configuration Parameters
- 📍 Location: `include/mpc_controller/config.h`
- 📝 Comments: 300+ lines
- 🎯 Topic: All tunable parameters explained
- ✅ Read for: Parameter meaning, FSAI 2026 values, tuning guidance
- **KEY SECTION**: Cost weights (Q, R, Q_terminal) explanation

#### **bicycle_model.h** - Vehicle Dynamics
- 📍 Location: `include/mpc_controller/bicycle_model.h`
- 📝 Comments: 400+ lines
- 🎯 Topics: 
  - Kinematic bicycle model equations
  - Why kinematic model suitable for FS
  - RK4 integration theory
  - Trajectory prediction
  - Jacobian linearization
- ✅ Read for: Understanding vehicle dynamics
- **KEY SECTIONS**: 
  - Bicycle geometry insight
  - RK4 accuracy comparison
  - Practical examples

#### **mpc_solver.h** - MPC Optimization
- 📍 Location: `include/mpc_controller/mpc_solver.h`
- 📝 Comments: Detailed
- 🎯 Topics:
  - Optimization problem formulation
  - Receding horizon strategy
  - Warm-starting
- ✅ Read for: How MPC control works

#### **mpc_controller_node.h** - ROS 2 Integration
- 📍 Location: `include/mpc_controller/mpc_controller_node.h`
- 📝 Comments: Detailed
- 🎯 Topics:
  - ROS 2 subscribers/publishers
  - Control loop implementation
  - Receding horizon execution
- ✅ Read for: How vehicle integration works

#### **constraints.h** - Safety Limits
- 📍 Location: `include/mpc_controller/constraints.h`
- 📝 Comments: Clear and concise
- 🎯 Topics: Constraint definitions, safety enforcement
- ✅ Read for: Understanding limit enforcement

#### **utils.h** - Helper Functions
- 📍 Location: `include/mpc_controller/utils.h`
- 📝 Comments: Detailed with examples
- 🎯 Topics:
  - wrapAngle()
  - saturate()
  - rateLimit()
  - getReferenceError()
- ✅ Read for: Understanding control utilities

---

## 🎓 Learning Paths

### Path 1: Quick Setup (2 hours)
```
1. Read: QUICKSTART_GUIDE.md (30 min)
2. Measure: Vehicle parameters (30 min)
3. Setup: Install and build (30 min)
4. Test: Run with defaults (30 min)
```

### Path 2: Practical Tuning (1 day)
```
1. Complete: Path 1 (2 hours)
2. Read: DOCUMENTATION_GUIDE.md - Configuration section (30 min)
3. Read: DOCUMENTATION_GUIDE.md - Tuning section (1 hour)
4. Test: Create 3 tuning profiles (2 hours)
5. Analyze: Compare results (30 min)
```

### Path 3: Deep Understanding (3 days)
```
1. Complete: Path 2 (1 day)
2. Read: DOCUMENTATION_GUIDE.md - All sections (1 day)
3. Study: Code comments in header files (3 hours)
4. Experiment: Modify parameters, test (4 hours)
```

### Path 4: Expert Development (1 week)
```
1. Complete: Path 3 (3 days)
2. Study: Source file implementations (.cpp files) (1 day)
3. Advanced: Read "Advanced Topics" section (1 day)
4. Development: Implement custom features (2 days)
```

---

## 🔍 Finding Information by Topic

### "I want to understand..."

#### Basic Concepts
- **What is MPC?** → QUICKSTART_GUIDE.md, then "Core Concepts" in DOCUMENTATION_GUIDE.md
- **What is receding horizon?** → DOCUMENTATION_GUIDE.md "Receding Horizon" section
- **How does the controller work?** → mpc_solver.h comments + DOCUMENTATION_GUIDE.md
- **What parameters exist?** → config.h comments + DOCUMENTATION_GUIDE.md "Configuration Guide"

#### Vehicle Dynamics
- **Kinematic bicycle model** → bicycle_model.h comments (400+ lines!)
- **Why RK4 integration?** → bicycle_model.h "Runge-Kutta 4" section
- **Vehicle state representation** → DOCUMENTATION_GUIDE.md "Core Concepts"
- **Control input meaning** → config.h "CONTROL INPUT" section

#### MPC Control
- **How MPC solves problems** → mpc_solver.h comments + DOCUMENTATION_GUIDE.md "MPC Solver"
- **What is warm-starting?** → DOCUMENTATION_GUIDE.md "MPC Solver" section
- **Cost function explanation** → config.cpp comments (300+ lines!)
- **Constraint handling** → constraints.h + DOCUMENTATION_GUIDE.md

#### Tuning & Configuration
- **How to tune for my vehicle** → DOCUMENTATION_GUIDE.md "FSAI 2026 Tuning Guide"
- **What does Q matrix do?** → config.h comments + config.cpp
- **What does R matrix do?** → config.h comments + config.cpp
- **Tuning table for common problems** → DOCUMENTATION_GUIDE.md "Performance Table"

#### ROS 2 & Integration
- **How to connect to vehicle** → mpc_controller_node.h comments
- **What topics does it use?** → mpc_controller_node.h + DOCUMENTATION_GUIDE.md
- **How to visualize predictions** → QUICKSTART_GUIDE.md "Debugging" section
- **How to adjust parameters at runtime** → DOCUMENTATION_GUIDE.md "Online Parameter Adjustment"

#### Troubleshooting
- **Vehicle oscillates** → DOCUMENTATION_GUIDE.md "Troubleshooting"
- **Solver too slow** → DOCUMENTATION_GUIDE.md "Troubleshooting"
- **Can't turn tight enough** → DOCUMENTATION_GUIDE.md "Troubleshooting"
- **General issues** → DOCUMENTATION_GUIDE.md "Common Issues" table

---

## 📊 Documentation Coverage

| Topic | Location | Detail Level |
|-------|----------|--------------|
| Getting started | QUICKSTART_GUIDE.md | ⭐⭐⭐⭐⭐ |
| Configuration | config.h comments | ⭐⭐⭐⭐⭐ |
| Vehicle dynamics | bicycle_model.h comments | ⭐⭐⭐⭐⭐ |
| MPC algorithm | mpc_solver.h comments | ⭐⭐⭐⭐ |
| ROS 2 integration | mpc_controller_node.h comments | ⭐⭐⭐⭐ |
| Tuning guide | DOCUMENTATION_GUIDE.md | ⭐⭐⭐⭐⭐ |
| Troubleshooting | DOCUMENTATION_GUIDE.md | ⭐⭐⭐⭐ |
| Theory background | DOCUMENTATION_GUIDE.md | ⭐⭐⭐ |
| Advanced topics | DOCUMENTATION_GUIDE.md | ⭐⭐⭐ |
| Code implementation | Source files (.cpp) | ⭐⭐ |

---

## 🎯 Quick Navigation by Role

### I'm a Driver/Team Manager
- Start: QUICKSTART_GUIDE.md
- Focus: "How to Tune" sections
- Goal: Understand tuning process
- Skip: Theory sections

### I'm a Control Engineer
- Start: DOCUMENTATION_GUIDE.md "Core Concepts"
- Focus: Theory, math, algorithm
- Goal: Understand full system design
- Read: All theory sections

### I'm a Embedded Systems Engineer
- Start: Code comments
- Focus: Implementation details
- Goal: Optimize code
- Read: .cpp source files

### I'm a Robotics Student
- Start: QUICKSTART_GUIDE.md
- Then: DOCUMENTATION_GUIDE.md (all sections)
- Focus: Learning and understanding
- Goal: Master MPC control concepts

### I'm in a Time Crunch
- Start: QUICKSTART_GUIDE.md (30 min)
- Then: config.h comments (30 min)
- Skip: Advanced/theory sections
- Goal: Get vehicle running

---

## 📋 All Documentation Files

### Root Level
- **DOCUMENTATION_COMPLETE.md** - Summary of all docs

### In src/mpc_controller/
- **QUICKSTART_GUIDE.md** - Quick start for all users ✅ START HERE
- **DOCUMENTATION_GUIDE.md** - Comprehensive 40+ page reference
- **QUICKSTART.md** - Original quick start
- **README.md** - Project overview
- **INDEX.md** - Original index
- **CHECKLIST.md** - Delivery checklist
- **SETUP_SUMMARY.md** - Setup instructions
- **DELIVERY_SUMMARY.md** - Delivery notes

### In src/mpc_controller/include/mpc_controller/
- **config.h** - 300+ lines: Parameter explanation ✅ READ THESE
- **bicycle_model.h** - 400+ lines: Dynamics explanation ✅ READ THESE
- **constraints.h** - Constraint definitions
- **mpc_solver.h** - MPC solver algorithm
- **utils.h** - Helper functions
- **mpc_controller_node.h** - ROS 2 integration

### In src/mpc_controller/src/
- **config.cpp** - Default weight initialization
- **bicycle_model.cpp** - RK4 implementation
- **constraints.cpp** - Constraint enforcement
- **mpc_solver.cpp** - Optimization implementation
- **utils.cpp** - Helper function implementation
- **mpc_controller_node.cpp** - ROS 2 node implementation

---

## ✅ Verification Checklist

Use this to verify documentation completeness:

- [ ] Read QUICKSTART_GUIDE.md
- [ ] Found config.h parameter explanations
- [ ] Understood bicycle_model.h dynamics
- [ ] Reviewed DOCUMENTATION_GUIDE.md structure
- [ ] Located MPC solver explanation
- [ ] Found tuning guide
- [ ] Located troubleshooting section
- [ ] Verified all header files have comments
- [ ] Ready to start implementation

---

## 🚀 Next Steps

1. **Choose your learning path** above
2. **Start with QUICKSTART_GUIDE.md**
3. **Read code comments in header files**
4. **Consult DOCUMENTATION_GUIDE.md** for deep dives
5. **Set up your vehicle parameters**
6. **Test and tune** for your vehicle
7. **Compete at FSAI 2026!**

---

## 💡 Pro Tips

- 💾 **Bookmark this file** for quick navigation
- 📖 **Read on tablet** for easier reference during development
- 🔍 **Use Find function** in DOCUMENTATION_GUIDE.md
- 📝 **Take notes** while reading
- 💻 **Keep terminal open** with `ros2 topic echo /mpc/debug`
- 📊 **Monitor predictions** in RVIZ while reading code
- 🎯 **Iterate**: Test, adjust, measure, repeat

---

## 🏆 Success Looks Like

After using this documentation, you will:
- ✅ Understand every component of the MPC
- ✅ Successfully tune for your vehicle
- ✅ Know how to troubleshoot issues
- ✅ Be ready to compete at FSAI 2026
- ✅ Have a foundation for advanced improvements

---

**Documentation Index Version**: 1.0  
**Last Updated**: February 5, 2026  
**Status**: Complete and Ready for Use

**Ready to get started? Open QUICKSTART_GUIDE.md now!** 🚀

