# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    merge_dicts,
    try_get,
)


class KanalDIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://(?:www\.)?kanald\.com\.tr/
                    (?:
                        (?:[a-zA-Z0-9-]+)/
                        (?:
                            (?:[0-9]+)-bolum|
                            (?:[0-9]+)-bolum-izle|
                            bolumler|
                            bolum
                        )|
                        embed
                    )/
                    (?P<id>[a-zA-Z0-9-]+)
                '''

    _TESTS = [{
        'url': 'https://www.kanald.com.tr/kuzeyguney/1-bolum/10115',
        'md5': '8a32b6e894d45d618360b8b01173de9a',
        'info_dict': {
            'id': '10115',
            'title': '1.Bölüm',
            'description': 'md5:64edbdd153b7eefdf92c31bf5a6e5c1b',
            'upload_date': '20110907',
            'timestamp': 1315426815,
            'ext': 'm3u8',
        }
    }, {
        'url': 'https://www.kanald.com.tr/embed/5465f0d2cf45af1064b73077',
        'only_matching': True
    }, {
        'url': 'https://www.kanald.com.tr/kuzeyguney/79-bolum-izle/19270',
        'only_matching': True
    }, {
        'url': 'https://www.kanald.com.tr/sevdanin-bahcesi/bolumler/sevdanin-bahcesi-2-bolum',
        'only_matching': True
    }, {
        'url': 'https://www.kanald.com.tr/yarim-elma/bolum/yarim-elma-36-bolum',
        'only_matching': True
    }, {
        'url': 'https://www.kanald.com.tr/ask-ve-gunah/bolumler/ask-ve-gunah-120-bolum-final',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        info = {
            'id': video_id,
        }

        search_json_ld = self._search_regex(
            r'(?is)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?:\s+)?(?P<json_ld>{[^<]+VideoObject[^<]+})(?:\s+)?</script>', webpage, 'JSON-LD', group='json_ld')

        # https://stackoverflow.com/questions/22394235/invalid-control-character-with-python-json-loads
        try:
            json_ld = json.loads(search_json_ld, strict=False)
        except ValueError as ve:
            raise ExtractorError('%s: Failed to parse JSON ' % video_id, cause=ve)

        if not re.match(r'dogannet\.tv', json_ld['contentUrl']):
            json_ld.update({
                'contentUrl': 'https://soledge13.dogannet.tv/%s' % json_ld['contentUrl']
            })

        ld_info = self._json_ld(json_ld, video_id)

        return merge_dicts(ld_info, info)


class KanalDSeriesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kanald\.com\.tr/(?P<id>[a-zA-Z0-9-]+)/(?:bolum|bolumler)'

    _TESTS = [{
        'url': 'https://www.kanald.com.tr/kuzeyguney/bolum',
        'info_dict': {
            'id': 'kuzeyguney'
        },
        'playlist_mincount': 80
    }, {
        'url': 'https://www.kanald.com.tr/iki-yalanci/bolumler',
        'only_matching': True
    }]

    def extract_episodes(self, url, playlist_id):
        page = 1
        has_more = True

        while has_more:
            webpage = self._download_webpage(
                url, playlist_id, 'Downloading page %s' % page, query={
                    'page': page,
                })

            episode_urls = re.findall(r'<a class=(["\'])title\1 href=\1/(?P<url>' + re.escape(playlist_id) + r'[a-zA-Z0-9-/]+)\1[^>]*>', webpage)

            if len(episode_urls) is 0:
                has_more = False
                continue

            for episode_url in episode_urls:
                episode_url = try_get(episode_url, lambda x: x[1])
                if not episode_url:
                    continue
                yield self.url_result(
                    'https://www.kanald.com.tr/%s' % episode_url,
                    ie=KanalDIE.ie_key())

            page += 1

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        return self.playlist_result(self.extract_episodes(url, playlist_id), playlist_id)
