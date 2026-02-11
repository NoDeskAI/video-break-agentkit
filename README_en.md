# Video Breakdown Analyzer

## Overview

This is an intelligent short-video analysis system built on Volcengine VeADK & AgentKit. The system adopts a Multi-Agent architecture, integrating FFmpeg video processing, Volcengine ASR speech recognition, LiteLLM multimodal vision analysis, and TOS object storage, capable of comprehensive professional analysis of short videos.

## Core Features

This project provides the following core capabilities:

- **Video Scene Segmentation**: Automatically identifies video scenes based on FFmpeg, extracts key frames and analyzes visual content, outputting structured scene data
- **First 3-Second Hook Analysis**: Professional scoring from 5 dimensions: visual impact, language hooks, emotional arousal, information density, and rhythm control
- **Professional Report Generation**: Integrates scene data and hook analysis results to generate complete analysis reports in Markdown format
- **Web Search**: Real-time access to the latest short-video industry information, platform rules, and trending topics

## Agent Architecture

![Video Breakdown Agent with AgentKit Runtime](assets/architecture_video_breakdown_agent.jpg)

```text
User Input (Video URL/Local File)
    ↓
AgentKit Runtime
    ↓
Root Agent (XiaoShi - Main Orchestrator)
    ├── Breakdown Agent (Scene Segmentation)
    │   ├── FFmpeg Video Preprocessing
    │   ├── Volcengine ASR Speech Recognition
    │   ├── LiteLLM Vision Analysis
    │   └── BGM Analysis
    ├── Hook Analyzer Agent (Hook Analysis)
    │   ├── First 3-Second Scene Extraction
    │   ├── Multimodal Vision Scoring
    │   └── JSON Formatting
    ├── Report Generator Agent (Report Generation)
    └── Search Agent (Web Search)
```

Main Volcengine products and Agent components:

- Ark LLM Platform:
  - doubao-seed-1-6-251015 (primary reasoning model)
  - doubao-seed-1-6-vision-250815 (vision analysis model)
- TOS Object Storage
- Volcengine ASR Speech Recognition (optional)
- Web Search
- AgentKit
- APMPlus (optional observability)

Third-party dependencies:

- FFmpeg (auto-packaged via imageio-ffmpeg, no manual installation required)
- LiteLLM (supports Gemini, Doubao, GPT-4o and other vision models)

## Directory Structure

```bash
video_breakdown_agent/
├── README.md                   # Project documentation (Chinese)
├── README_en.md                # Project documentation (English)
├── README_CONFIG.md            # Detailed configuration guide
├── project.toml                # Application marketplace metadata
├── agent.py                    # AgentKit deployment entry
├── requirements.txt            # pip dependencies
├── pyproject.toml              # uv project configuration
├── config.yaml                 # Configuration file (example, actual keys injected via env vars)
├── config.yaml.example         # Configuration template
├── deploy.sh                   # Deployment script
├── video_breakdown_agent/      # Python package (core code)
│   ├── agent.py                # Root Agent definition
│   ├── prompt.py               # Main orchestration prompt
│   ├── sub_agents/             # Sub Agents
│   │   ├── breakdown_agent/    # Scene segmentation Agent
│   │   ├── hook_analyzer_agent/# Hook analysis Agent (SequentialAgent)
│   │   └── report_generator_agent/  # Report generation Agent
│   ├── tools/                  # Tool functions
│   │   ├── process_video.py    # Video preprocessing (FFmpeg + ASR)
│   │   ├── analyze_segments_vision.py  # Vision analysis
│   │   ├── analyze_bgm.py      # BGM analysis
│   │   ├── analyze_hook_segments.py    # Hook scene extraction
│   │   ├── report_generator.py # Report generation
│   │   └── video_upload.py     # TOS video upload
│   ├── hook/                   # Callback hooks
│   │   ├── format_hook.py      # JSON repair
│   │   └── video_upload_hook.py# File upload interceptor
│   └── utils/                  # Utility classes
│       └── types.py            # Pydantic data models
└── img/                        # Architecture diagrams and screenshots
```

## Local Development

### Prerequisites

**Python Version:**

- Python 3.12 or higher

**1. Enable Volcengine Ark Model Service:**

- Visit [Volcengine Ark Console](https://console.volcengine.com/ark/region:ark+cn-beijing/overview)
- Enable model inference service
- Create API Key (used for `MODEL_AGENT_API_KEY`)

**2. Create TOS Bucket (for video upload):**

- Visit [TOS Console](https://console.volcengine.com/tos/bucket)
- Create a new bucket (e.g., `video-breakdown-uploads`)
- Set region to `cn-beijing`
- Configure public read permissions (or use pre-signed URLs)

**3. Obtain Volcengine Access Keys:**

- Visit [IAM Key Management](https://console.volcengine.com/iam/keymanage/)
- Create Access Key/Secret Key (used for `VOLCENGINE_ACCESS_KEY` and `VOLCENGINE_SECRET_KEY`)

**4. (Optional) Configure ASR Service:**

- Visit [Speech Service](https://console.volcengine.com/speech/service/list) to obtain App ID and Access Key
- If not configured, the system will gracefully degrade (skip speech recognition)

### Dependency Installation

**Method 1: Using pip**

```bash
pip install -r requirements.txt
```

**Method 2: Using uv (recommended)**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Environment Configuration

**Method 1: Create `.env` file (recommended for local development)**

```bash
# Copy configuration template
cp config.yaml.example config.yaml

# Edit .env file and fill in the following required environment variables:
MODEL_AGENT_API_KEY=your_ark_api_key
VOLCENGINE_ACCESS_KEY=your_volcengine_ak
VOLCENGINE_SECRET_KEY=your_volcengine_sk
DATABASE_TOS_BUCKET=your_tos_bucket_name
DATABASE_TOS_REGION=cn-beijing

# Optional: ASR configuration (graceful degradation if not configured)
ASR_APP_ID=your_asr_app_id
ASR_ACCESS_KEY=your_asr_access_key

# Optional: Vision model configuration (defaults to Doubao if not configured)
MODEL_VISION_NAME=doubao-seed-1-6-vision-250815
# Or use Gemini:
# MODEL_VISION_NAME=gemini/gemini-2.5-pro
# GEMINI_API_KEY=your_gemini_api_key
```

**Method 2: Use environment variables directly**

```bash
export MODEL_AGENT_API_KEY=your_ark_api_key
export VOLCENGINE_ACCESS_KEY=your_volcengine_ak
export VOLCENGINE_SECRET_KEY=your_volcengine_sk
export DATABASE_TOS_BUCKET=your_tos_bucket_name
```

**Priority**: System environment variables > `.env` file > `config.yaml`

For detailed configuration instructions, see [README_CONFIG.md](README_CONFIG.md).

### Running the Application

**Method 1: Local debugging with veadk web (recommended)**

```bash
# veadk automatically discovers video_breakdown_agent/ package
uv run veadk web
```

Access `http://localhost:8000` to interact with the Agent.

**Method 2: Run directly**

```bash
python agent.py
```

**Method 3: Smoke test**

```bash
# Quick test
uv run python .scripts/smoke_test.py "Hello"

# Full pipeline test
uv run python .scripts/smoke_test.py --pipeline-cases
```

## AgentKit Deployment

### Prerequisites

**Install AgentKit CLI:**

```bash
pip install agentkit
```

### One-Click Deployment

**1. Initialize configuration:**

```bash
# Configure AgentKit credentials
agentkit config --account-id YOUR_ACCOUNT_ID --access-key YOUR_AK --secret-key YOUR_SK
```

**2. Deploy to cloud:**

```bash
# Deploy (automatically creates Runtime, builds image, deploys)
agentkit launch

# View deployment status
agentkit status

# View Runtime logs
agentkit logs
```

**3. Configure environment variables in console:**

After deployment, you need to configure the following environment variables in the [AgentKit Console](https://console.volcengine.com/agentkit):

- `MODEL_AGENT_API_KEY`: Ark API Key
- `VOLCENGINE_ACCESS_KEY`: Volcengine Access Key
- `VOLCENGINE_SECRET_KEY`: Volcengine Secret Key
- `DATABASE_TOS_BUCKET`: TOS bucket name
- `DATABASE_TOS_REGION`: TOS region (default: `cn-beijing`)

**4. Test deployment:**

```bash
# Test using agentkit CLI
agentkit run "Analyze this video: https://example.com/video.mp4"
```

### Advanced Deployment Options

**Custom Docker build:**

```bash
# Build image locally
docker build -t video-breakdown-agent:latest .

# Run container
docker run -p 8000:8000 \
  -e MODEL_AGENT_API_KEY=your_key \
  -e VOLCENGINE_ACCESS_KEY=your_ak \
  -e VOLCENGINE_SECRET_KEY=your_sk \
  video-breakdown-agent:latest
```

**Deployment script:**

```bash
# Use built-in deployment script
./deploy.sh
```

For detailed deployment instructions, see [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md).

## Key Features

### 1. Multi-Agent Architecture

- **Root Agent**: Main orchestrator, responsible for understanding user intent and dispatching sub-agents
- **Breakdown Agent**: Video preprocessing + vision analysis + BGM analysis
- **Hook Analyzer Agent**: SequentialAgent (vision scoring → JSON formatting)
- **Report Generator Agent**: Markdown report generation
- **Search Agent**: Real-time web search

### 2. Powerful Vision Analysis

- LiteLLM unified routing supporting multiple vision models:
  - Volcengine Doubao Vision
  - Google Gemini 2.5 Pro
  - OpenAI GPT-4o
- Switch models with one line of configuration, no code changes required

### 3. Graceful Degradation

- **TOS upload failure**: Automatically falls back to base64 encoding
- **ASR not configured**: Automatically skips speech recognition
- **Vision analysis failure**: Attempts model fallback
- **Hook analysis failure**: Still generates basic scene reports

### 4. Production-Ready

- Complete error handling and logging
- OpenTelemetry observability support (APMPlus/CozeLoop/TLS)
- Docker containerization
- AgentKit one-click deployment

## Sample Prompts

**Basic scene segmentation:**
```
Analyze the scene structure of this video
```

**Hook analysis:**
```
Analyze the hook effectiveness of the first 3 seconds of this video and provide professional scoring
```

**Complete analysis:**
```
Generate a complete video analysis report
```

**Search information:**
```
What are the latest Douyin recommendation algorithm rules?
```

## Usage Showcase

The following is a complete usage case, demonstrating the entire process from web search to in-depth video breakdown and analysis.

### 1. Web Search: Context Gathering
**User**: Check the weather in Hangzhou.

**XiaoShi**: Based on search results, here is the current weather and forecast for Hangzhou:

📍 **Hangzhou Weather (Wednesday, Feb 11, 2026)**
**Current Conditions**
- Temperature: 13°C (Current), Range 5~15°C
- Weather: Sunny
- Wind: North force 4 (Turning west in the afternoon)
- Humidity: 36%
- Air Quality: AQI 64 (Good), Primary pollutant PM2.5

📅 **3-Day Forecast**
| Date | Weather | Temp Range | Wind |
| :--- | :--- | :--- | :--- |
| Feb 11 (Wed) | Sunny → Sunny | 5~15°C | North to West, 2-4 |
| Feb 12 (Thu) | Sunny → Sunny | 6~16°C | Southeast, 2 |
| Feb 13 (Fri) | Cloudy | 8~20°C | South, 2 |

🌡️ **Life Index Reference**
- Car Wash: Suitable today (No rain for the next two days)
- Exercise: Not suitable for strenuous exercise today (Low pressure), suitable tomorrow
- UV: Weak (Basic sun protection recommended)

If you need more detailed hourly forecasts or long-term trends, just let me know!

---

### 2. Video Breakdown: Scene Analysis
**User**: Breakdown the scene structure of this video http://sns-video-hs.xhscdn.com/stream/1/110/259/01e85cee721721eb0103700397ab071344_259.mp4

**XiaoShi**: Sure, breaking down the video scenes for you...

#### Video Scene Breakdown Results
**Video Info**
- Duration: 17.07s
- Resolution: 720x960
- Frame Rate: 60fps

**Scene List**
| No. | Time | Shot | Camera | Visual Description | Audio | Tag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 0.0-3.0s | Close-up | Static | Holding a beige Lock & Lock water bottle, showing the handle. | None | Product |
| 2 | 3.0-5.0s | Close-up | Static | Opening the lid, pouring water; background shows a calendar. | None | Product |
| 3 | 5.0-10.0s | Medium | Static | Holding the filled bottle; home-style background. | None | Product |
| 4 | 10.0-17.07s | Medium | Static | Showing different bottle styles in the same setting. | None | Product |

**BGM Analysis**
- BGM Detected: Yes
- Style: Light music (Ambient), Tags: Soothing, Healing, Minimalist
- Mood: Relaxed & Pleasant, Moderate intensity
- Instruments: Piano (Lead), Violin, Synth, Soft percussion
- Tempo: 60-80 BPM (Slow), Steady 4/4 beat

**Full Transcription**
- No speech content detected (ASR skipped)

---

### 3. Hook Analysis: Effectiveness Scoring
**User**: Analyze the hook effectiveness of the first 3 seconds and provide professional scoring.

**XiaoShi**: Received. Analyzing the first three seconds in depth...

#### First 3-Second Hook Analysis
**Core Element Breakdown**
- **Visual Hook (0-3s)**
  - Shot & Camera: Close-up + Static, focusing on the core selling point (lid handle design).
  - Content: 0-1.5s shows the overall scene, 1.5-3s reinforces portability through the "hold-lift" action.
  - Visual Impact: Manicure details add refinement, beige color fits home style.
- **Audio Hook (0-3s)**
  - BGM: Soothing piano + violin, creating a relaxed atmosphere.
  - Speech: None, avoiding interference, relying on visual cues.
- **Content Hook (0-3s)**
  - Info Density: Completes the "Appearance → Function" loop within 3s.
  - Pain Point: Implies "Easy opening, portability," targeting the need for convenience.

**Effectiveness Rating**
| Dimension | Score (1-10) | Analysis |
| :--- | :--- | :--- |
| Visual Appeal | 8.5 | Close-up focuses on product, coherent action, clean background. |
| Info Efficiency | 9.0 | Rapidly conveys "What it is → How to use," fitting short-video habits. |
| Emotional Impact | 7.5 | BGM is soothing but lack a strong memory point. |
| Conversion Guide | 8.0 | Action implies value, but key selling points (e.g., material) could be clearer. |

**Optimization Suggestions**
- Visual: Add a "Leak-proof test" close-up (e.g., inverting the bottle) to strengthen the USP.
- Audio: Add a crisp sound effect for the lid opening (sync with action).
- Content: Overlay text labels like "One-touch open · Leak-proof design".

---

### 4. Insight Report: One-Click Generation
**User**: Generate a complete video analysis report.

**XiaoShi**: All analysis data has been integrated. Here is your detailed insight report:

#### Lock & Lock Product Showcase Insight Report
**I. Basic Info**
- Type: E-commerce product showcase
- Duration: 17.07s | Resolution: 720x960

**II. Content Structure**
Follows a "General → Detail → Scene → Extension" logic, forming a complete cognitive chain across 4 scenes.

**III. Audience Attention**
- High Attention: 0-5s (Clear visual focus).
- Drop-off Risk: 10-17s (Product switch lack transition).

**IV. Visual & Audio Strategy**
- Visual: Tone fits home positioning, dynamic camera movement suggested.
- Audio: Soothing vibe, suggested to add action-synced sound effects.

**V. Conversion Potential**
- Strengths: Fits the "Golden 3 Seconds" rule, multiple products cover wide needs.
- Weaknesses: Core differentiation (e.g., material safety) is under-represented.

**VI. Competitor Insights**
Could strengthen the "Manicure-friendly" design to target female users precisely.

**VII. Summary & Optimization**
Suggest adding "Pain point → Solution" logic and key selling point voiceovers.

## Demo

## FAQ

**Q1: Does FFmpeg need to be installed manually?**

A: No. This project uses `imageio-ffmpeg` which automatically downloads and packages FFmpeg binaries. If you have system FFmpeg installed, it will be used preferentially.

**Q2: Does the system support platforms like Douyin/Xiaohongshu/Bilibili links?**

A: Currently only public HTTP/HTTPS video download links are supported. Platform-specific links need to be extracted to download URLs first.

**Q3: What should I do if TOS upload fails?**

A: The system will automatically fall back to base64 encoding to continue analysis. Check:
- Whether `VOLCENGINE_ACCESS_KEY` and `VOLCENGINE_SECRET_KEY` are correctly configured
- Whether TOS bucket permissions are correct (recommend public read or pre-signed URLs)

**Q4: What should I do if vision analysis fails?**

A: Check:
- Whether `MODEL_AGENT_API_KEY` is correctly configured
- Whether the vision model name is correct (must include date suffix, e.g., `doubao-seed-1-6-vision-250815`)
- Whether network can access the model endpoint

**Q5: What should I do if ASR speech recognition fails?**

A: ASR is optional. The system will automatically skip speech recognition and continue with vision analysis if not configured. To enable ASR, configure:
```bash
ASR_APP_ID=your_app_id
ASR_ACCESS_KEY=your_access_key
```

**Q6: How to switch vision models?**

A: Modify environment variable `MODEL_VISION_NAME`:

```bash
# Use Doubao (default)
MODEL_VISION_NAME=doubao-seed-1-6-vision-250815

# Use Gemini
MODEL_VISION_NAME=gemini/gemini-2.5-pro
GEMINI_API_KEY=your_gemini_api_key

# Use GPT-4o
MODEL_VISION_NAME=gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

**Q7: Are there any limits on video duration?**

A: Recommended:
- Video duration: 15 seconds to 3 minutes
- File size: <100MB
- Resolution: 720p or 1080p

Longer videos will require more processing time and model tokens.

## References

- [VeADK Documentation](https://volcengine.github.io/veadk-python/)
- [AgentKit Documentation](https://www.volcengine.com/docs/6459)
- [Volcengine Ark Platform](https://console.volcengine.com/ark)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## Contributing

Contributions are welcome! Please refer to [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
