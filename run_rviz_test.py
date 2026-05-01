#!/usr/bin/env python3
"""
RViz Test Runner - Launches bicycle simulator, MPC controller, visualizer, and RViz
This script loads track.csv and visualizes the vehicle movement in RViz
"""

import sys
import os
import subprocess
import time

# Absolute paths
WORKSPACE_ROOT = "/home/ibrahim-el-dawy/FSAI_2026/MPC_Controller/Control_Project/fs-system-26"
INSTALL_ROOT = os.path.join(WORKSPACE_ROOT, "install")
EXEC_DIR = os.path.join(INSTALL_ROOT, "mpc_controller", "lib", "mpc_controller")
CONFIG_DIR = os.path.join(INSTALL_ROOT, "mpc_controller", "share", "mpc_controller", "config")
TRACK_CSV = os.path.join(CONFIG_DIR, "track.csv")
RVIZ_CONFIG = os.path.join(CONFIG_DIR, "mpc_test.rviz")

def main():
    print("[INFO] Starting RViz Test - Bicycle Simulator with MPC and Track Data...")
    print(f"[INFO] Workspace: {WORKSPACE_ROOT}")
    print(f"[INFO] Track file: {TRACK_CSV}")
    print(f"[INFO] RViz config: {RVIZ_CONFIG}")
    
    # Verify track.csv exists
    if not os.path.exists(TRACK_CSV):
        print(f"[ERROR] Track file not found: {TRACK_CSV}")
        return 1
    
    print(f"[INFO] ✓ Track file found: {os.path.getsize(TRACK_CSV)} bytes")
    
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
        print(f"[INFO] ✓ Found {name}")
    
    # Set up environment
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{WORKSPACE_ROOT}/src/mpc_controller/src/install/lib:{env.get('LD_LIBRARY_PATH', '')}"
    env["ROS_DOMAIN_ID"] = "0"
    
    processes = []
    
    try:
        print("\n[INFO] ════════════════════════════════════════")
        print("[INFO] Launching Bicycle Simulator (loading track.csv)...")
        print("[INFO] ════════════════════════════════════════\n")
        
        bicycle_proc = subprocess.Popen(
            [bicycle_sim_exec],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("Bicycle Simulator", bicycle_proc))
        time.sleep(2)
        
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
            if os.path.exists(RVIZ_CONFIG):
                rviz_proc = subprocess.Popen(
                    ["rviz2", "-d", RVIZ_CONFIG],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"[INFO] ✓ RViz2 launched with config: {RVIZ_CONFIG}")
            else:
                rviz_proc = subprocess.Popen(
                    ["rviz2"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("[INFO] ✓ RViz2 launched (no config file)")
            processes.append(("RViz2", rviz_proc))
        except FileNotFoundError:
            print("[WARN] RViz2 not installed. Continuing without visualization UI.")
            print("[INFO] You can connect to this system from another machine with RViz2 installed.")
        
        print("\n" + "="*60)
        print("✓ ALL SYSTEMS OPERATIONAL!")
        print("="*60)
        print("[INFO] • Bicycle Simulator - Loading and following track.csv")
        print("[INFO] • MPC Controller - Computing optimal control commands")
        print("[INFO] • MPC Visualizer - Publishing RViz visualization markers")
        print("[INFO] • RViz2 - Displaying vehicle, track, and constraints")
        print("\n[INFO] Vehicle is moving along the track with MPC control!")
        print("[INFO] Press Ctrl+C to shutdown all systems...\n")
        print("="*60 + "\n")
        
        # Read and display output from processes
        import threading
        import select
        
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
                    print(f"\n[WARN] {name} has exited with code {proc.returncode}")
                    all_running = False
            
            if not all_running:
                break
            time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n\n[INFO] ════════════════════════════════════════")
        print("[INFO] Shutdown signal received!")
        print("[INFO] ════════════════════════════════════════")
        print("[INFO] Shutting down all processes...")
        
        for name, proc in reversed(processes):
            try:
                print(f"[INFO] Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                    print(f"[INFO] ✓ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"[WARN] {name} did not stop, force killing...")
                    proc.kill()
                    proc.wait()
                    print(f"[INFO] ✓ {name} force killed")
            except Exception as e:
                print(f"[ERROR] Error stopping {name}: {e}")
        
        print("[INFO] ════════════════════════════════════════")
        print("[INFO] Shutdown complete")
        print("[INFO] ════════════════════════════════════════")
        return 0
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        for name, proc in reversed(processes):
            try:
                proc.terminate()
            except:
                pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
