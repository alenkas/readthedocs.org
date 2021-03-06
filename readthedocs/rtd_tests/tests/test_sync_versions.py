import json

from django.test import TestCase

from builds.models import Version
from builds.constants import STABLE
from projects.models import Project


class TestSyncVersions(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        Version.objects.create(project=self.pip, identifier='origin/master',
                               verbose_name='master', active=True,
                               machine=True)
        Version.objects.create(project=self.pip, identifier='to_delete',
                               verbose_name='to_delete', active=False)

    def test_proper_url_no_slash(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ]}

        r = self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        json_data = json.loads(r.content)
        self.assertEqual(json_data['deleted_versions'], ['to_delete'])
        self.assertEqual(json_data['added_versions'], ['to_add'])

    def test_stable_versions(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8',
                    'verbose_name': '0.8',
                },

            ]
        }

        self.assertRaises(
            Version.DoesNotExist,
            Version.objects.get,
            slug=STABLE
        )
        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

    def test_update_stable_version(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8',
                    'verbose_name': '0.8',
                },
            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '0.9')

        version_post_data = {
            'tags': [
                {
                    'identifier': '1.0.0',
                    'verbose_name': '1.0.0',
                },
            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

        version_post_data = {
            'tags': [
                {
                    'identifier': '0.7',
                    'verbose_name': '0.7',
                },
            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertTrue(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

    def test_update_inactive_stable_version(self):
        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertEqual(version_stable.identifier, '0.9')
        version_stable.active = False
        version_stable.save()

        version_post_data['tags'].append({
            'identifier': '1.0.0',
            'verbose_name': '1.0.0',
        })

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )

        version_stable = Version.objects.get(slug=STABLE)
        self.assertFalse(version_stable.active)
        self.assertEqual(version_stable.identifier, '1.0.0')

    def test_new_tag_update_active(self):

        Version.objects.create(project=self.pip, identifier='0.8.3',
                               verbose_name='0.8.3', active=True)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },

            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_9 = Version.objects.get(slug='0.9')
        self.assertTrue(version_9.active)

    def test_new_tag_update_inactive(self):

        Version.objects.create(project=self.pip, identifier='0.8.3',
                               verbose_name='0.8.3', active=False)

        version_post_data = {
            'branches': [
                {
                    'identifier': 'origin/master',
                    'verbose_name': 'master',
                },
                {
                    'identifier': 'origin/to_add',
                    'verbose_name': 'to_add',
                },
            ],
            'tags': [
                {
                    'identifier': '0.9',
                    'verbose_name': '0.9',
                },
                {
                    'identifier': '0.8.3',
                    'verbose_name': '0.8.3',
                },

            ]
        }

        self.client.post(
            '/api/v2/project/%s/sync_versions/' % self.pip.pk,
            data=json.dumps(version_post_data),
            content_type='application/json',
        )
        version_9 = Version.objects.get(slug='0.9')
        self.assertTrue(version_9.active is False)
