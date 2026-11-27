import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class RustFSAdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = yaml.safe_load((ROOT / "lazycat-action.yml").read_text())
        cls.manifest = yaml.safe_load((ROOT / "lzc-manifest.yml").read_text())
        cls.package = yaml.safe_load((ROOT / "package.yml").read_text())

    def test_package_identity_and_online_baseline(self):
        self.assertEqual(self.package["package"], "white.lazycat.app.rustfs")
        self.assertRegex(self.package["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(self.package["homepage"], "https://rustfs.com")

    def test_source_selects_stable_unprefixed_semver_tags(self):
        source = self.action["source"]
        self.assertEqual(source["url"], "https://github.com/rustfs/rustfs.git")
        self.assertEqual(source["select"]["strategy"], "semver-tag")
        regex = source["select"]["tag_regex"]
        self.assertIsNotNone(re.fullmatch(regex, "1.0.7"))
        self.assertIsNone(re.fullmatch(regex, "1.0.7-rc.1"))
        self.assertIsNone(re.fullmatch(regex, "v1.0.7"))

    def test_console_and_s3_routes_keep_legacy_contract(self):
        application = self.manifest["application"]
        self.assertEqual(application["subdomain"], "rustfs")
        self.assertEqual(application["routes"], ["/=http://rustfs.white.lazycat.app.rustfs.lzcapp:9001"])
        self.assertEqual(application["public_path"], ["/api/public"])
        ingress = application["ingress"]
        self.assertEqual(ingress, [{"protocol": "tcp", "port": 9000, "service": "rustfs"}])

    def test_persistent_mounts_and_runtime_configuration(self):
        service = self.manifest["services"]["rustfs"]
        self.assertEqual(service["binds"], [
            "/lzcapp/var/data:/data",
            "/lzcapp/var/config:/config/rustfs",
        ])
        self.assertEqual(service["environment"]["RUSTFS_VOLUMES"], "/data")
        self.assertEqual(service["environment"]["RUSTFS_ADDRESS"], "0.0.0.0:9000")
        self.assertEqual(service["environment"]["RUSTFS_CONSOLE_ADDRESS"], "0.0.0.0:9001")
        self.assertEqual(service["environment"]["RUSTFS_ROOT_USER"], "rustfsadmin")
        self.assertEqual(service["environment"]["RUSTFS_ROOT_PASSWORD"], "rustfsadmin")
        self.assertEqual(service["user"], "10001:10001")

    def test_image_is_upstream_and_delivery_is_lazycat(self):
        image = self.action["images"][0]
        self.assertEqual(image["source"], "docker.io/rustfs/rustfs:{source_version}")
        self.assertEqual(image["delivery"]["mode"], "lazycat")
        self.assertTrue(self.manifest["services"]["rustfs"]["image"].startswith("registry.lazycat.cloud/"))


if __name__ == "__main__":
    unittest.main()
