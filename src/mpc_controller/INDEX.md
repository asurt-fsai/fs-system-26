# INDEX - C++ MPC Controller Documentation

## Quick Navigation

### 🚀 I want to get started NOW
→ [QUICKSTART.md](QUICKSTART.md) (5 minutes)

### 📖 I want to understand the full system
→ [README.md](README.md) (15 minutes)

### 🔗 I want to connect Python to C++
→ [PYTHON_CPP_INTEGRATION.md](PYTHON_CPP_INTEGRATION.md) (10 minutes)

### ⚙️ I want to configure & tune it
→ [SETUP_SUMMARY.md](SETUP_SUMMARY.md) (10 minutes)

### 🏗️ I want to understand the architecture
→ [PYTHON_VS_CPP.md](PYTHON_VS_CPP.md) (5 minutes)

### 🐛 The build is failing
→ [docs/BUILD_TROUBLESHOOTING.md](docs/BUILD_TROUBLESHOOTING.md)

### ⚡ I want to make it faster (50x speedup)
→ [docs/NLOPT_INTEGRATION.md](docs/NLOPT_INTEGRATION.md)

### 📋 I want a complete overview
→ [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)

---

## File Directory

### Documentation Files (8 total)

| File | Purpose | Read Time |
|------|---------|-----------|
| **QUICKSTART.md** | Get running in 5 min | 5 min |
| **README.md** | Full documentation | 15 min |
| **SETUP_SUMMARY.md** | Configuration guide | 10 min |
| **PYTHON_VS_CPP.md** | Architecture rationale | 5 min |
| **PYTHON_CPP_INTEGRATION.md** | Python-C++ bridge | 10 min |
| **DELIVERY_SUMMARY.md** | Complete overview | 20 min |
| **docs/BUILD_TROUBLESHOOTING.md** | Fix build issues | 10 min |
| **docs/NLOPT_INTEGRATION.md** | Performance upgrade | 15 min |

### Header Files (6 total) - Read for Learning

| File | Concept |
|------|---------|
| `include/config.h` | Configuration parameters |
| `include/bicycle_model.h` | Vehicle dynamics |
| `include/mpc_solver.h` | Main optimization |
| `include/constraints.h` | Constraints |
| `include/utils.h` | Helpers |
| `include/mpc_controller_node.h` | ROS 2 node |

### Source Files (6 total) - Implementation

| File | Purpose |
|------|---------|
| `src/config.cpp` | Initialize defaults |
| `src/bicycle_model.cpp` | Kinematic equations |
| `src/mpc_solver.cpp` | Optimization logic |
| `src/constraints.cpp` | Constraint checking |
| `src/utils.cpp` | Helper functions |
| `src/mpc_controller_node.cpp` | ROS 2 integration |

### Build Files (2 total)

| File | Purpose |
|------|---------|
| `CMakeLists.txt` | Build configuration |
| `package.xml` | ROS 2 metadata |

---

## Reading Paths Based on Your Goal

### Path 1: "I just want to run it" ⚡
1. QUICKSTART.md
2. Build and test
3. Done!

**Time: 10 minutes**

### Path 2: "I need to integrate with my Python code" 🔗
1. QUICKSTART.md
2. PYTHON_CPP_INTEGRATION.md
3. Modify your Python node
4. Test end-to-end

**Time: 20 minutes**

### Path 3: "I want to understand everything" 📚
1. PYTHON_VS_CPP.md
2. README.md
3. SETUP_SUMMARY.md
4. Read source code headers
5. Study implementation (.cpp files)

**Time: 1 hour**

### Path 4: "I need to optimize performance" ⚡⚡
1. QUICKSTART.md (verify it works)
2. docs/NLOPT_INTEGRATION.md
3. Install NLOPT
4. Update CMakeLists.txt
5. Rebuild and test

**Time: 30 minutes**

### Path 5: "Build is failing" 🐛
1. docs/BUILD_TROUBLESHOOTING.md
2. Follow specific fix
3. Rebuild

**Time: 5-15 minutes**

---

## Search by Topic

### MPC & Control
- **Understanding MPC**: See README.md "How it Works"
- **Tuning for better tracking**: See SETUP_SUMMARY.md "Configuration"
- **Cost functions**: See src/mpc_solver.cpp

### ROS 2 & Integration
- **Python-C++ communication**: See PYTHON_CPP_INTEGRATION.md
- **Node structure**: See include/mpc_controller_node.h
- **Topics/services**: See README.md "Topics"

### Performance
- **Why C++**: See PYTHON_VS_CPP.md
- **Making it faster**: See docs/NLOPT_INTEGRATION.md
- **Profiling**: See docs/BUILD_TROUBLESHOOTING.md

### Build & Deployment
- **Build issues**: See docs/BUILD_TROUBLESHOOTING.md
- **Build configuration**: See CMakeLists.txt
- **Package setup**: See package.xml

### Learning & Development
- **Code organization**: See DELIVERY_SUMMARY.md "Code Organization"
- **Module dependencies**: See docs/NLOPT_INTEGRATION.md (system architecture)
- **Algorithm details**: See src/*.cpp (implementation)

---

## Quick Reference

### Most Important Files to Understand
1. **config.h** - Start here to understand parameters
2. **README.md** - Understand the overall system
3. **mpc_controller_node.cpp** - Understand ROS integration

### Most Important Files to Modify
1. **src/config.cpp** - Tune weight matrices (80% of performance!)
2. **CMakeLists.txt** - Add dependencies like NLOPT
3. **src/mpc_controller_node.cpp** - Modify topic names if needed

### Most Important Commands
```bash
# Build
colcon build --packages-select mpc_controller

# Run
ros2 run mpc_controller mpc_controller_node

# Check topics
ros2 topic list | grep mpc

# Monitor
ros2 topic echo /cmd_vel
```

---

## Performance Goals

| Scenario | Target | Docs |
|----------|--------|------|
| Basic tuning | ✅ Works well | SETUP_SUMMARY.md |
| Real-time control | ✅ 100+ Hz | README.md |
| High-speed system | ⚡ NLOPT needed | docs/NLOPT_INTEGRATION.md |
| Embedded hardware | ⚡ C++ advantage | PYTHON_VS_CPP.md |

---

## Support Resources

### Building
- [ROS 2 Documentation](https://docs.ros.org/en/humble/)
- [CMake Guide](https://cmake.org/documentation/)
- [Eigen Documentation](https://eigen.tuxfamily.org/)

### Debugging
- [GDB Tutorial](https://www.gnu.org/software/gdb/documentation/)
- [ROS 2 Debugging](https://docs.ros.org/en/humble/Guides/Debugging-ROS2-packages.html)

### Learning
- [MPC Theory](https://en.wikipedia.org/wiki/Model_predictive_control)
- [C++ Best Practices](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)

---

## Checklist

After reading this index:

- [ ] Picked a reading path above
- [ ] Started with appropriate documentation file
- [ ] Bookmarked files for later reference
- [ ] Ready to build and run

---

**Start here → [QUICKSTART.md](QUICKSTART.md)** 🚀
