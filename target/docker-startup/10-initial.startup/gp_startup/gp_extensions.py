"""
This module contains attributes and metaclasses.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

# ---------------------------------------------------------------------------------------------------------------------

class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

