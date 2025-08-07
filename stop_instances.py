#!/usr/bin/env python3
"""
Utility script to stop running Gradio instances and free up ports
"""

import subprocess
import sys
import os

def find_processes_on_ports(ports):
    """Find processes running on specified ports"""
    processes = []
    
    for port in ports:
        try:
            # Use netstat to find processes on the port
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ['netstat', '-ano', '-p', 'tcp'],
                    capture_output=True,
                    text=True
                )
                
                lines = result.stdout.split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            processes.append((port, pid))
                            print(f"📍 Found process on port {port}: PID {pid}")
            else:  # Unix/Linux/Mac
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip():
                    pid = result.stdout.strip()
                    processes.append((port, pid))
                    print(f"📍 Found process on port {port}: PID {pid}")
                    
        except Exception as e:
            print(f"⚠️  Error checking port {port}: {e}")
    
    return processes

def stop_processes(processes):
    """Stop the specified processes"""
    for port, pid in processes:
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
            else:  # Unix/Linux/Mac
                subprocess.run(['kill', '-9', pid], check=True)
            print(f"✅ Stopped process {pid} on port {port}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to stop process {pid} on port {port}")
        except Exception as e:
            print(f"❌ Error stopping process {pid}: {e}")

def main():
    print("🔍 Checking for running Smart Trip Scout instances...")
    
    # Common Gradio ports
    ports_to_check = [7860, 7861, 7862, 7863, 7864]
    
    processes = find_processes_on_ports(ports_to_check)
    
    if not processes:
        print("✅ No processes found on common Gradio ports")
        return
    
    print(f"\n🛑 Found {len(processes)} process(es) to stop")
    
    response = input("\nDo you want to stop these processes? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        stop_processes(processes)
        print("\n🎉 Done! You can now start the application.")
    else:
        print("\n📝 Processes left running. Use a different port or stop them manually.")
        print("   Alternative: The updated app.py will try different ports automatically.")

if __name__ == "__main__":
    main()
