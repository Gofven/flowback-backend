from django.db import models
from flowback.common.models import BaseModel
from flowback.user.models import User


# Create your models here.
class FileCollection(BaseModel):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


class FileSegment(BaseModel):
    def __init__(self, directory="", include_timestamp=True, *args, **kwargs):
        self.directory = directory
        self.include_timestamp = include_timestamp

        super(FileSegment, self).__init__(*args, **kwargs)

    def upload_directory(self):
        if self.directory != "" and not self.directory.endswith("/"):
            self.directory += "/"

        if self.include_timestamp:
            self.directory += "%Y/%m/%d/"

    collection = models.ForeignKey(FileCollection, on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_directory)
