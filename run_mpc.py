#!/usr/bin/env python3
"""
Direct MPC Launch Script with Bicycle Simulator and RViz

This script directly runs the MPC system without relying on ROS 2 package resource discovery.
Launches:
  - Bicycle Simulator
  - MPC Controller Node
  - MPC Visualizer
  - RViz2
"""

import sys
import os
import subprocess
import time

# Absolute paths
WORKSPACE_ROOT = "/home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26"
INSTALL_ROOT = os.path.join(WORKSPACE_ROOT, "install")
EXEC_DIR = os.path.join(INSTALL_ROOT, "mpc_controller", "lib", "mpc_controller")

def main():
    print("[INFO] Starting MPC Controller System with Simulator and RViz...")
    print(f"[INFO] Workspace: {WORKSPACE_ROOT}")
    print(f"[INFO] Install directory: {INSTALL_ROOT}")
    
    # Get the paths to the executables
    bicycle_sim_exec = os.path.join(EXEC_DIR, "bicycle_simulator")
    mpc_controller_exec = os.path.join(EXEC_DIR, "mpc_controller_node")
    mpc_visualizer_exec = os.path.join(EXEC_DIR, "mpc_visualizer")
    
    # Check if executables exist
    for name, path in [("Bicycle Simulator", bicycle_sim_exec), 
                       ("MPC Controller", mpc_controller_exec),
                       ("MPC Visualizer", mpc_visualizer_exec)]:
        if not os.path.exists(path):
            print(f"[ERROR] {name} executable not found: {path}")
            return 1
        print(f"[INFO] Found {name}: {path}")
    
    # Set up environment
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{WORKSPACE_ROOT}/src/mpc_controller/src/install/lib:{env.get('LD_LIBRARY_PATH', '')}"
    
    processes = []
    
    try:
        print("\n[INFO] Launching Bicycle Simulator...")
        bicycle_proc = subprocess.Popen(
            [bicycle_sim_exec],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("Bicycle Simulator", bicycle_proc))
        time.sleep(1)
        
        print("[INFO] Launching MPC Controller Node...")
        mpc_proc = subprocess.Popen(
            [mpc_controller_exec],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("MPC Controller", mpc_proc))
        time.sleep(1)
        
        print("[INFO] Launching MPC Visualizer...")
        viz_proc = subprocess.Popen(
            [mpc_visualizer_exec],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("MPC Visualizer", viz_proc))
        time.sleep(1)
        
        print("[INFO] Attempting to launch RViz2...")
        try:
            rviz_proc = subprocess.Popen(
                ["rviz2"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            processes.append(("RViz2", rviz_proc))
        except FileNotFoundError:
            print("[WARN] RViz2 not installed. Skipping RViz2 launch.")
        
        print("\n✓ All processes launched successfully!")
        print("[INFO] - Bicycle Simulator is generating vehicle dynamics")
        print("[INFO] - MPC Controller is computing optimal commands")
        print("[INFO] - MPC Visualizer is publishing markers")
        print("\n[INFO] Press Ctrl+C to shutdown...\n")
        
        # Read and display output from processes
        import threading
        
        def read_output(proc, name):
            """Read and print output from a process"""
            try:
                for line in proc.stdout:
                    if line:
                        print(f"[{name}] {line.rstrip()}")
            except:
                pass
        
        # Start threads to read output
        threads = []
        for name, proc in processes:
            if hasattr(proc, 'stdout') and proc.stdout:
                thread = threading.Thread(target=read_output, args=(proc, name), daemon=True)
                thread.start()
                threads.append(thread)
        
        # Wait for all processes
        while True:
            all_running = True
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"[WARN] {name} has exited with code {proc.returncode}")
                    all_running = False
            
            if not all_running:
                break
            time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down all processes...")
        for name, proc in reversed(processes):
            try:
                print(f"[INFO] Stopping {name}...")
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print(f"[WARN] Force killing {name}...")
                proc.kill()
                proc.wait()
        print("[INFO] Shutdown complete")
        return 0
    
    except Exception as e:
        print(f"[ERROR] {e}")
        for name, proc in reversed(processes):
            try:
                proc.terminate()
            except:
                pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
