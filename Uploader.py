import datetime
import os
import logging
import traceback

from bilibiliuploader.bilibiliuploader import BilibiliUploader
from bilibiliuploader.core import VideoPart

from BiliLive import BiliLive
import utils


def upload(uploader: BilibiliUploader, parts: list, cr: int, title: str, tid: int, tags: list, desc: str, source: str, thread_pool_workers: int = 1, max_retry: int = 3, upload_by_edit: bool = False) -> tuple:
    bvid = None
    if upload_by_edit:
        while bvid is None:
            avid, bvid = uploader.upload(
                parts=[parts[0]],
                copyright=cr,
                title=title,
                tid=tid,
                tag=",".join(tags),
                desc=desc,
                source=source,
                thread_pool_workers=thread_pool_workers,
                max_retry=max_retry,
            )
            os.remove(parts[0].path)
        for i in range(1, len(parts)):
            uploader.edit(
                bvid=bvid,
                parts=[parts[i]],
                max_retry=max_retry,
                thread_pool_workers=thread_pool_workers
            )
            os.remove(parts[i].path)
    else:
        while bvid is None:
            avid, bvid = uploader.upload(
                parts=parts,
                copyright=cr,
                title=title,
                tid=tid,
                tag=",".join(tags),
                desc=desc,
                source=source,
                thread_pool_workers=thread_pool_workers,
                max_retry=max_retry,
            )
            print(avid, bvid)
            for i in range(len(parts)):
                os.remove(parts[i].path)
    return avid, bvid


class Uploader(BiliLive):
    def __init__(self, output_dir: str, splits_dir: str, config: dict):
        super().__init__(config)
        self.output_dir = output_dir
        self.splits_dir = splits_dir
        self.uploader = BilibiliUploader()
        self.uploader.login(config.get('spec', {}).get('uploader', {}).get('account', {}).get('username', ""),
                            config.get('spec', {}).get('uploader', {}).get('account', {}).get('password', ""))

    def upload(self, global_start: datetime.datetime) -> dict:
        logging.basicConfig(level=utils.get_log_level(self.config),
                            format='%(asctime)s %(thread)d %(threadName)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(self.config.get('root', {}).get('logger', {}).get('log_path', "./log"), "Uploader_"+datetime.datetime.now(
                            ).strftime('%Y-%m-%d_%H-%M-%S')+'.log'),
                            filemode='a')
        return_dict = {}
        try:
            if self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('upload_clips', False):
                output_parts = []
                datestr = global_start.strftime(
                    '%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
                filelists = sorted(os.listdir(self.output_dir), key=utils.get_split_index)
                for filename in filelists:
                    if os.path.getsize(os.path.join(self.output_dir, filename)) < 1024*1024:
                        continue
                    title = os.path.splitext(filename)[0].split("_")[-1]
                    output_parts.append(VideoPart(
                        path=os.path.join(self.output_dir, filename),
                        title=title,
                        desc=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('desc', "").format(
                            date=datestr),
                    ))

                avid, bvid = upload(self.uploader, output_parts,
                                    cr=self.config.get('spec', {}).get(
                                        'uploader', {}).get('copyright', 2),
                                    title=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('title', "").format(
                                        date=datestr),
                                    tid=self.config.get('spec', {}).get(
                                        'uploader', {}).get('clips', {}).get('tid', 27),
                                    tags=self.config.get('spec', {}).get(
                                        'uploader', {}).get('clips', {}).get('tags', []),
                                    desc=self.config.get('spec', {}).get('uploader', {}).get('clips', {}).get('desc', "").format(
                                        date=datestr),
                                    source="https://live.bilibili.com/"+self.room_id,
                                    thread_pool_workers=self.config.get('root', {}).get(
                                        'uploader', {}).get('thread_pool_workers', 1),
                                    max_retry=self.config.get('root', {}).get(
                                        'uploader', {}).get('max_retry', 10),
                                    upload_by_edit=self.config.get('root', {}).get('uploader', {}).get('upload_by_edit', False))
                return_dict["clips"] = {
                    "avid": avid,
                    "bvid": bvid
                }
            if self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('upload_record', False):
                splits_parts = []
                datestr = global_start.strftime(
                    '%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
                filelists = sorted(os.listdir(self.splits_dir), key=utils.get_split_index)
                for idx, filename in enumerate(filelists):
                    if os.path.getsize(os.path.join(self.splits_dir, filename)) < 1024*1024:
                        continue
                    split_interval = int(self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('split_interval', 3600))
                    start_time = global_start + datetime.timedelta(seconds= idx * split_interval)
                    title = start_time.strftime('%Y-%m-%d_%H:%M:%S')
                    splits_parts.append(VideoPart(
                        path=os.path.join(self.splits_dir, filename),
                        title=title,
                        desc=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('desc', "").format(
                            date=datestr),
                    ))

                avid, bvid = upload(self.uploader, splits_parts,
                                    cr=self.config.get('spec', {}).get(
                                        'uploader', {}).get('copyright', 2),
                                    title=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('title', "").format(
                                        date=datestr),
                                    tid=self.config.get('spec', {}).get(
                                        'uploader', {}).get('record', {}).get('tid', 27),
                                    tags=self.config.get('spec', {}).get(
                                        'uploader', {}).get('record', {}).get('tags', []),
                                    desc=self.config.get('spec', {}).get('uploader', {}).get('record', {}).get('desc', "").format(
                                        date=datestr),
                                    source="https://live.bilibili.com/"+self.room_id,
                                    thread_pool_workers=self.config.get('root', {}).get(
                                        'uploader', {}).get('thread_pool_workers', 1),
                                    max_retry=self.config.get('root', {}).get(
                                        'uploader', {}).get('max_retry', 10),
                                    upload_by_edit=self.config.get('root', {}).get('uploader', {}).get('upload_by_edit', False))
                return_dict["record"] = {
                    "avid": avid,
                    "bvid": bvid
                }
        except Exception as e:
            logging.error(self.generate_log(
                'Error while uploading:' + str(e)+traceback.format_exc()))
        return return_dict
