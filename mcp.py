from machine import I2C

# Ce fichier contient une classe prenant en charge la communication I2C avec le module MCP9600
# Pour le détail des registres, et les diverses information concernant le module, je recommande la consultation du datasheet : https://ww1.microchip.com/downloads/en/DeviceDoc/MCP960X-L0X-RL0X-Data-Sheet-20005426F.pdf

class mcp9600:
    def __init__(self, port: int = 0):
        self.i2c = I2C(0, freq=50000) # On initialise le module I2C, en utilisant le port I2C 0 (SCL à la pine 7, et SDA à la pine 6)

        # On teste si le module est bien connecté en écrivant le registre servant à paramétrer le type de thermocouple utilisé, ainsi que le coefficient de filtrage.
        try:
            self.i2c.writeto_mem(0x66, 0x05, b'\x20')

        # Si le test est négatif, on crée une erreur qui sera affichée dans la console.
        except:
            raise OSError("Device not found")
    
    # Lecture de la température de jonction chaude (registre 0x00)
    def get_hot(self):
        return mcp9600.convert(self.i2c.readfrom_mem(0x66, 0x00, 2))
    
    # Lecture de la température de jonction froide (registre 0x02)
    def get_cold(self):
        return mcp9600.convert(self.i2c.readfrom_mem(0x66, 0x02, 2))
    
    # Lecture de la différence de température entre jonction froide et jonction chaude (0x01)
    def get_diff(self):
        return mcp9600.convert(self.i2c.readfrom_mem(0x66, 0x01, 2))

    # Fonction réalisant la conversion de température, de l'écriture en octet vers celle en écriture "commune"
    @staticmethod
    def convert(buf: bytes):
        buf_ar = list(buf)
        upper, lower = buf_ar[0], buf_ar[1]

        if upper > 8:
            return (upper * 16 + lower / 16) - 4096
        else:
            return (upper * 16 + lower /16)


# Code de test
if __name__ == "__main__":
    mcp = mcp9600()

    print(mcp.get_hot(), mcp.get_cold(), mcp.get_diff())