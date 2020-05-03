import asyncio
import copy
from xml.dom import minidom
from os import listdir
from os.path import isfile, join
from url import Url


class Sitemap:
    def __init__(self):
        self.urls = None
        self.host_filter = None
        self.checked_in = set()
        self.start_url = None

    async def read_sitemap(self, file_path):
        xml_map = minidom.parse(file_path)
        requests = xml_map.getElementsByTagName('request')
        urls = set()
        host_filter = set()
        for req in requests:
            host = req.attributes['host'].value
            scheme = req.attributes['scheme'].value
            path = req.attributes['path'].value
            port = req.attributes['port'].value
            url = await Url().from_options(host, scheme, port, path)
            if not self.start_url:
                self.start_url = url
            urls.add(url)
            host_filter.add(host)

        self.urls = urls
        self.host_filter = host_filter
        return self

    async def checkin(self, url):
        if url in self.urls:
            self.checked_in.add(url)

    async def checkin_structured(self, url):
        path_split = list(filter(bool, url.path.split('/')))
        if len(path_split) > 0:
            tmp_url = copy.deepcopy(url)

            for i in range(len(path_split) + 1):
                tmp_url.path = '/{}'.format('/'.join(path_split[:i]))
                await self.checkin(await Url().from_named_tuple(tmp_url))
        else:
            await self.checkin(url)

    def calc_score(self):
        return float(len(self.urls - self.checked_in)) / len(self.urls)


async def generate_test_sitemaps(sitemaps_folder='sitemaps'):
    sitemaps_files = [join(sitemaps_folder, f) for f in listdir(sitemaps_folder) if isfile(join(sitemaps_folder, f))]
    result_sitemaps = []
    for sitemap_file in sitemaps_files:
        result_sitemaps.append(await Sitemap().read_sitemap(sitemap_file))

    return result_sitemaps
