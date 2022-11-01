from urllib import response
from dotenv import load_dotenv

import shotstack_sdk as shotstack
import os

from pexelsapi.pexels                import Pexels
from shotstack_sdk.model.image_asset import ImageAsset
from shotstack_sdk.api               import edit_api
from shotstack_sdk.model.clip        import Clip
from shotstack_sdk.model.track       import Track
from shotstack_sdk.model.timeline    import Timeline
from shotstack_sdk.model.output      import Output
from shotstack_sdk.model.edit        import Edit
from shotstack_sdk.model.title_asset import TitleAsset
from shotstack_sdk.model.video_asset import VideoAsset
from shotstack_sdk.model.soundtrack  import Soundtrack
from shotstack_sdk.model.transition  import Transition
from shotstack_sdk.model.html_asset  import HtmlAsset

from extract_keywords_for_each_sentence import our_keyword_extractor
load_dotenv()

shotstack_url           = os.getenv("SHOTSTACK_HOST")
shotstack_api_key       = os.getenv("SHOTSTACK_API_KEY")
shotstack_assets_url    = os.getenv("SHOTSTACK_ASSETS_URL")
pexels_api_key          = os.getenv("PEXELS_API_KEY")

api                     = Pexels(pexels_api_key)

configuration = shotstack.Configuration(host = shotstack_url)
configuration.api_key['DeveloperKey'] = shotstack_api_key

def pexel_searcher():
    para='there is a decline in bitcoin price nowadays. This is due to ongoing war between russia and ukraine. The market is also taking a toll. The dollar is facing inflation. Alleluia praise the Lord.'
    # para = "They decided to settle the argument with a race. They agreed on a route and started off the race. The rabbit shot ahead and ran briskly for some time. Then seeing that he was far ahead of the tortoise, he thought he'd sit under a tree for some time and relax before continuing the race. He sat under the tree and soon fell asleep."
    # para = "The last goal doesn’t matter. The last victory, already forgotten. Yesterday is gone. Lost, in the record books. But today is up for grabs. Unpredictable. Unwritten. Undecided. “Now” is ours. Do something and be remembered. Or do nothing and be forgotten. No one owns today. Take it"
    print(para)
    keyphrase,sentences = our_keyword_extractor(para=para)
    pexels_api_key          = os.getenv("PEXELS_API_KEY")
    api                     = Pexels(pexels_api_key)
    pexel_videos = []

    for sentence_index, keyword in enumerate(keyphrase):
        hd_file = None    
        search_videos = api.search_videos(
            query           = keyword,
            orientation     = '', size='', color='', locale='', page=1,
            per_page        = 1
        )
        for index, video in enumerate(search_videos.get('videos')):
            videos  = video.get('video_files')
            for entry in videos:
                if entry.get('height') == 720 or entry.get('width') == 1920:
                    hd_file = entry
            if hd_file is None:
                hd_file = videos[0]
            
            hd_file["keyword_caption"] = sentences[sentence_index] # --------- testing keyword
        print(hd_file)
        print('-------------')
        pexel_videos.append(hd_file)
    return pexel_videos


def submit(data):
    pexel_videos = pexel_searcher()
    min_clips   = 4.0
    max_clips   = 8.0
    clip_length = 2.0
    video_start = 4.0

    search_videos = api.search_videos(
        query           = data.get("search"),
        orientation     = '', size='', color='', locale='', page=1,
        per_page        = max_clips
    )
    
    with shotstack.ApiClient(configuration) as api_client:
        api_instance = edit_api.EditApi(api_client)
        video_clips  = []
        Caption_clips = []

        title_asset = TitleAsset(
            text        = data.get('title'),
            style       = "minimal",
            size        = "small"
        )

        title_transition = Transition(
            _in="fade",
            out="fade"
        )

        title_clip = Clip(
            asset       = title_asset,
            length      = video_start,
            start       = 0.0,
            transition  = title_transition,
            effect      = "zoomIn"
        )

        for index, video in enumerate(pexel_videos):
            # if index >= max_clips:
            #     break
            
            hd_file = None
            videos  = pexel_videos

            # for entry in videos:
            #     if entry.get('height') == 720 or entry.get('width') == 1920:
            #         hd_file = entry

            if hd_file is None:
                hd_file = videos[index]
            
            # ---CAPTIONS---------------
            # htmlAsset = HtmlAsset(
            # html      = f'<p>{video["keyword_caption"]}</p>',
            # css       = 'p { color: #FFFF00; }',
            # # width     = 800,
            # # height    = 100,
            # background= 'transparent',
            # position  = 'bottom'
            # )

            title_asset = TitleAsset(
            text        = video["keyword_caption"],
            style       = "subtitle",
            size        = "small",
            color      = '#FFFF00',
            position   = 'bottom',
            )


            Caption_clip = Clip(
                asset     = title_asset,
                start = video_start + (index * clip_length),
                length    = clip_length,
                fit       = 'crop',
                scale     = 0.0,
                position  = 'bottom',
                opacity   = 1.0,
            )

            Caption_clips.append(Caption_clip)
            
            #-------VIDEO----------------
            video_asset = VideoAsset(
                src = hd_file.get('link'),
                trim= 2.0
            )

            video_clip = Clip(
                asset = video_asset,
                start = video_start + (index * clip_length),
                length= clip_length
            )

            video_clips.append(video_clip)

            title_transition = Transition(
                _in="fade",
                out="fade"
            )

        soundtrack = Soundtrack(
            src         = f"{shotstack_assets_url}music/{data.get('soundtrack')}.mp3",
            effect      = "fadeOut"
        )

        timeline = Timeline(
            background  = "#000000",
            soundtrack  = soundtrack,
            tracks      = [Track(clips=Caption_clips),Track(clips=video_clips),Track(clips=[title_clip])]
        )

        output = Output(
            format      = "mp4",
            resolution  = "sd"
        )

        edit = Edit(
            timeline    = timeline,
            output      = output
        )

        return api_instance.post_render(edit)['response']

def status(render_id):
    with shotstack.ApiClient(configuration) as api_client:
        api_instance = edit_api.EditApi(api_client)

        
        return api_instance.get_render(render_id, data=True, merged=True)['response']


if __name__ == '__main__':
    import time
    request = {'title': 'CRypto-Currency', 'soundtrack': 'melodic'}
    response = submit(request)
    print(response)
    time.sleep(30)
    print(status(response.id))
    # print(status("b319fa2f-ad66-4274-a7c5-bf99d2b1bad3"))
    # var = pexel_searcher()
    # print(var)