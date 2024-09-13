import serial

ser = serial.Serial('/dev/rfcomm2', 115200, timeout=1)
ser.write(b'ATZ\r')  # リセットコマンド
response = ser.read(100)  # レスポンスを読み取る
print(response)

ser.write(b'0100\r')  # OBD-IIのモード1、PID 00（サポートされているPIDのリスト）を要求
response = ser.read(100)
print(response)

ser.close()