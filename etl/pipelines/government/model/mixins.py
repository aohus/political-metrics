import random
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any


class model_meta(type):
    _id_counter = 1

    def __call__(cls, *args, **kwargs):
        # Create the instance
        instance = super().__call__(*args, **kwargs)
        # Auto-generate id if not provided
        if not hasattr(instance, 'id') or getattr(instance, 'id', None) is None:
            instance.id = cls._id_counter
            cls._id_counter += 1
        return instance

    @property
    def header(cls):
        if hasattr(cls, '__dataclass_fields__'):
            keys = [field.name for field in fields(cls)]
        else:
            keys = list(cls.__dict__.keys())
        return ", ".join(keys)

    # @property
    # def to_csv_row(self):
    #     if hasattr(self, '__dataclass_fields__'):
    #         values = [str(getattr(self, field.name)) for field in fields(self)]
    #     else:
    #         values = [str(v) for v in self.__dict__.values()]
    #     return ", ".join(values)


