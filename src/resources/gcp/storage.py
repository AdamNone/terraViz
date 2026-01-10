from ..base import ResourceHandler
from diagrams.gcp.storage import Storage

class StorageBucketHandler(ResourceHandler):
    @property
    def diagram_class(self):
        return Storage

    def get_label(self):
        name = self.name
        location = self._get_val("location", "")
        uniform_access = self._get_val("uniform_bucket_level_access", None)
        
        label = f"{name}"
        if location:
            label += f"\nLocation: {location}"
        if uniform_access is True:
            label += "\nUniform Access: Enabled"
            
        return label