# written by Arno Bakker, Yuan Yuan
# Modified by Raul Jimenez to integrate KTH DHT
# see LICENSE.txt for license information

import sys
from threading import currentThread
from Tribler.Core.CacheDB.CacheDBHandler import TorrentDBHandler
from Tribler.Core.CacheDB.sqlitecachedb import forceDBThread

DEBUG = False


class mainlineDHTChecker:
    __single = None

    def __init__(self):

        if DEBUG:
            print('mainlineDHTChecker: initialization', file=sys.stderr)
        if mainlineDHTChecker.__single:
            raise RuntimeError("mainlineDHTChecker is Singleton")
        mainlineDHTChecker.__single = self

        self.dht = None
        self.torrent_db = TorrentDBHandler.getInstance()

    def getInstance(*args, **kw):
        if mainlineDHTChecker.__single is None:
            mainlineDHTChecker(*args, **kw)
        return mainlineDHTChecker.__single
    getInstance = staticmethod(getInstance)

    def register(self, dht):
        self.dht = dht

    def lookup(self, infohash):
        if DEBUG:
            print("mainlineDHTChecker: Lookup", repr(infohash), file=sys.stderr)

        try:
            from Tribler.Core.Libtorrent.LibtorrentMgr import LibtorrentMgr
            LibtorrentMgr.getInstance().get_peers(infohash, self.got_peers_callback)
        except:
            print("mainlineDHTChecker: No lookup, libtorrent not loaded", file=sys.stderr)

    def got_peers_callback(self, infohash, peers, node=None):
        if DEBUG:
            if peers:
                print("mainlineDHTChecker: Got", len(peers), "peers for torrent", repr(infohash), currentThread().getName(), file=sys.stderr)
            else:
                print("mainlineDHTChecker: Got no peers for torrent", repr(infohash), currentThread().getName(), file=sys.stderr)

        if peers:
            # Arno, 2010-02-19: this can be called frequently with the new DHT,
            # so first check before doing commit.
            @forceDBThread
            def do_db():
                torrent = self.torrent_db.getTorrent(infohash)  # ,keys=('torrent_id','status_id') don't work, st*pid code
                if torrent['status'] != "good":
                    status = "good"
                    kw = {'status': status}
                    self.torrent_db.updateTorrent(infohash, **kw)
            do_db()
