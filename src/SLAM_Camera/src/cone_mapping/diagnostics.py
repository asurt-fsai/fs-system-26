#!/usr/bin/env python3
"""
Comprehensive Cone Mapping System Diagnostic Tool

Evaluates:
- ROS 2 communication (topics, frequencies, message flow)
- Each processing phase (inputs, outputs, transformations)
- Lifecycle management and state transitions
- Performance metrics and bottlenecks
"""

import subprocess
import time
import json
import sys
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ConeMappingDiagnostics:
    def __init__(self):
        self.source_cmd = "source /home/hazem/Desktop/FSAI/SLAM_Camera/install/setup.bash"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'warnings': 0,
            'phases': {}
        }
        self.processes = []
        
    def print_header(self, text):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def print_test(self, name, status, details=""):
        if status == "PASS":
            symbol = "✓"
            color = Colors.OKGREEN
            self.results['tests_passed'] += 1
        elif status == "FAIL":
            symbol = "✗"
            color = Colors.FAIL
            self.results['tests_failed'] += 1
        elif status == "WARN":
            symbol = "⚠"
            color = Colors.WARNING
            self.results['warnings'] += 1
        else:
            symbol = "ℹ"
            color = Colors.OKCYAN
            
        print(f"{color}{symbol} {name:<50}{Colors.ENDC}", end="")
        if details:
            print(f" {details}")
        else:
            print()
    
    def run_command(self, cmd, timeout=5):
        """Execute shell command and return output"""
        try:
            result = subprocess.run(
                f"{self.source_cmd} && {cmd}",
                shell=True,
                executable='/bin/bash',
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "TIMEOUT", -1
    
    def start_system(self):
        """Start all system components"""
        self.print_header("SYSTEM STARTUP")
        
        # Kill old processes
        subprocess.run("pkill -f 'test_case|cone_mapping|static_transform'", shell=True)
        time.sleep(1)
        
        # Start TF publisher
        print("Starting TF publisher...")
        p1 = subprocess.Popen(
            f"{self.source_cmd} && ros2 run tf2_ros static_transform_publisher 0.3 0.0 0.5 0.0 0.0 0.0 1.0 base_link zed_camera",
            shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.processes.append(p1)
        time.sleep(1)
        
        # Start simulator
        print("Starting perception simulator...")
        p2 = subprocess.Popen(
            f"{self.source_cmd} && ros2 run cone_mapping test_case_1_ideal.py",
            shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.processes.append(p2)
        time.sleep(2)
        
        # Start mapper with logging
        print("Starting cone mapping node...")
        self.log_file = "/tmp/cone_mapping_diagnostics.log"
        self.log_handle = open(self.log_file, 'w')
        p3 = subprocess.Popen(
            f"{self.source_cmd} && ros2 run cone_mapping cone_mapping_node.py --ros-args -p max_cone_height_deviation:=2.0",
            shell=True, executable='/bin/bash', stdout=self.log_handle, stderr=subprocess.STDOUT
        )
        self.processes.append(p3)
        time.sleep(3)
        
        print(f"{Colors.OKGREEN}✓ All components started{Colors.ENDC}\n")
    
    def test_ros_communication(self):
        """Test ROS 2 topic communication"""
        self.print_header("ROS 2 COMMUNICATION TESTS")
        
        # Test 1: Topic existence
        stdout, _, _ = self.run_command("ros2 topic list")
        topics = stdout.strip().split('\n')
        
        required_topics = [
            '/perception/landmarks',
            '/zed2i/zed_node/pose',
            '/map/global_cones',
            '/tf',
            '/tf_static'
        ]
        
        for topic in required_topics:
            if topic in topics:
                self.print_test(f"Topic exists: {topic}", "PASS")
            else:
                self.print_test(f"Topic exists: {topic}", "FAIL")
        
        # Test 2: Topic types
        type_checks = {
            '/perception/landmarks': 'cone_mapping/msg/LandmarkArray',
            '/zed2i/zed_node/pose': 'geometry_msgs/msg/PoseStamped',
            '/map/global_cones': 'cone_mapping/msg/LandmarkArray'
        }
        
        for topic, expected_type in type_checks.items():
            stdout, _, _ = self.run_command(f"ros2 topic type {topic}")
            actual_type = stdout.strip()
            if expected_type in actual_type:
                self.print_test(f"Topic type: {topic}", "PASS", f"({expected_type})")
            else:
                self.print_test(f"Topic type: {topic}", "FAIL", f"Expected {expected_type}, got {actual_type}")
        
        # Test 3: Publisher/Subscriber counts
        for topic in ['/perception/landmarks', '/zed2i/zed_node/pose', '/map/global_cones']:
            stdout, _, _ = self.run_command(f"ros2 topic info {topic}")
            pub_count = stdout.count("Publisher count:")
            sub_count = stdout.count("Subscription count:")
            
            if pub_count > 0 and sub_count > 0:
                # Extract actual counts
                for line in stdout.split('\n'):
                    if 'Publisher count:' in line:
                        pubs = line.split(':')[1].strip()
                    if 'Subscription count:' in line:
                        subs = line.split(':')[1].strip()
                self.print_test(f"Pub/Sub: {topic}", "PASS", f"Pubs:{pubs} Subs:{subs}")
            else:
                self.print_test(f"Pub/Sub: {topic}", "WARN", "No connections")
    
    def test_message_frequencies(self):
        """Test message publication frequencies"""
        self.print_header("MESSAGE FREQUENCY TESTS")
        
        freq_tests = {
            '/perception/landmarks': (9.0, 11.0, "10 Hz"),
            '/zed2i/zed_node/pose': (9.0, 11.0, "10 Hz"),
            '/map/global_cones': (9.0, 11.0, "10 Hz")
        }
        
        for topic, (min_hz, max_hz, expected) in freq_tests.items():
            stdout, stderr, _ = self.run_command(f"timeout 3 ros2 topic hz {topic}", timeout=4)
            
            if "average rate:" in stdout:
                # Extract frequency
                for line in stdout.split('\n'):
                    if 'average rate:' in line:
                        rate = float(line.split('average rate:')[1].split()[0])
                        if min_hz <= rate <= max_hz:
                            self.print_test(f"Frequency: {topic}", "PASS", f"{rate:.1f} Hz (expected {expected})")
                        else:
                            self.print_test(f"Frequency: {topic}", "WARN", f"{rate:.1f} Hz (expected {expected})")
                        break
            else:
                self.print_test(f"Frequency: {topic}", "FAIL", "No data published")
    
    def test_message_content(self):
        """Test message content and structure"""
        self.print_header("MESSAGE CONTENT TESTS")
        
        # Test perception landmarks
        stdout, _, _ = self.run_command("timeout 2 ros2 topic echo /perception/landmarks --once", timeout=3)
        if stdout:
            landmark_count = stdout.count("position:")
            if landmark_count > 0:
                self.print_test("Perception publishing landmarks", "PASS", f"{landmark_count} landmarks")
                self.results['phases']['perception_output'] = landmark_count
            else:
                self.print_test("Perception publishing landmarks", "WARN", "Empty array")
        else:
            self.print_test("Perception publishing landmarks", "FAIL", "No message received")
        
        # Test vehicle pose
        stdout, _, _ = self.run_command("timeout 2 ros2 topic echo /zed2i/zed_node/pose --once", timeout=3)
        if "position:" in stdout and "orientation:" in stdout:
            # Extract position
            for line in stdout.split('\n'):
                if 'x:' in line and 'position' in stdout[:stdout.index(line)]:
                    x_val = line.split('x:')[1].strip()
                    self.print_test("Vehicle pose publishing", "PASS", f"x={x_val}m")
                    break
        else:
            self.print_test("Vehicle pose publishing", "FAIL", "Invalid pose message")
        
        # Test global map
        stdout, _, _ = self.run_command("timeout 2 ros2 topic echo /map/global_cones --once", timeout=3)
        if stdout:
            confirmed_count = stdout.count("position:")
            self.print_test("Global map publishing", "PASS", f"{confirmed_count} confirmed landmarks")
            self.results['phases']['final_output'] = confirmed_count
        else:
            self.print_test("Global map publishing", "FAIL", "No message received")
    
    def test_tf_transforms(self):
        """Test TF transform tree"""
        self.print_header("TF TRANSFORM TESTS")
        
        # Test static transform
        stdout, _, _ = self.run_command("ros2 run tf2_ros tf2_echo base_link zed_camera", timeout=2)
        if "Translation:" in stdout and "Rotation:" in stdout:
            self.print_test("Static TF: base_link → zed_camera", "PASS")
        else:
            self.print_test("Static TF: base_link → zed_camera", "FAIL", "Transform not available")
        
        # Test TF tree
        stdout, _, _ = self.run_command("ros2 run tf2_tools view_frames.py", timeout=3)
        if "map" in stdout or "base_link" in stdout:
            self.print_test("TF tree structure", "PASS")
        else:
            self.print_test("TF tree structure", "WARN", "Limited TF data")
    
    def analyze_processing_pipeline(self):
        """Analyze each phase of the processing pipeline"""
        self.print_header("PROCESSING PIPELINE ANALYSIS")
        
        # Wait for some processing
        print("Collecting pipeline data (10 seconds)...")
        time.sleep(10)
        
        # Read log file
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Phase 1: Transform & Gating
        phase1_lines = [line for line in log_content.split('\n') if 'Phase 1:' in line]
        if phase1_lines:
            last_phase1 = phase1_lines[-1]
            if '->' in last_phase1:
                parts = last_phase1.split('->')
                raw = parts[0].split('Phase 1:')[1].strip().split()[0]
                gated = parts[1].strip().split()[0]
                self.print_test("Phase 1: Transform & Gating", "PASS", f"{raw} raw → {gated} gated")
                self.results['phases']['phase1'] = {'raw': raw, 'gated': gated}
                
                if int(gated) == 0 and int(raw) > 0:
                    self.print_test("  └─ Gating effectiveness", "WARN", "All detections filtered out")
        else:
            self.print_test("Phase 1: Transform & Gating", "FAIL", "No Phase 1 logs found")
        
        # Phase 2: Data Association
        phase2_lines = [line for line in log_content.split('\n') if 'Phase 2:' in line]
        if phase2_lines:
            last_phase2 = phase2_lines[-1]
            if 'matches' in last_phase2:
                # Parse: "Phase 2: X matches, Y new detections, Z unmatched landmarks"
                parts = last_phase2.split('Phase 2:')[1].strip()
                matches = parts.split('matches')[0].strip()
                self.print_test("Phase 2: Data Association", "PASS", f"{matches} matches found")
                self.results['phases']['phase2'] = {'matches': matches}
        else:
            self.print_test("Phase 2: Data Association", "FAIL", "No Phase 2 logs found")
        
        # Synchronized callbacks
        callback_lines = [line for line in log_content.split('\n') if 'Callbacks:' in line]
        if callback_lines:
            last_callback = callback_lines[-1]
            callback_count = last_callback.split('Callbacks:')[1].strip()
            self.print_test("Synchronized callbacks", "PASS", f"{callback_count} callbacks processed")
            self.results['phases']['callbacks'] = callback_count
        else:
            self.print_test("Synchronized callbacks", "FAIL", "No callback logs found")
        
        # Map statistics
        map_lines = [line for line in log_content.split('\n') if 'Map:' in line and 'Confirmed:' in line]
        if map_lines:
            last_map = map_lines[-1]
            # Parse: "Map: X total | Confirmed: Y | Tentative: Z | Lost: W"
            total = last_map.split('total')[0].split('Map:')[1].strip()
            confirmed = last_map.split('Confirmed:')[1].split('|')[0].strip()
            tentative = last_map.split('Tentative:')[1].split('|')[0].strip()
            lost = last_map.split('Lost:')[1].split('|')[0].strip()
            
            self.print_test("Lifecycle Management", "PASS", 
                          f"Total:{total} Confirmed:{confirmed} Tentative:{tentative} Lost:{lost}")
            self.results['phases']['lifecycle'] = {
                'total': total, 'confirmed': confirmed, 
                'tentative': tentative, 'lost': lost
            }
            
            if int(confirmed) > 0:
                self.print_test("  └─ Landmark confirmation", "PASS", f"{confirmed} landmarks confirmed")
            else:
                self.print_test("  └─ Landmark confirmation", "WARN", "No landmarks confirmed yet")
        else:
            self.print_test("Lifecycle Management", "FAIL", "No map statistics found")
    
    def test_parameter_loading(self):
        """Test parameter loading"""
        self.print_header("PARAMETER LOADING TESTS")
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Check if parameters were loaded
        if 'Loaded parameters:' in log_content:
            for line in log_content.split('\n'):
                if 'Loaded parameters:' in line:
                    params = line.split('Loaded parameters:')[1].strip()
                    self.print_test("Parameter loading", "PASS", params)
                    
                    # Verify height deviation
                    if 'height_dev=2.0m' in line:
                        self.print_test("  └─ Height deviation parameter", "PASS", "2.0m (correct)")
                    else:
                        self.print_test("  └─ Height deviation parameter", "WARN", "Not 2.0m")
                    break
        else:
            self.print_test("Parameter loading", "FAIL", "No parameter loading logs")
    
    def generate_report(self):
        """Generate final diagnostic report"""
        self.print_header("DIAGNOSTIC SUMMARY")
        
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        pass_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests:    {total_tests}")
        print(f"Passed:         {Colors.OKGREEN}{self.results['tests_passed']}{Colors.ENDC}")
        print(f"Failed:         {Colors.FAIL}{self.results['tests_failed']}{Colors.ENDC}")
        print(f"Warnings:       {Colors.WARNING}{self.results['warnings']}{Colors.ENDC}")
        print(f"Pass Rate:      {Colors.OKGREEN if pass_rate >= 80 else Colors.WARNING}{pass_rate:.1f}%{Colors.ENDC}")
        
        # Overall status
        print(f"\n{Colors.BOLD}Overall Status:{Colors.ENDC} ", end="")
        if self.results['tests_failed'] == 0 and pass_rate >= 90:
            print(f"{Colors.OKGREEN}✓ SYSTEM HEALTHY{Colors.ENDC}")
        elif self.results['tests_failed'] <= 2:
            print(f"{Colors.WARNING}⚠ MINOR ISSUES{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ CRITICAL ISSUES{Colors.ENDC}")
        
        # Save JSON report
        report_file = "/tmp/cone_mapping_diagnostic_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Colors.OKCYAN}Detailed log: {self.log_file}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}JSON report:  {report_file}{Colors.ENDC}")
    
    def cleanup(self):
        """Stop all processes"""
        print(f"\n{Colors.OKCYAN}Cleaning up...{Colors.ENDC}")
        for p in self.processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except:
                try:
                    p.kill()
                except:
                    pass
        
        if hasattr(self, 'log_handle'):
            self.log_handle.close()
    
    def run_full_diagnostics(self):
        """Run complete diagnostic suite"""
        try:
            self.start_system()
            self.test_ros_communication()
            self.test_message_frequencies()
            self.test_message_content()
            self.test_tf_transforms()
            self.test_parameter_loading()
            self.analyze_processing_pipeline()
            self.generate_report()
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Diagnostics interrupted by user{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.FAIL}Error during diagnostics: {e}{Colors.ENDC}")
        finally:
            self.cleanup()

def main():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║     CONE MAPPING SYSTEM - COMPREHENSIVE DIAGNOSTICS TOOL          ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    diagnostics = ConeMappingDiagnostics()
    diagnostics.run_full_diagnostics()
    
    print(f"\n{Colors.OKGREEN}Diagnostics complete!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
