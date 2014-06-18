
class Fahrenheit(object):
    
    def convert_from(self, temperature):
        return (temperature - 32.0) / 1.8

    def convert_to(self, temperature):
        return (temperature * 1.8) + 32.0


class Kelvin(object):

    def convert_from(self, temperature):
        return temperature - 273.15

    def convert_to(self, temperature):
        return temperature + 273.15
