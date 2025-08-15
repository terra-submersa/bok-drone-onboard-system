from serial import Serial

from bok_drone_onboard_system.survey.emlid_reader import read_from_emlid, find_emlid_device

if __name__ == "__main__":
    # Find the EMLID device
    emlid_device = find_emlid_device()
    
    if emlid_device:
        print(f"EMLID device found at: {emlid_device}")
        try:
            ser = Serial(emlid_device, 115200, timeout=1)
            read_from_emlid(ser, lambda x: print(x))
        except Exception as e:
            print(f"Error connecting to EMLID device: {e}")
    else:
        print("No EMLID device found. Please check the connection.")
