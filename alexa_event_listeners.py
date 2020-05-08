import asyncio
from queue import Queue  # thread safe
from dynamic_crauler_api import DynamicAPI
from collections import defaultdict
import json


async def main():
    urls_queue = Queue()
    handlers_stat = {}

    top100_urls = []
    with open('../alexa_top100.txt') as f:
        for line in f:
            line = "https://" + line.strip() + '/'
            top100_urls.append(line)

    api = await (DynamicAPI().init())

    for u in top100_urls[:2]:
        urls_queue.put(u)

    while not urls_queue.empty():
        url = urls_queue.get()
        print(url)
        await api.add_url(url)
        results = await api.get_results()
    
        curr_handlers_stat = defaultdict(int)
        for result in results:
            ev_handlers = result["eventHandlers"]
            for lst in ev_handlers:
                for dct in lst:
                    curr_handlers_stat[dct['type']] += 1
        handlers_stat[url] = curr_handlers_stat

        with open('../top100_handlers.txt', 'w') as f:
            json.dump(handlers_stat, f)
    await api.destroy()


if __name__ == '__main__':
    asyncio.run(main())
