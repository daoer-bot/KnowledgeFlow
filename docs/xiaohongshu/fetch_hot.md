# 获取小红书热榜/Fetch Xiaohongshu hot list

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /api/v1/xiaohongshu/web_v2/fetch_hot_list:
    get:
      summary: 获取小红书热榜/Fetch Xiaohongshu hot list
      deprecated: false
      description: |-
        # [中文]
        ### 用途:
        - 获取小红书热榜
        ### 返回:
        - 小红书热榜

        # [English]
        ### Purpose:
        - Get Xiaohongshu hot list
        ### Return:
        - Xiaohongshu hot list

        # [示例/Example]
      operationId: fetch_hot_list_api_v1_xiaohongshu_web_v2_fetch_hot_list_get
      tags:
        - Xiaohongshu-Web-V2-API
        - Xiaohongshu-Web-V2-API
      parameters: []
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResponseModel'
          headers: {}
          x-apifox-name: OK
      security:
        - HTTPBearer: []
          x-apifox:
            schemeGroups:
              - id: AkAs1X3hjceL6PSyLW1FD
                schemeIds:
                  - HTTPBearer
            required: true
            use:
              id: AkAs1X3hjceL6PSyLW1FD
            scopes:
              AkAs1X3hjceL6PSyLW1FD:
                HTTPBearer: []
      x-apifox-folder: Xiaohongshu-Web-V2-API
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/4705614/apis/api-321103382-run
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
响应数据结构
{
    "code": 200,
    "request_id": "b8d3aa0f-3ba6-4965-a857-87da832e8395",
    "message": "Request successful. This request will incur a charge.",
    "message_zh": "请求成功，本次请求将被计费。",
    "support": "Discord: https://discord.gg/aMEAS8Xsvz",
    "time": "2025-12-27 00:37:10",
    "time_stamp": 1766824630,
    "time_zone": "America/Los_Angeles",
    "docs": "https://api.tikhub.io/#/Xiaohongshu-Web-V2-API/fetch_hot_list_api_v1_xiaohongshu_web_v2_fetch_hot_list_get",
    "cache_message": "This request will be cached. You can access the cached result directly using the URL below, valid for 24 hours. Accessing the cache will not incur additional charges.",
    "cache_message_zh": "本次请求将被缓存，你可以使用下面的 URL 直接访问缓存结果，有效期为 24 小时，访问缓存不会产生额外费用。",
    "cache_url": "https://cache.tikhub.io/api/v1/cache/public/b8d3aa0f-3ba6-4965-a857-87da832e8395?sign=bd1de6b7647478b39c29518288d97bb8cb73a94b62af943702a06e037ecf6a5d",
    "router": "/api/v1/xiaohongshu/web_v2/fetch_hot_list",
    "params": {},
    "data": {
        "code": 0,
        "data": {
            "background_color": {},
            "host": "",
            "hot_list_id": "4840583",
            "is_new_hot_list_exp": true,
            "items": [
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/4d6304d79d71bd1f68611ae09184b778ec1a6d97.png",
                    "id": "dora_1989688",
                    "rank_change": 0,
                    "score": "941.4万",
                    "title": "小红书里的0.1%都来集合",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "独家"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1985182",
                    "rank_change": 8,
                    "score": "807.8万",
                    "title": "美甲界年终突击考研了",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1987177",
                    "rank_change": 15,
                    "score": "615.1万",
                    "title": "跨年仙女棒新拍法",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "id": "dora_1989489",
                    "rank_change": 7,
                    "score": "568.5万",
                    "title": "泰柬就停火问题签署联合声明",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "无"
                },
                {
                    "id": "dora_1989940",
                    "rank_change": 0,
                    "score": "557.9万",
                    "title": "我们P人搞装修是这样的",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "无"
                },
                {
                    "id": "dora_1989239",
                    "rank_change": 1,
                    "score": "542.8万",
                    "title": "我的年度美甲结算报告",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "无"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1989150",
                    "rank_change": 1,
                    "score": "536.6万",
                    "title": "6名大学生坠落事故调查结果",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1989490",
                    "rank_change": 6,
                    "score": "508.9万",
                    "title": "当飘雪遇见丁达尔效应",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "id": "dora_1989129",
                    "rank_change": -4,
                    "score": "491.4万",
                    "title": "原来飞驰人生3是出发团团建",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "无"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1986821",
                    "rank_change": -4,
                    "score": "453.6万",
                    "title": "研究生KTV吵架式解压",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/be184ffb03399b2ea1d28a81f3991aac3224f9d3.png",
                    "id": "dora_1987070",
                    "rank_change": 4,
                    "score": "447.5万",
                    "title": "马年跨年朋友圈搞笑文案",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "梗"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1987067",
                    "rank_change": 5,
                    "score": "446.7万",
                    "title": "学校的糖葫芦考上研了",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "id": "dora_1989642",
                    "rank_change": 12,
                    "score": "441.4万",
                    "title": "被薛之谦张弛新歌蝠唱服了",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "无"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1988472",
                    "rank_change": -12,
                    "score": "437.1万",
                    "title": "拍到了跟课本里一样标准的雪花",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1983488",
                    "rank_change": -12,
                    "score": "433.5万",
                    "title": "临时抱佛脚跟练跨年妆",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1990081",
                    "rank_change": 0,
                    "score": "431.5万",
                    "title": "我和王一博成攀岩搭子了",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/be184ffb03399b2ea1d28a81f3991aac3224f9d3.png",
                    "id": "dora_1987232",
                    "rank_change": 6,
                    "score": "427.9万",
                    "title": "萝卜纸巾界的差生连考场都找不到",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "梗"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1987069",
                    "rank_change": 9,
                    "score": "427.3万",
                    "title": "人 请你好好爱自己",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1986349",
                    "rank_change": -10,
                    "score": "423.2万",
                    "title": "老辈子谈恋爱又争又抢",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                },
                {
                    "icon": "https://picasso-static.xiaohongshu.com/fe-platform/cfd317ff14757c7ede6ef5176ec487589565e49e.png",
                    "id": "dora_1986855",
                    "rank_change": 6,
                    "score": "411.2万",
                    "title": "请选择你的2026幸运绳",
                    "title_img": "",
                    "type": "normal",
                    "word_type": "热"
                }
            ],
            "result": {
                "success": true
            },
            "scene": "",
            "title": "搜索发现",
            "word_request_id": "ee4906144eb94a4593b5ca84a6bb2880"
        },
        "msg": "成功",
        "success": true
    }
}