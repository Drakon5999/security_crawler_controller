import asyncio
from queue import Queue  # thread safe
from dynamic_crauler_api import DynamicAPI
from url import Url
from url_clusterized_queue import UrlClusterizedQueue

from tests.sitemap import generate_test_sitemaps


async def main():
    sitemaps = await generate_test_sitemaps()
    for sitemap in sitemaps:
        if not sitemap.start_url:
            continue

        api = await (DynamicAPI().init())
        urls_queue = UrlClusterizedQueue()

        query_limit = 50

        found_endpoints = set()
        found_urls = set()
        start_url = sitemap.start_url
        await sitemap.checkin(sitemap.start_url)
        await urls_queue.put(start_url)
        while not await urls_queue.empty() and query_limit > 0:
            url = str(await urls_queue.get())
            print(url)
            await api.add_url(url)
            results = await api.get_results()

            for result in results:
                # print(result)
                for link in result['links']:
                    if not link:
                        continue
                    url_res = await Url().from_string(link)
                    if url_res.host in sitemap.host_filter:
                        await urls_queue.put(url_res)
                        await sitemap.checkin_structured(url_res)
                for url in result['requestedUrls']:
                    if not url:
                        continue
                    found_endpoints.add(url)
                    url_res = await Url().from_string(url)
                    await sitemap.checkin_structured(url_res)

                for url in result['urlChanges']:
                    if not url:
                        continue
                    found_urls.add(url)
                    url_res = await Url().from_string(url)
                    await sitemap.checkin_structured(url_res)
            print("Found endpoints: {}".format(len(found_endpoints)))
            query_limit -= 1
            print("Query limit: {}".format(query_limit))

        with open("{}.txt".format(sitemap.start_url.host), "w") as f:
            f.write(str(found_endpoints))
            f.write(str(found_urls))
            f.write(str(sitemap.calc_score()))
        print("Sitemap score: {}".format(sitemap.calc_score()))
        await api.destroy()


if __name__ == '__main__':
    asyncio.run(main())
