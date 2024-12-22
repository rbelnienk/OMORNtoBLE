import asyncio
from bleak import BleakScanner, BleakClient
from asyncio import TimeoutError
#from garmin import sendGarmin
# Gerätename des Blutdruckmessgeräts
DEVICE_NAME = "BLESmart_00000287F348F8657214"

# UUID der Blood Pressure Measurement Characteristic
BLOOD_PRESSURE_CHAR_UUID = "00002a35-0000-1000-8000-00805f9b34fb"

# Callback-Funktion für Benachrichtigungen
def notification_handler(sender: int, data: bytearray):
    """
    Callback für Benachrichtigungen vom Blutdruckgerät.
    """
    try:
        # Gegebenes Bytearray
        byte_array = bytearray(data)

        # Umwandlung der Bytes in Dezimalwerte
        decimal_values = [byte for byte in byte_array]

        # Ausgabe der Dezimalwerte
        print("Dezimalwerte:", decimal_values)

        # Systole und Diastole aus den Bytes extrahieren
        systole = int.from_bytes(data[1:3], "little")  # Byte 2-3
        diastole = int.from_bytes(data[3:5], "little")  # Byte 4-5
        pulse = int.from_bytes(data[14:15], "little")  # Byte 6-7
        #sendGarmin(systole, diastole, pulse)
        print(f"Systole: {systole} mmHg, Diastole: {diastole} mmHg, Puls: {pulse} bpm")

    except Exception as e:
        print(f"Fehler beim Verarbeiten der Daten: {e}")


async def scan_and_connect():
    while True:
        print("Scanning nach BLE-Geräten...")

        # Scanne nach Geräten
        devices = await BleakScanner.discover()
        target_device = None
        for device in devices:
            if device.name == DEVICE_NAME:
                target_device = device
                print(f"Gefunden: {device.name} - {device.address}")
                break

        if not target_device:
            print(f"Gerät mit Namen '{DEVICE_NAME}' nicht gefunden. Versuche es später erneut...")
            await asyncio.sleep(5)  # Warten, bevor erneut nach Geräten gesucht wird
            continue  # Zurück zum Beginn der Schleife

        # Versuche, eine Verbindung zum Gerät herzustellen
        try:
            async with BleakClient(target_device.address) as client:
                print("Verbunden:", client.is_connected)

                # Prüfen, ob die Characteristic verfügbar ist
                blood_pressure_char = None
                for service in client.services:
                    for char in service.characteristics:
                        if char.uuid == BLOOD_PRESSURE_CHAR_UUID:
                            blood_pressure_char = char
                            break
                    if blood_pressure_char:
                        break

                if not blood_pressure_char:
                    print(f"Characteristic {BLOOD_PRESSURE_CHAR_UUID} nicht gefunden.")
                    continue  # Wenn keine passende Characteristic gefunden, dann erneut scannen

                # Notifications aktivieren
                print(f"Benachrichtigungen aktivieren für Characteristic {BLOOD_PRESSURE_CHAR_UUID}...")
                await client.start_notify(blood_pressure_char.uuid, notification_handler)

                print("Warte auf Daten...")

                try:
                    # Schleife für regelmäßige Pings, um die Verbindung aufrechtzuerhalten
                    while True:
                        if not client.is_connected:
                            print("Verbindung unterbrochen. Versuche erneut zu verbinden...")
                            break  # Verbindung wurde unterbrochen, gehe zurück und suche wieder nach Geräten
                        await asyncio.sleep(1)  # 1 Sekunde warten pro Iteration
                finally:
                    # Benachrichtigungen stoppen
                    await client.stop_notify(blood_pressure_char.uuid)
                    print("Benachrichtigungen gestoppt.")

        except TimeoutError:
            print("Verbindung zum Gerät konnte nicht innerhalb des Zeitlimits hergestellt werden. Versuche es erneut...")
            continue  # Im Falle eines Timeouts direkt einen neuen Verbindungsversuch starten
        except Exception as e:
            print(f"Fehler bei der Verbindung oder beim Empfang von Benachrichtigungen: {e}")
            continue  # Fehlerbehandlung und Rückkehr zum Start der Schleife


# Asynchrones Skript ausführen
asyncio.run(scan_and_connect())
