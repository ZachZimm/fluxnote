import subprocess
import psutil
import platform

def get_gpu_info() -> dict:
    # Not sure how to determine the platform
    # or what commands should be run for non-NVIDIA users

    # if IS_NVIDIA:
    if platform.system() == "Linux":
        try:
            # Run nvidia-smi command
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.total,memory.used,memory.free', '--format=csv,noheader,nounits'],
                                    capture_output=True, text=True, check=True)
            # Extract the output
            output = result.stdout.strip()
            gpu_info = output.split(', ')
            gpu_usage = int(gpu_info[0])
            total_vram = int(gpu_info[1])
            used_vram = int(gpu_info[2])
            free_vram = int(gpu_info[3])
            vram_usage = round((used_vram/total_vram)*100,2)

            return {"gpu_usage":gpu_usage,"total_vram":total_vram, "used_vram":used_vram, "free_vram":free_vram, "vram_usage": vram_usage, "gpu_platform":"NVIDIA"}

        except subprocess.CalledProcessError as e:
            print(f"Error running nvidia-smi: {e}")
            return None, None, None
        # elif IS_AMD:
        # elif IS_INTEL:
        # elif IS_METAL:
        # elif IS_ARM:
        # else
    else: 
        return {"gpu_usage":0,"total_vram":0, "used_vram":0, "free_vram":0, "vram_usage": 0, "gpu_platform":"UNKNOWN"}

def get_cpu_info() -> dict:
    num_cores = psutil.cpu_count(logical=True)
    core_usages = psutil.cpu_percent(percpu=True)

    # Calculate min, max, and average CPU usage
    min_core_usage = min(core_usages)
    max_core_usage = max(core_usages)
    avg_core_usage = round(sum(core_usages) / len(core_usages), 2)

    cpu_info = {
        "min_core_usage": min_core_usage,
        "max_core_usage": max_core_usage,
        "avg_core_usage": avg_core_usage,
        "num_cores": num_cores
    }

    # Check if the platform is Intel and running on Linux
    if platform.system() == "Linux":
        try:
            # Run the sensors command to get temperature information
            result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
            output = result.stdout

            core_temperatures = [] 
            for line in output.splitlines():
                if "Core" in line:
                    parts = line.split()
                    # Extract temperature value, removing the '°C' symbol
                    temp = float(parts[2].strip('+°C'))
                    core_temperatures.append(temp)

            if core_temperatures:
                min_temp = min(core_temperatures)
                max_temp = max(core_temperatures)
                avg_temp = round(sum(core_temperatures) / len(core_temperatures), 2)

                cpu_info.update({
                    "min_temp": min_temp,
                    "max_temp": max_temp,
                    "avg_temp": avg_temp
                })

        except subprocess.CalledProcessError as e:
            print(f"Error running sensors: {e}")

    return cpu_info

def get_disk_info():
    try:
        if platform.system() == "Windows":
            # Run wmic command
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            disk_info = output.split('\n')[1]
            return {"disk_info":disk_info}
        # Run df command - 
        # I am sure there is a better way to get disk info, this is almost not worth doing. It assumes the current directory contains the databases. For now, it is fine.
        if platform.system() == "Linux" or platform.system() == "Darwin":
            result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            disk_info = output.split('\n')[-1]
            return {"disk_info":disk_info}

    except subprocess.CalledProcessError as e:
        print(f"Error running df -h: {e}")
        return None


if __name__ == "__main__":
    sys_info = [get_gpu_info(), get_cpu_info(), get_disk_info()]
    for device_info in sys_info:
        for key in device_info:
            print(key, ":", device_info[key])
    