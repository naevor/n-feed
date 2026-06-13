import os
from unittest.mock import patch

from django.test import SimpleTestCase

from twitmain.settings import base


class StorageSettingsTests(SimpleTestCase):
    def test_default_storage_uses_filesystem_when_s3_disabled(self):
        with patch.dict(os.environ, {"USE_S3_STORAGE": "False"}, clear=False):
            config = base.build_default_storage_config()

        self.assertEqual(config["BACKEND"], "django.core.files.storage.FileSystemStorage")

    def test_default_storage_can_use_s3_backend(self):
        env = {
            "USE_S3_STORAGE": "True",
            "AWS_ACCESS_KEY_ID": "access",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "AWS_STORAGE_BUCKET_NAME": "n-feed-media",
            "AWS_S3_ENDPOINT_URL": "http://localhost:9000",
        }
        with patch.dict(os.environ, env, clear=False):
            config = base.build_default_storage_config()

        self.assertEqual(config["BACKEND"], "storages.backends.s3.S3Storage")
        self.assertEqual(config["OPTIONS"]["bucket_name"], "n-feed-media")
        self.assertEqual(config["OPTIONS"]["endpoint_url"], "http://localhost:9000")
