import asyncio
import bisect
import copy
import threading
from queue import Queue
from collections import defaultdict

import numpy as np
from sortedcontainers import SortedList, SortedSet, SortedKeyList
from sklearn.cluster import DBSCAN

import url_features


class UrlClusterizedQueue:
    def __init__(self):
        self._features_count_list = SortedList()  # list of pairs (feature_count, feature_name)
        self._features_count_dict = dict()

        self._clusterizer = DBSCAN(metric='jaccard')
        self._min_freq = 0.1
        self._max_freq = 0.9

        self._urls = dict()
        self._urls_keys = []
        self._index = -1
        self._min_urls_count = 50

        self._subqueue = Queue()
        self._subqueue_len = 4

        # constants
        self._i_is_used = 1
        self._i_features = 0

        self._i_list_for_unused = 0
        self._i_list_for_used = 1
        self._i_list_total = 2

    def _return_url(self, url):
        self._urls[url][1] = True
        return url

    def _next_queue_fallback(self):
        self._index += 1
        url = self._urls_keys[self._index]
        return self._return_url(url)

    def _run_clustering(self):
        print("try to use clustering")
        # here we need to run clustering
        # first of all we need to choose features
        max_feature_count = int(self._max_freq * len(self._urls))
        min_feature_count = int(self._min_freq * len(self._urls))
        start_index = bisect.bisect_left(self._features_count_list, (min_feature_count, ''))
        end_index = bisect.bisect_right(self._features_count_list, (max_feature_count, 'ZZZ'))
        if start_index >= end_index:
            print("not enough features")
            return self._next_queue_fallback()

        chosen_features = SortedSet()
        for i in range(start_index, end_index):
            chosen_features.add(self._features_count_list[i][1])

        # then we need to build features matrix
        X = np.empty((len(self._urls), len(chosen_features)))
        for i in range(len(self._urls)):
            features = self._urls[self._urls_keys[i]][self._i_features]
            for j, fname in enumerate(chosen_features):
                if fname in features:
                    X[i][j] = 1
                else:
                    X[i][j] = 0

        # now we can run clustering
        y = self._clusterizer.fit_predict(X)

        # and we need to create uniform distributed queue
        def get_list_of_2_sets():
            return [set(), set(), 0]  # 0 is for used urls, # 1 is for unused # 3 is for total count

        url_in_cluster = defaultdict(get_list_of_2_sets)
        for i in range(len(y)):
            url = self._urls_keys[i]
            if self._urls[url][self._i_is_used]:
                url_in_cluster[y[i]][self._i_list_for_used].add(url)
            else:
                url_in_cluster[y[i]][self._i_list_for_unused].add(url)
            url_in_cluster[y[i]][self._i_list_total] += 1

        limit = self._subqueue_len
        cluster_keys = SortedKeyList(url_in_cluster.keys(), key=lambda x: -len(url_in_cluster[x][self._i_list_for_used]))
        while limit > 0:  # Todo: optimize
            if len(cluster_keys) > 0:
                less_index = cluster_keys.pop()
                unused_urls = url_in_cluster[less_index][self._i_list_for_unused]
                if len(unused_urls) > 0:
                    url = unused_urls.pop()
                    self._subqueue.put(url)
                    limit -= 1

                    if len(unused_urls) > 0:
                        url_in_cluster[less_index][self._i_list_for_used].add(url)
                        cluster_keys.add(less_index)
            else:
                break

    async def _run_and_wait_clustering(self):
        t = threading.Thread(target=UrlClusterizedQueue._run_clustering, args=(self,))
        t.run()
        while t.is_alive():
            await asyncio.sleep(0.3)

    async def get(self):
        if len(self._urls) < self._min_urls_count:
            return self._next_queue_fallback()
        else:
            if self._subqueue.empty():
                await self._run_and_wait_clustering()
            # if self._subqueue.qsize() == 1:
            #     asyncio.create_task(self._run_and_wait_clustering())
            return self._return_url(self._subqueue.get())

    async def empty(self):
        if self._index + 1 >= len(self._urls):
            return True
        else:
            return False

    async def put(self, url):
        if url in self._urls:
            return

        features = url_features.extract(url)
        for fname in features:
            if fname in self._features_count_dict:
                fcount = self._features_count_dict[fname]
                del self._features_count_list[self._features_count_list.index((fcount, fname))]
            else:
                fcount = 0
            fcount += 1
            self._features_count_dict[fname] = fcount
            self._features_count_list.add((fcount, fname))

        self._urls[url] = [features, False]  # False is for used
        self._urls_keys.append(url)
