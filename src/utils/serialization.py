from pydantic import BaseModel


class SerializableModel(BaseModel):

    def to_dict(self):
        """Convert model to JSON-safe dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data):
        """Rebuild model from serialized dictionary."""
        return cls.model_validate(data)