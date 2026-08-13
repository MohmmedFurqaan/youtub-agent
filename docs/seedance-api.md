# Seedance 2 5 API Documentation

> Generate content using the Seedance 2 5 model

## Overview

This document describes how to use the Seedance 2 5 model for content generation. The process consists of two steps:
1. Create a generation task
2. Query task status and results

## Authentication

All API requests require a Bearer Token in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

Get API Key:
1. Visit [API Key Management Page](https://kie.ai/api-key) to get your API Key
2. Add to request header: `Authorization: Bearer YOUR_API_KEY`

---

## 1. Create Generation Task

### API Information
- **URL**: `POST https://api.kie.ai/api/v1/jobs/createTask`
- **Content-Type**: `application/json`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model name, format: `bytedance/seedance-2-5` |
| input | object | Yes | Input parameters object |
| callBackUrl | string | No | Callback URL for task completion notifications. If provided, the system will send POST requests to this URL when the task completes (success or fail). If not provided, no callback notifications will be sent. Example: `"https://your-domain.com/api/callback"` |

### Model Parameter

The `model` parameter specifies which AI model to use for content generation.

| Property | Value | Description |
|----------|-------|-------------|
| **Format** | `bytedance/seedance-2-5` | The exact model identifier for this API |
| **Type** | string | Must be passed as a string value |
| **Required** | Yes | This parameter is mandatory for all requests |

> **Note**: The model parameter must match exactly as shown above. Different models have different capabilities and parameter requirements.

### Callback URL Parameter

The `callBackUrl` parameter allows you to receive automatic notifications when your task completes.

| Property | Value | Description |
|----------|-------|-------------|
| **Purpose** | Task completion notification | Receive real-time updates when your task finishes |
| **Method** | POST request | The system sends POST requests to your callback URL |
| **Timing** | When task completes | Notifications sent for both success and failure states |
| **Content** | Query Task API response | Callback content structure is identical to the Query Task API response |
| **Parameters** | Complete request data | The `param` field contains the complete Create Task request parameters, not just the input section |
| **Optional** | Yes | If not provided, no callback notifications will be sent |

**Important Notes:**
- The callback content structure is identical to the Query Task API response
- The `param` field contains the complete Create Task request parameters, not just the input section  
- If `callBackUrl` is not provided, no callback notifications will be sent

### input Object Parameters

#### first_frame_url
- **Type**: `string`
- **Required**: No
- **Description**: first_frame_url
- **Max File Size**: 30MB
- **Accepted File Types**: image/jpeg, image/jpeg, image/png, image/webp, image/gif

#### last_frame_url
- **Type**: `string`
- **Required**: No
- **Description**: last_frame_url
- **Max File Size**: 30MB
- **Accepted File Types**: image/jpeg, image/jpeg, image/png, image/webp, image/gif

#### prompt
- **Type**: `string`
- **Required**: No
- **Description**: The text prompt or description for the video.
- **Max Length**: 30000 characters
- **Default Value**: `"Reference @Image1 @Image2 for the spear-wielding character, @Image3 @Image4 for the scene. Generate a martial arts action sequence where the character performs fluid spear techniques. Use multi-angle tracking shots to capture the power and beauty of martial arts."`

#### reference_image_urls
- **Type**: `array`
- **Required**: No
- **Description**: Please provide the URL of the uploaded file, A list of input image URLs.
- **Max File Size**: 30MB
- **Accepted File Types**: image/jpeg, image/png, image/webp, image/jpg
- **Multiple Files**: Yes
- **Default Value**: `["https://static.aiquickdraw.com/tools/example/1786092891389_T0JK8jQL.png","https://static.aiquickdraw.com/tools/example/1786092908885_6l0CRkwT.png"]`

#### reference_video_urls
- **Type**: `array`
- **Required**: No
- **Description**: Please provide the URL of the uploaded file, A list of input video URLs. Furthermore, the total length of the three videos must not exceed 30 seconds.
- **Max File Size**: 200MB
- **Accepted File Types**: video/mp4, video/quicktime, video/x-matroska
- **Multiple Files**: Yes
- **Default Value**: `["https://static.aiquickdraw.com/tools/example/1786093001312_B9PoOxnN.mp4"]`

#### reference_audio_urls
- **Type**: `array`
- **Required**: No
- **Description**: Please provide the URL of the uploaded file, A list of input audio URLs. Furthermore, the total length of the three audios must not exceed 30 seconds.
- **Max File Size**: 15MB
- **Accepted File Types**: audio/mpeg, audio/wav, audio/x-wav, audio/aac, audio/mp4, audio/ogg
- **Multiple Files**: Yes
- **Default Value**: `["https://static.aiquickdraw.com/tools/example/1786093062974_6T2WB0cA.mp3"]`

#### generate_audio
- **Type**: `boolean`
- **Required**: No
- **Description**: Whether to generate AI audio synchronized with the video.
- **Default Value**: `true`

#### return_last_frame
- **Type**: `boolean`
- **Required**: No
- **Description**: Whether to return the last frame of the video. When draft=true, this parameter cannot be set to true.

#### resolution
- **Type**: `string`
- **Required**: No
- **Description**: The output video resolution.
- **Options**:
  - `480p`: 480p
  - `720p`: 720p
- **Default Value**: `"720p"`

#### aspect_ratio
- **Type**: `string`
- **Required**: No
- **Description**: The aspect ratio of the generated video.
- **Options**:
  - `16:9`: 16:9
  - `4:3`: 4:3
  - `1:1`: 1:1
  - `3:4`: 3:4
  - `9:16`: 9:16
  - `21:9`: 21:9
  - `adaptive`: adaptive
- **Default Value**: `"adaptive"`

#### duration
- **Type**: `number`
- **Required**: No
- **Description**: Video duration in seconds.
- **Range**: -1 - 30 (step: 1)
- **Default Value**: `5`

#### output_format
- **Type**: `string`
- **Required**: No
- **Description**: Video output format.
- **Options**:
  - `mp4`: mp4
  - `mov`: mov
- **Default Value**: `"mp4"`

#### web_search
- **Type**: `boolean`
- **Required**: No
- **Description**: Enable online search?
- **Default Value**: `false`

#### nsfw_checker
- **Type**: `boolean`
- **Required**: No
- **Description**: A configurable parameter. Defaults to true in the Playground.
- **Default Value**: `true`

### Request Example

```json
{
  "model": "bytedance/seedance-2-5",
  "input": {
    "first_frame_url": "",
    "last_frame_url": "",
    "prompt": "Reference @Image1 @Image2 for the spear-wielding character, @Image3 @Image4 for the scene. Generate a martial arts action sequence where the character performs fluid spear techniques. Use multi-angle tracking shots to capture the power and beauty of martial arts.",
    "reference_image_urls": ["https://static.aiquickdraw.com/tools/example/1786092891389_T0JK8jQL.png","https://static.aiquickdraw.com/tools/example/1786092908885_6l0CRkwT.png"],
    "reference_video_urls": ["https://static.aiquickdraw.com/tools/example/1786093001312_B9PoOxnN.mp4"],
    "reference_audio_urls": ["https://static.aiquickdraw.com/tools/example/1786093062974_6T2WB0cA.mp3"],
    "generate_audio": true,
    "return_last_frame": true,
    "resolution": "720p",
    "aspect_ratio": "adaptive",
    "duration": 5,
    "output_format": "mp4",
    "web_search": false,
    "nsfw_checker": true
  }
}
```
### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9"
  }
}
```

### Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| code | integer | Response status code, 200 indicates success |
| msg | string | Response message |
| data.taskId | string | Task ID for querying task status |

---

## 2. Query Task Status

### API Information
- **URL**: `GET https://api.kie.ai/api/v1/jobs/recordInfo`
- **Parameter**: `taskId` (passed via URL parameter)

### Request Example
```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=281e5b0*********************f39b9
```

### Response Example

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "281e5b0*********************f39b9",
    "model": "bytedance/seedance-2-5",
    "state": "waiting",
    "param": "{\"model\":\"bytedance/seedance-2-5\",\"input\":{\"first_frame_url\":\"\",\"last_frame_url\":\"\",\"prompt\":\"Reference @Image1 @Image2 for the spear-wielding character, @Image3 @Image4 for the scene. Generate a martial arts action sequence where the character performs fluid spear techniques. Use multi-angle tracking shots to capture the power and beauty of martial arts.\",\"reference_image_urls\":[\"https://static.aiquickdraw.com/tools/example/1786092891389_T0JK8jQL.png\",\"https://static.aiquickdraw.com/tools/example/1786092908885_6l0CRkwT.png\"],\"reference_video_urls\":[\"https://static.aiquickdraw.com/tools/example/1786093001312_B9PoOxnN.mp4\"],\"reference_audio_urls\":[\"https://static.aiquickdraw.com/tools/example/1786093062974_6T2WB0cA.mp3\"],\"generate_audio\":true,\"return_last_frame\":true,\"resolution\":\"720p\",\"aspect_ratio\":\"adaptive\",\"duration\":5,\"output_format\":\"mp4\",\"web_search\":false,\"nsfw_checker\":true}}",
    "resultJson": "{\"resultUrls\":[\"https://static.aiquickdraw.com/tools/example/1786093098205_DMt8m5z9.mp4\"]}",
    "failCode": null,
    "failMsg": null,
    "costTime": null,
    "completeTime": null,
    "createTime": 1757584164490
  }
}
```

### Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| code | integer | Response status code, 200 indicates success |
| msg | string | Response message |
| data.taskId | string | Task ID |
| data.model | string | Model name used |
| data.state | string | Task status: `waiting`(waiting),  `success`(success), `fail`(fail) |
| data.param | string | Task parameters (JSON string) |
| data.resultJson | string | Task result (JSON string, available when task is success). Structure depends on outputMediaType: `{resultUrls: []}` for image/media/video, `{resultObject: {}}` for text |
| data.failCode | string | Failure code (available when task fails) |
| data.failMsg | string | Failure message (available when task fails) |
| data.costTime | integer | Task duration in milliseconds (available when task is success) |
| data.completeTime | integer | Completion timestamp (available when task is success) |
| data.createTime | integer | Creation timestamp |

---

## Usage Flow

1. **Create Task**: Call `POST https://api.kie.ai/api/v1/jobs/createTask` to create a generation task
2. **Get Task ID**: Extract `taskId` from the response
3. **Wait for Results**: 
   - If you provided a `callBackUrl`, wait for the callback notification
   - If no `callBackUrl`, poll status by calling `GET https://api.kie.ai/api/v1/jobs/recordInfo`
4. **Get Results**: When `state` is `success`, extract generation results from `resultJson`

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request successful |
| 400 | Invalid request parameters |
| 401 | Authentication failed, please check API Key |
| 402 | Insufficient account balance |
| 404 | Resource not found |
| 422 | Parameter validation failed |
| 429 | Request rate limit exceeded |
| 500 | Internal server error |

