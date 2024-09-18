import can
import os
import threading
import subprocess

def initialize_BLE(device_mac):
    """
    Initialize Bluetooth Low Energy (BLE) for OBDLink MX+ connection.
    """
    def run_command(command):
        result = os.system(command)
        if result != 0:
            print(f"Command failed: {command}")
        return result
    
    def is_device_paired(mac_address):
        try:
            result = subprocess.check_output(['bluetoothctl', 'paired-devices'])
            return mac_address in result.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error checking paired devices: {e}")
            return False
    
    # Check if device is paired
    if not is_device_paired(device_mac):
        print(f"Device {device_mac} is not paired.")
        return False
    
    # Assuming device is paired, attempt to bind and listen
    if run_command(f'sudo rfcomm bind 0 {device_mac}') != 0:
        return False
    if run_command('sudo rfcomm listen 0 1 &') != 0:
        return False
    
    return True

def receive_obd_response(bus, timeout=10.0):
    """
    Receive an OBD-II response message from CAN bus.
    """
    try:
        print("Waiting for response...")
        response_msg = bus.recv(timeout)
        if response_msg:
            print(f"Received message: {response_msg}")
            return response_msg
        else:
            print("No response received within the timeout.")
            return None
    except can.CanError as e:
        print(f"Error receiving message: {e}")
        return None

def send_obd_request(bus, arbitration_id, data):
    """
    Send an OBD-II request message over CAN bus.
    """
    try:
        # Create CAN message
        request_msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False
        )
        bus.send(request_msg)
        print(f"Request message sent: {request_msg}")
    except can.CanError as e:
        print(f"Failed to send message: {e}")


def decode_obd_response(response_msg):
    """
    Decode the OBD-II response message.
    """
    if response_msg:
        print(f"Received message: {response_msg}")
        # Print the actual arbitration ID and data
        print(f"Arbitration ID: {response_msg.arbitration_id:#04x}")
        print(f"Data: {response_msg.data}")
        
        # Check for the correct response ID
        if response_msg.arbitration_id == 0x7E8:  # Adjust based on actual response ID
            data = response_msg.data
            if len(data) >= 4:
                # Data parsing example (e.g., vehicle speed)
                speed = data[3]  # 4th byte is the speed data (assuming standard PID)
                print(f"Vehicle Speed: {speed} km/h")
            else:
                print("Data length is insufficient.")
        else:
            print("Unexpected message ID.")
    else:
        print("No response received.")


def main():
    print("Main program is started")
    device_mac = "8A:2A:D4:FF:38:F3" # 00:04:3E:84:7D:4C OBDLink
    
    bus = None
    
    try:
        if not initialize_BLE(device_mac):
            print("Failed to initialize BLE.")
            return
        
        # Connect to CAN Bus using serial interface
        bus = can.interface.Bus(bustype='serial', channel='/dev/rfcomm0', bitrate=500000)
        
        # Send Engine RPM Speed(PID 0x0C) Request
        send_obd_request(bus, arbitration_id=0x7DF, data=[0x02, 0x01, 0x0C])
        response_msg = receive_obd_response(bus)
        decode_obd_response(response_msg)
        
        # Send custom PID 2147 (0x0867) request
        send_obd_request(bus, arbitration_id=0x7DF, data=[0x04, 0x01, 0x08, 0x67])
        response_msg = receive_obd_response(bus)
        decode_obd_response(response_msg)

    except Exception as e:
        print("----------Exception!----------")
        print(e)

    finally:
        if bus:
            bus.shutdown()  # Ensure that the bus is properly shut down
        print("Program finished.")
        os.system('sudo rfcomm release 0')        

if __name__ == '__main__':
    main()
