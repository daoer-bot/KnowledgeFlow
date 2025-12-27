# 搜索笔记 V3/Search notes V3

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /api/v1/xiaohongshu/web/search_notes_v3:
    get:
      summary: 搜索笔记 V3/Search notes V3
      deprecated: false
      description: |-
        # [中文]
        ### 用途:
        - 搜索笔记 V3
        ### 参数:
        - keyword: 搜索关键词
        - page: 页码，默认为1
        - sort: 排序方式
            - 综合排序（默认参数）: general
            - 最热排序: popularity_descending
            - 最新排序: time_descending
            - 最多评论: comment_descending
            - 最多收藏: collect_descending
        - noteType: 笔记类型
            - 综合笔记（默认参数）: _0
            - 视频笔记: _1
            - 图文笔记: _2
            - 直播: _3
        - noteTime: 发布时间
            - 不限: ""
            - 一天内 :一天内
            - 一周内 :一周内
            - 半年内 :半年内
        ### 返回:
        - 笔记列表

        # [English]
        ### Purpose:
        - Search notes V3
        ### Parameters:
        - keyword: Keyword
        - page: Page, default is 1
        - sort: Sort
            - General sort (default): general
            - Popularity sort: popularity_descending
            - Latest sort: time_descending
            - Most comments: comment_descending
            - Most favorites: collect_descending
        - noteType: Note type
            - General note (default): _0
            - Video note: _1
            - Image note: _2
            - Live: _3
        - noteTime: Release time
            - No limit: ""
            - Within one day: 一天内
            - Within one week: 一周内
            - Within half a year: 半年内
        ### Return:
        - Note list

        # [示例/Example]
        keyword="美食"
        page=1
        sort="general"
        noteType="_0"
      operationId: search_notes_v3_api_v1_xiaohongshu_web_search_notes_v3_get
      tags:
        - Xiaohongshu-Web-API
        - Xiaohongshu-Web-API
      parameters:
        - name: keyword
          in: query
          description: 搜索关键词/Keyword
          required: true
          example: 美食
          schema:
            type: string
            description: 搜索关键词/Keyword
            title: Keyword
        - name: page
          in: query
          description: 页码/Page
          required: false
          example: 1
          schema:
            type: integer
            description: 页码/Page
            default: 1
            title: Page
        - name: sort
          in: query
          description: 排序方式/Sort
          required: false
          example: general
          schema:
            type: string
            description: 排序方式/Sort
            default: general
            title: Sort
        - name: noteType
          in: query
          description: 笔记类型/Note type
          required: false
          example: _0
          schema:
            type: string
            description: 笔记类型/Note type
            default: _0
            title: Notetype
        - name: noteTime
          in: query
          description: 发布时间/Release time
          required: false
          example: ''
          schema:
            type: string
            description: 发布时间/Release time
            default: ''
            title: Notetime
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResponseModel'
          headers: {}
          x-apifox-name: OK
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
          headers: {}
          x-apifox-name: Parameter Error
      security:
        - HTTPBearer: []
          x-apifox:
            schemeGroups:
              - id: F228x4VE25Ek6v6DCu7Gd
                schemeIds:
                  - HTTPBearer
            required: true
            use:
              id: F228x4VE25Ek6v6DCu7Gd
            scopes:
              F228x4VE25Ek6v6DCu7Gd:
                HTTPBearer: []
      x-apifox-folder: Xiaohongshu-Web-API
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/4705614/apis/api-322238020-run
components:
  schemas:
    ResponseModel:
      properties:
        code:
          type: integer
          title: Code
          description: HTTP status code | HTTP状态码
          default: 200
        request_id:
          anyOf:
            - type: string
            - type: 'null'
          title: Request Id
          description: Unique request identifier | 唯一请求标识符
        message:
          type: string
          title: Message
          description: Response message (EN-US) | 响应消息 (English)
          default: Request successful. This request will incur a charge.
        message_zh:
          type: string
          title: Message Zh
          description: Response message (ZH-CN) | 响应消息 (中文)
          default: 请求成功，本次请求将被计费。
        support:
          type: string
          title: Support
          description: Support message | 支持消息
          default: 'Discord: https://discord.gg/aMEAS8Xsvz'
        time:
          type: string
          title: Time
          description: The time the response was generated | 生成响应的时间
        time_stamp:
          type: integer
          title: Time Stamp
          description: The timestamp the response was generated | 生成响应的时间戳
        time_zone:
          type: string
          title: Time Zone
          description: The timezone of the response time | 响应时间的时区
          default: America/Los_Angeles
        docs:
          anyOf:
            - type: string
            - type: 'null'
          title: Docs
          description: >-
            Link to the API Swagger documentation for this endpoint | 此端点的 API
            Swagger 文档链接
        cache_message:
          anyOf:
            - type: string
            - type: 'null'
          title: Cache Message
          description: Cache message (EN-US) | 缓存消息 (English)
          default: >-
            This request will be cached. You can access the cached result
            directly using the URL below, valid for 24 hours. Accessing the
            cache will not incur additional charges.
        cache_message_zh:
          anyOf:
            - type: string
            - type: 'null'
          title: Cache Message Zh
          description: Cache message (ZH-CN) | 缓存消息 (中文)
          default: 本次请求将被缓存，你可以使用下面的 URL 直接访问缓存结果，有效期为 24 小时，访问缓存不会产生额外费用。
        cache_url:
          anyOf:
            - type: string
            - type: 'null'
          title: Cache Url
          description: The URL to access the cached result | 访问缓存结果的 URL
        router:
          type: string
          title: Router
          description: The endpoint that generated this response | 生成此响应的端点
          default: ''
        params:
          type: string
        data:
          anyOf:
            - type: string
            - type: 'null'
          title: Data
          description: The response data | 响应数据
      type: object
      title: ResponseModel
      x-apifox-orders:
        - code
        - request_id
        - message
        - message_zh
        - support
        - time
        - time_stamp
        - time_zone
        - docs
        - cache_message
        - cache_message_zh
        - cache_url
        - router
        - params
        - data
      x-apifox-ignore-properties: []
      x-apifox-folder: ''
    HTTPValidationError:
      properties:
        detail:
          items:
            $ref: '#/components/schemas/ValidationError'
          type: array
          title: Detail
      type: object
      title: HTTPValidationError
      x-apifox-orders:
        - detail
      x-apifox-ignore-properties: []
      x-apifox-folder: ''
    ValidationError:
      properties:
        loc:
          items:
            anyOf:
              - type: string
              - type: integer
          type: array
          title: Location
        msg:
          type: string
          title: Message
        type:
          type: string
          title: Error Type
      type: object
      required:
        - loc
        - msg
        - type
      title: ValidationError
      x-apifox-orders:
        - loc
        - msg
        - type
      x-apifox-ignore-properties: []
      x-apifox-folder: ''
  securitySchemes:
    Bearer Token:
      type: bearer
      scheme: bearer
    HTTPBearer:
      type: bearer
      description: >
        ----

        #### API Token Introduction:

        ##### Method 1: Use API Token in the Request Header (Recommended)

        - **Header**: `Authorization`

        - **Format**: `Bearer {token}`

        - **Example**: `{"Authorization": "Bearer your_token"}`

        - **Swagger UI**: Click on the `Authorize` button in the upper right
        corner of the page to enter the API token directly without the `Bearer`
        keyword.


        ##### Method 2: Use API Token in the Cookie (Not Recommended, Use Only
        When Method 1 is Unavailable)

        - **Cookie**: `Authorization`

        - **Format**: `Bearer {token}`

        - **Example**: `Authorization=Bearer your_token`


        #### Get API Token:

        1. Register and log in to your account on the TikHub website.

        2. Go to the user center, click on the API token menu, and create an API
        token.

        3. Copy and use the API token in the request header.

        4. Keep your API token confidential and use it only in the request
        header.


        ----


        #### API令牌简介:

        ##### 方法一：在请求头中使用API令牌（推荐）

        - **请求头**: `Authorization`

        - **格式**: `Bearer {token}`

        - **示例**: `{"Authorization": "Bearer your_token"}`

        - **Swagger UI**: 点击页面右上角的`Authorize`按钮，直接输入API令牌，不需要`Bearer`关键字。


        ##### 方法二：在Cookie中使用API令牌（不推荐，仅在无法使用方法一时使用）

        - **Cookie**: `Authorization`

        - **格式**: `Bearer {token}`

        - **示例**: `Authorization=Bearer your_token`


        #### 获取API令牌:

        1. 在TikHub网站注册并登录账户。

        2. 进入用户中心，点击API令牌菜单，创建API令牌。

        3. 复制并在请求头中使用API令牌。

        4. 保密您的API令牌，仅在请求头中使用。
      scheme: bearer
servers:
  - url: https://api.tikhub.io
    description: Production Environment
security: []

```

接口响应结构
{
    "code": 200,
    "request_id": "ed0c9b35-91e6-4c13-b6cd-9bf8a44e81e1",
    "message": "Request successful. This request will incur a charge.",
    "message_zh": "请求成功，本次请求将被计费。",
    "support": "Discord: https://discord.gg/aMEAS8Xsvz",
    "time": "2025-12-27 00:36:08",
    "time_stamp": 1766824568,
    "time_zone": "America/Los_Angeles",
    "docs": "https://api.tikhub.io/#/Xiaohongshu-Web-API/search_notes_v3_api_v1_xiaohongshu_web_search_notes_v3_get",
    "cache_message": "This request will be cached. You can access the cached result directly using the URL below, valid for 24 hours. Accessing the cache will not incur additional charges.",
    "cache_message_zh": "本次请求将被缓存，你可以使用下面的 URL 直接访问缓存结果，有效期为 24 小时，访问缓存不会产生额外费用。",
    "cache_url": "https://cache.tikhub.io/api/v1/cache/public/ed0c9b35-91e6-4c13-b6cd-9bf8a44e81e1?sign=989d6e787d76b5e0f52d62f23a084eca48bc88c0c996e4c68052ec1da5959faa",
    "router": "/api/v1/xiaohongshu/web/search_notes_v3",
    "params": {
        "keyword": "美食",
        "noteTime": "",
        "noteType": "_0",
        "page": "1",
        "sort": "general"
    },
    "data": {
        "code": 0,
        "data": {
            "can_cut": false,
            "cur_cut_number": 0,
            "search_request_id": "6b3de1a1c9ac47fb935f06a0ec725478",
            "items": [
                {
                    "model_type": "note",
                    "note": {
                        "shared_count": 0,
                        "advanced_widgets_groups": {
                            "groups": [
                                {
                                    "mode": 1,
                                    "fetch_types": [
                                        "guos_test",
                                        "note_next_step",
                                        "second_jump_bar",
                                        "note_collection",
                                        "cooperate_binds",
                                        "rec_next_infos",
                                        "video_marks",
                                        "product_review",
                                        "related_search",
                                        "video_goods_cards",
                                        "cooperate_comment_component",
                                        "ads_goods_cards",
                                        "ads_comment_component",
                                        "goods_card_v2",
                                        "video_recommend_tag",
                                        "buyable_goods_card_v2",
                                        "cooperate_search_component",
                                        "ads_engage_bar",
                                        "challenge_card",
                                        "cooperate_engage_bar",
                                        "pgy_comment_component",
                                        "pgy_engage_bar",
                                        "related_recommend",
                                        "next_note_guide",
                                        "widgets_ndb",
                                        "pgy_bbc_exp",
                                        "brand_max_trailer",
                                        "super_activity",
                                        "note_nice_guide",
                                        "pin_search_highlights",
                                        "widgets_enhance",
                                        "packed_goods",
                                        "packed_buyable_goods",
                                        "widgets_ncb",
                                        "note_nice_compound",
                                        "live_shooting_flag",
                                        "widgets_nbb",
                                        "poi_declare",
                                        "async_group"
                                    ]
                                },
                                {
                                    "mode": 0,
                                    "fetch_types": [
                                        "guos_test",
                                        "vote_stickers",
                                        "bullet_comment_lead",
                                        "note_search_box",
                                        "interact_pk",
                                        "interact_vote",
                                        "guide_heuristic",
                                        "guide_post",
                                        "video_foot_bar",
                                        "follow_guide",
                                        "share_to_msg",
                                        "note_share_prompt_v1",
                                        "note_share_prompt_v2",
                                        "group_share",
                                        "share_guide_bubble",
                                        "goods_enhance_component",
                                        "guide_navigator",
                                        "sync_group"
                                    ]
                                }
                            ]
                        },
                        "collected": false,
                        "images_list": [
                            {
                                "original": "",
                                "trace_id": "1040g00831qj7ilp10m3g5obt7460j8opimu04dg",
                                "need_load_original_image": false,
                                "fileid": "1040g00831qj7ilp10m3g5obt7460j8opimu04dg",
                                "height": 1440,
                                "width": 1920,
                                "url": "https://sns-na-i8.xhscdn.com/1040g00831qj7ilp10m3g5obt7460j8opimu04dg?imageView2/2/w/640/format/heif/q/56|imageMogr2/strip&redImage/frame/0/enhance/4&ap=5&sc=SRH_PRV&sign=6f87611f0e23bde4654b4d2a208c9b35&t=694f9a77",
                                "url_size_large": "https://sns-na-i8.xhscdn.com/1040g00831qj7ilp10m3g5obt7460j8opimu04dg?imageView2/2/w/1440/format/heif/q/46&redImage/frame/0&ap=5&sc=SRH_DTL&sign=6f87611f0e23bde4654b4d2a208c9b35&t=694f9a77"
                            }
                        ],
                        "liked_count": 0,
                        "debug_info_str": "",
                        "liked": false,
                        "user": {
                            "show_red_official_verify_icon": false,
                            "red_official_verified": false,
                            "track_duration": 0,
                            "followed": false,
                            "FStatus": "none",
                            "red_id": "5311518605",
                            "nickname": "日月岛康养旅游度假区",
                            "images": "https://sns-avatar-qc.xhscdn.com/avatar/6620cf1a9f8f370001993a03.jpg?imageView2/2/w/80/format/jpg",
                            "red_official_verify_type": 0,
                            "userid": "617d390c000000000201a319"
                        },
                        "tag_info": {
                            "title": "",
                            "type": ""
                        },
                        "note_attributes": [],
                        "corner_tag_info": [
                            {
                                "location": -1,
                                "type": "ubt_sig_token",
                                "icon": "",
                                "text": "RAW2hHYvqy2K2KnLRGsachQIl4ks7QtK/H+wzVMfS8QAloVju/OuKqviOgjsXSsWxPPnomEk82tioD0avkIgu1ol65Yw6F9Jpb",
                                "text_en": "",
                                "style": 0
                            },
                            {
                                "text_en": "1 hrs ago",
                                "style": 0,
                                "location": 5,
                                "type": "publish_time",
                                "icon": "http://picasso-static.xiaohongshu.com/fe-platform/e9b67af62f67d9d6cfac936f96ad10a85fdb868e.png",
                                "text": "1小时前"
                            },
                            {
                                "location": 0,
                                "style": 0,
                                "poi_id": "423046464B5356564B35"
                            }
                        ],
                        "widgets_context": "{\"video\":true,\"origin_video_key\":\"pre_post/1040g2t031qj7inde70p05obt7460j8opdsl57oo\",\"flags\":{\"sound_track\":true},\"author_id\":\"617d390c000000000201a319\",\"author_name\":\"日月岛康养旅游度假区\",\"video_duration\":61}",
                        "desc": "东南亚肉骨茶×鲜肉馄饨？这波“混搭”太绝了！来#日月岛 必须狠狠安排上！ #盐城日月岛#盐城美食#美食双拼#暖心冬日#日月岛必吃#地球村食评人大赛[话题]# #随时享受地道中国味[话题]# #民以食为先[话题]# #奇迹中国味[话题]# #美食背后的故事[话题]# #",
                        "type": "video",
                        "video_info_v2": {
                            "capa": {
                                "duration": 61,
                                "frame_ts": 0,
                                "is_user_select": false,
                                "is_upload": false
                            },
                            "consumer": {
                                "can_super_resolution": false
                            },
                            "media": {
                                "video_id": 137728697860969105,
                                "video": {
                                    "height": 2160,
                                    "biz_id": "281843886844281834",
                                    "stream_types": [
                                        258,
                                        114,
                                        76,
                                        115
                                    ],
                                    "md5": "db659bfb8a501584d23b9431a300a7fb",
                                    "hdr_type": 0,
                                    "drm_type": 0,
                                    "bound": [
                                        {
                                            "x": 0,
                                            "y": 0,
                                            "w": 0,
                                            "h": 0
                                        }
                                    ],
                                    "opaque1": {
                                        "audioClsInfo": "{\"music_ratio\":0.9750849219368237,\"freesound_ratio\":0.444588247134958,\"speech_ratio\":0.6151108135397053}",
                                        "hasHumanVoice": "true",
                                        "isSupportSubtitle": "true",
                                        "videoLanguage": "[\"zh-CN\"]",
                                        "insertSubtitleLanguages": "[\"zh-CN\"]",
                                        "loudnorm": "{\"lra\":5.1,\"htp\":0.05,\"hldn\":-9.43,\"ldn\":-10.47,\"thr\":-20.49}",
                                        "amend": "30",
                                        "amend_2k": "25",
                                        "audioLevInfo": "{\"audio_quality_level\":\"G+\",\"mos_overall\":3.3308,\"version\":\"3.0\"}",
                                        "weakNetUserFlag": "1",
                                        "domestic": "1",
                                        "amend_mobile": "40",
                                        "amend_4k": "25"
                                    },
                                    "width": 3840,
                                    "biz_name": 110,
                                    "duration": 62
                                },
                                "stream": {
                                    "h264": [
                                        {
                                            "stream_type": 258,
                                            "fps": 30,
                                            "opaque1": {
                                                "use_pcdn": "0",
                                                "pcdn_302_flag": "false",
                                                "didLoudnorm": "false",
                                                "pcdn_supplier": ""
                                            },
                                            "audio_codec": "aac",
                                            "rotate": 0,
                                            "stream_desc": "X264_MP4",
                                            "format": "mp4",
                                            "video_duration": 61833,
                                            "vmaf": -1,
                                            "quality_type": "HD",
                                            "size": 15534880,
                                            "avg_bitrate": 2007576,
                                            "audio_bitrate": 56151,
                                            "backup_urls": [
                                                "http://sns-bak-v8.xhscdn.com/stream/79/110/258/01e94f855f6152914f0370019b5ea295ca_258.mp4",
                                                "http://sns-bak-v10.xhscdn.com/stream/79/110/258/01e94f855f6152914f0370019b5ea295ca_258.mp4"
                                            ],
                                            "hdr_type": 0,
                                            "weight": 47,
                                            "master_url": "http://sns-video-zl.xhscdn.com/stream/79/110/258/01e94f855f6152914f0370019b5ea295ca_258.mp4",
                                            "default_stream": 0,
                                            "height": 720,
                                            "video_bitrate": 1946865,
                                            "psnr": 0,
                                            "width": 1280,
                                            "volume": 0,
                                            "video_codec": "h264",
                                            "audio_duration": 61904,
                                            "audio_channels": 2,
                                            "duration": 61905,
                                            "ssim": 0,
                                            "sr": 0
                                        }
                                    ],
                                    "h265": [
                                        {
                                            "stream_type": 114,
                                            "height": 720,
                                            "backup_urls": [
                                                "http://sns-bak-v8.xhscdn.com/stream/79/110/114/01e94f855f6152914f0370019b5ea3d9d7_114.mp4",
                                                "http://sns-bak-v10.xhscdn.com/stream/79/110/114/01e94f855f6152914f0370019b5ea3d9d7_114.mp4"
                                            ],
                                            "weight": 48,
                                            "quality_type": "HD",
                                            "audio_codec": "aac",
                                            "audio_bitrate": 128287,
                                            "hdr_type": 0,
                                            "master_url": "http://sns-video-zl.xhscdn.com/stream/79/110/114/01e94f855f6152914f0370019b5ea3d9d7_114.mp4",
                                            "vmaf": -1,
                                            "width": 1280,
                                            "video_duration": 61844,
                                            "audio_duration": 61904,
                                            "size": 8804944,
                                            "video_bitrate": 1002584,
                                            "opaque1": {
                                                "didLoudnorm": "false",
                                                "roiWeight": "87.470074",
                                                "pcdn_supplier": "",
                                                "roi_info": "{\"alpha\":\"1.0\",\"gamma\":\"0.0\",\"lambda\":\"1.5E-6\",\"mvmaf\":\"88.97395\"}",
                                                "use_pcdn": "1",
                                                "pcdn_302_flag": "false"
                                            },
                                            "stream_desc": "R265_MP4_720P_114_android",
                                            "format": "mp4",
                                            "duration": 61905,
                                            "psnr": 40.30400085449219,
                                            "ssim": 0,
                                            "volume": 0,
                                            "fps": 29,
                                            "audio_channels": 2,
                                            "avg_bitrate": 1137865,
                                            "video_codec": "hevc",
                                            "default_stream": 1,
                                            "rotate": 0,
                                            "sr": 0
                                        },
                                        {
                                            "height": 1440,
                                            "size": 15451036,
                                            "psnr": 43.27799987792969,
                                            "quality_type": "2K",
                                            "stream_type": 76,
                                            "default_stream": 0,
                                            "width": 2560,
                                            "video_codec": "hevc",
                                            "audio_bitrate": 128287,
                                            "master_url": "http://sns-video-zl.xhscdn.com/stream/1/110/76/01e94f855f615291010370019b5ea2d824_76.mp4",
                                            "sr": 0,
                                            "duration": 61905,
                                            "volume": 0,
                                            "video_duration": 61844,
                                            "rotate": 0,
                                            "ssim": 0,
                                            "weight": 49,
                                            "opaque1": {
                                                "roiWeight": "87.814867",
                                                "pcdn_supplier": "",
                                                "roi_info": "{\"alpha\":\"1.0\",\"gamma\":\"0.0\",\"lambda\":\"1.5E-6\",\"mvmaf\":\"90.60832\"}",
                                                "use_pcdn": "0",
                                                "pcdn_302_flag": "false",
                                                "didLoudnorm": "false"
                                            },
                                            "stream_desc": "R265_MP4_2K4K_76_ANDR_prediction",
                                            "format": "mp4",
                                            "fps": 29,
                                            "video_bitrate": 1862302,
                                            "backup_urls": [
                                                "http://sns-bak-v8.xhscdn.com/stream/1/110/76/01e94f855f615291010370019b5ea2d824_76.mp4",
                                                "http://sns-bak-v10.xhscdn.com/stream/1/110/76/01e94f855f615291010370019b5ea2d824_76.mp4"
                                            ],
                                            "hdr_type": 0,
                                            "avg_bitrate": 1996741,
                                            "audio_codec": "aac",
                                            "audio_duration": 61904,
                                            "audio_channels": 2,
                                            "vmaf": -1
                                        },
                                        {
                                            "video_codec": "hevc",
                                            "default_stream": 0,
                                            "avg_bitrate": 1533935,
                                            "audio_channels": 2,
                                            "sr": 0,
                                            "video_duration": 61844,
                                            "audio_codec": "aac",
                                            "width": 1920,
                                            "format": "mp4",
                                            "audio_bitrate": 128287,
                                            "master_url": "http://sns-video-zl.xhscdn.com/stream/1/110/115/01e94f855f615291010370019b5ea3b724_115.mp4",
                                            "psnr": 41.005001068115234,
                                            "ssim": 0,
                                            "vmaf": -1,
                                            "weight": 50,
                                            "quality_type": "FHD",
                                            "stream_desc": "R265_MP4_1080P_115_low_device_0",
                                            "height": 1080,
                                            "size": 11869781,
                                            "volume": 0,
                                            "fps": 29,
                                            "stream_type": 115,
                                            "video_bitrate": 1399041,
                                            "opaque1": {
                                                "didLoudnorm": "false",
                                                "roiWeight": "90.5265585",
                                                "pcdn_supplier": "",
                                                "roi_info": "{\"alpha\":\"1.0\",\"gamma\":\"0.0\",\"lambda\":\"1.5E-6\",\"mvmaf\":\"92.62512\"}",
                                                "use_pcdn": "1",
                                                "pcdn_302_flag": "false"
                                            },
                                            "duration": 61905,
                                            "audio_duration": 61904,
                                            "rotate": 0,
                                            "backup_urls": [
                                                "http://sns-bak-v8.xhscdn.com/stream/1/110/115/01e94f855f615291010370019b5ea3b724_115.mp4",
                                                "http://sns-bak-v10.xhscdn.com/stream/1/110/115/01e94f855f615291010370019b5ea3b724_115.mp4"
                                            ],
                                            "hdr_type": 0
                                        }
                                    ],
                                    "h266": [],
                                    "av1": []
                                },
                                "user_level": 0
                            },
                            "image": {
                                "thumbnail_dim": "https://sns-na-i8.xhscdn.com/frame/110/0/01e94f855f6152910010000000019b5ea2f2d5_0.webp?imageView2/2/w/720/h/720/format/heif/q/46&ap=5&sc=SRH_SPRT&sign=8df7115776f6162814dd257ef49c1359&t=694f9a77",
                                "first_frame": "https://sns-na-i8.xhscdn.com/110/0/01e94f855f6152910010000000019b5ea1d633_0.jpg?imageView2/2/w/1440/format/heif/q/46&redImage/frame/0&ap=5&sc=SRH_DTL&sign=5f24743407a4c00e7724dc5bba3fec69&t=694f9a77",
                                "thumbnail": "https://sns-na-i8.xhscdn.com/frame/110/0/01e94f855f6152910010000000019b5ea2f2d5_0.webp?imageView2/2/w/5000/h/5000/format/heif/q/56&redImage/frame/0&ap=5&sc=SRH_ORG&sign=8df7115776f6162814dd257ef49c1359&t=694f9a77"
                            }
                        },