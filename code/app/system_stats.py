import subprocess
import psutil
import socket
import datetime
from Logger import Logger

class SystemStats:
    @staticmethod
    def get_cpu_temp():
        """Gets the tempurature of the CPU from the system (raspberry pi 4 model B)

        Returns:
            String: tempurature 
        """
        try:
            temp_str = subprocess.getoutput("cat /sys/class/thermal/thermal_zone0/temp") # get the temp of the raspie
            if temp_str.isdigit(): # if its a float number
                temp = round(int(temp_str) / 1000, 1) # cast to string
                Logger.info(f"CPU temp read successfully: {temp}°C") # log text with temp number
                return temp # return temp
            else: # if it doesn't exist or not a digit
                Logger.warning(f"Unexpected CPU temp format: '{temp_str}'") # log the warning
                return "N/A" # return N/A so its not empty space
        except Exception as e:  # catch errors
            Logger.error(f"Failed to get CPU temp: {e}") # log the error
            return "N/A" # set to N/A so its not empty space

    @staticmethod
    def get_cpu_usage():
        """percentage of CPU utilization

        Returns:
            float: percentage
        """
        try:
            usage = psutil.cpu_percent(interval=0.5) # get the cpu percentage utilization
            Logger.info(f"CPU usage read successfully: {usage}%") # log that it was got
            return usage # return this number
        except Exception as e:
            Logger.error(f"Failed to get CPU usage: {e}") # log the error
            return 0.0 # set to 0

    @staticmethod
    def get_mem_usage():
        """gets the memory utilization

        Returns:
            String: total and used memory
        """
        try:
            mem = psutil.virtual_memory() # get the memory utilization 
            used = round(mem.used / (1024*1024)) # divide it over raspie ram and round it
            total = round(mem.total / (1024*1024)) # same with total memory
            Logger.info(f"Memory usage read successfully: used {used}MB, total {total}MB") # log this infomation
            return (used, total) # return these numbers
        except Exception as e:
            Logger.error(f"Failed to get memory usage: {e}") # log the error
            return (0, 0) # return 0s

    @staticmethod
    def get_disk_free():
        """gets the disk utilization

        Returns:
            String: storage space
        """
        try:
            disk = psutil.disk_usage('/') # get the disk utilization and space
            free_gb = round(disk.free / (1024*1024*1024), 2) # divide free space over the total space of the raspie
            Logger.info(f"Disk free space read successfully: {free_gb}GB") # log this information
            return free_gb # return the total free space
        except Exception as e:
            Logger.error(f"Failed to get disk free space: {e}") # log the error
            return 0.0 # return 0s

    @staticmethod
    def get_uptime():
        """gets the uptime of the Raspie

        Returns:
            String: uptime
        """
        try:
            boot_time = psutil.boot_time() # get the boot time
            now = datetime.datetime.now().timestamp() # get the date and time as of right now
            uptime_seconds = int(now - boot_time) # calculate uptime and cast to integer
            uptime_str = str(datetime.timedelta(seconds=uptime_seconds)) # set uptime to string
            Logger.info(f"System uptime calculated successfully: {uptime_str}") # log this info
            return uptime_str # return string value
        except Exception as e:
            Logger.error(f"Failed to get uptime: {e}") # log error
            return "N/A" # return N/A so its not blank

    @staticmethod
    def get_ip():
        """gets the ip of the raspie

        Returns:
            String: ip address
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # new socket to connect
        try:
            s.connect(('8.8.8.8', 80)) # connect to socket
            ip = s.getsockname()[0] # get the ip of the socket
            Logger.info(f"IP address detected successfully: {ip}") # log the ip
            return ip # return this ip
        except Exception as e:
            Logger.error(f"Failed to get IP address: {e}") # log the error
            return 'N/A' # set to N/A so its not empty
        finally:
            s.close() # close the connection

    def get_all_stats(self):
        """gets all of the other methods

        Returns:
            String: everything
        """
        try:
            stats = { # create a list  of these items that calls the methods 
                "cpu_temp": self.get_cpu_temp(),
                "cpu_usage": self.get_cpu_usage(),
                "mem_used": self.get_mem_usage()[0],
                "mem_total": self.get_mem_usage()[1],
                "disk_free": self.get_disk_free(),
                "uptime": self.get_uptime(),
                "ip_address": self.get_ip()
            }
            Logger.info("All system stats collected successfully") # log that they where all successful
            return stats # return this list
        except Exception as e:
            Logger.error(f"Failed to collect all system stats: {e}") # log the error
            return {
                "cpu_temp": "N/A",
                "cpu_usage": 0.0,
                "mem_used": 0,
                "mem_total": 0,
                "disk_free": 0.0,
                "uptime": "N/A",
                "ip_address": "N/A"
            } # return default values if cannot be gotten
