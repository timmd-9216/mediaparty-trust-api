# Diggity: a tool for checking the quality of journalistic content 

**An intelligent journalism quality analysis system that combines NLP with LLM-powered metrics to evaluate article credibility and objectivity.**

Built for the [2025 MediaParty Hackathon](https://docs.google.com/presentation/d/1vU38j0-vZcb5TrZEJ-d_1gVM2oLHOujc/edit?usp=sharing&ouid=104445841918104065705&rtpof=true&sd=true) | [Video Demo](https://drive.google.com/file/d/1nKPmSiT8_sjRimqFFCisDHxc1hx3ge67/view?usp=sharing) | (Hackdash)[https://hackdash.org/projects/68dd4b82f23e470f557fa1e2]

Powered by [Trust: NLP news and text analyzer](https://github.com/timmd-9216/trust)

🎉 Won first prize at MediaParty Hackathon 2025 🏆 : [https://mediaparty.org/hackaton-2025](https://mediaparty.org/hackaton-2025) sponsored by The World Bank, Internet Society, Fundación Avina and FUNDAR.

---

## 🎯 What is MediaParty Trust API?

MediaParty Trust API is a complete journalism quality assessment platform consisting of:

1. **REST API**: Backend service that analyzes articles using NLP and LLM techniques
2. **Chrome Extension**: Browser plugin that automatically scrapes, analyzes, and annotates articles in real-time
3. **Prompt Tester App**: Web interface for developing and testing prompts

The system evaluates articles across **6 dimensions**:
- **Linguistic Quality**: Sentence complexity, word count, writing style
- **Objectivity Markers**: LLM-filtered qualitative adjectives that reveal bias
- **Journalistic Standards**: Verb tense analysis for proper news reporting
- **Title-Content Relation**: Whether the headline accurately reflects the content
- **Signature Transparency**: Presence of author, editor, and media group information
- **Web Scraping**: Automatic extraction of article metadata from URLs

### 🌐 Chrome Extension

The included Chrome extension transforms how you consume news:
- **Auto-Detection**: Automatically identifies when you're reading a news article on supported sites (e.g., Infobae, Clarín, Perfil)
- **One-Click Analysis**: Click the extension icon to instantly analyze the current article
- **In-Page Annotations**: Displays quality indicators and metric scores directly on the article page
- **Visual Feedback**: Color-coded badges (🟢 good, 🟡 moderate, 🔴 poor) for quick assessment
- **No Manual Copy-Paste**: Seamlessly integrates with your reading workflow

### 🧪 Prompt Tester App

A Next.js-based web interface for developers to iterate on prompts:
- **URL Scraping**: Enter any news URL to automatically extract article content
- **Manual Input**: Paste article text directly for analysis
- **Real-time Metrics**: See all 6 metrics with detailed explanations
- **Auto-Analysis**: Automatically runs analysis after successful scrape
- **Perfect for Development**: Test prompt changes without touching the Chrome extension

**Run the Prompt Tester:**
```bash
cd prompt-tester-app
npm install
npm run dev
```
Then open http://localhost:3000

### 🔬 How It Works

1. **Article Ingestion**: Submit via URL scraping, REST API, Chrome extension, or Prompt Tester
2. **Web Scraping**: BeautifulSoup extracts article metadata (title, body, author, editor, media group)
3. **NLP Processing**: Stanza performs linguistic analysis (POS tagging, dependency parsing, verb tense detection)
4. **LLM Enhancement**: OpenRouter + DSPy filters subjective language patterns
5. **Metric Calculation**: **6 core metrics** evaluate article quality
6. **Visual Feedback**: Chrome extension or Prompt Tester displays quality indicators

### 🎨 Use Cases

- **Fact-checkers**: Identify potentially biased language in articles
- **Journalists**: Self-audit writing for objectivity
- **Media Literacy**: Teach critical reading skills with objective metrics
- **Research**: Analyze large corpora for language patterns

---

## ✨ Features

- **6 Comprehensive Metrics**: Adjectives, Word Count, Sentence Complexity, Verb Tense, Title-Content Relation, and Signature Transparency
- **LLM-Powered Analysis**: Uses OpenRouter + DSPy for qualitative adjective filtering and content evaluation
- **Web Scraping**: Automatic extraction of article metadata from URLs (title, body, author, editor, media group)
- **NLP Foundation**: Stanford Stanza for robust Spanish language processing (POS tagging, dependency parsing, verb tense analysis)
- **Multiple Interfaces**: REST API, Chrome Extension, and Prompt Tester web app
- **Failover Architecture**: Graceful degradation when LLM or NLP services are unavailable
- **Comprehensive Logging**: Track API calls, scraper operations, and metric calculations

---

## 📋 Requirements

- Python 3.12+
- Node.js 18+ (for Prompt Tester App)
- OpenRouter API Key (optional, for LLM-powered metrics)
- `transformers` and `torch` (for Stanza NLP - installed automatically)

---

## 🚀 Installation

### API Backend

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Additional dependencies for NLP
pip install transformers torch beautifulsoup4
```

**Note**: If using `uv`, see [SETUP.md](SETUP.md) for known issues on macOS ARM64.

### Prompt Tester App

```bash
cd prompt-tester-app
npm install
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# OpenRouter API Configuration (optional but recommended)
OPENROUTER_API_KEY=your_api_key_here

# Optional: Site information for OpenRouter
SITE_URL=https://your-site.com
SITE_NAME=MediaParty Trust API
```

### Getting an OpenRouter API Key

1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Go to [API Keys](https://openrouter.ai/keys)
3. Create a new API key
4. Copy the key to your `.env` file

**Note**: Without `OPENROUTER_API_KEY`, metrics will work with fallback heuristics (no LLM filtering).

---

## 🎮 Usage

### Starting the API

```bash
# Option 1: Using the script
./run_api.sh

# Option 2: Direct command
source .venv/bin/activate && uvicorn mediaparty_trust_api.main:app --reload
```

The API will be available at `http://localhost:8000`

### Starting the Prompt Tester

```bash
cd prompt-tester-app
npm run dev
```

The Prompt Tester will be available at `http://localhost:3000`

**Note**: Ensure the API is running on port 8000 before using the Prompt Tester.

### API Documentation

Interactive docs at: `http://localhost:8000/docs`

### Test Client

```bash
# Run with default example
python test_api.py

# Use a specific file
python test_api.py --input test/input_example.json

# Specify output file
python test_api.py --input test/input_example.json --output result.json
```

---

## 📁 Project Structure

```
mediaparty-trust-api/
├── src/mediaparty_trust_api/
│   ├── main.py                  # FastAPI entry point
│   ├── models.py                # Pydantic models
│   ├── api/v1/
│   │   └── endpoints.py         # API endpoints (scrape + analyze)
│   └── services/
│       ├── metrics.py           # 6 analysis metrics
│       ├── scraper.py           # Web scraping service
│       ├── stanza_service.py    # NLP processing
│       └── prompt_loader.py     # Prompt management
├── prompts/                     # DSPy prompt definitions
│   ├── prompt-adjectives.json
│   ├── prompt-signatures.json
│   ├── prompt-verb-tense.json
│   └── ...
├── prompt-tester-app/           # Next.js web interface
│   ├── app/
│   │   ├── components/          # UI components
│   │   └── page.tsx             # Main interface
│   └── README.md
├── chrome-extension/
│   └── extension/               # Browser extension
├── test/
│   ├── input.json               # Input template
│   ├── input_example.json       # Basic example
│   └── input_example_espert.json # Real article example
├── test_api.py                  # Test client
├── run_api.sh                   # API startup script
├── .env.example                 # Config template
└── README.md                    # This file
```

---

## 🔌 API Endpoints

### GET /api/v1/scrape

Scrapes a news article from a URL and extracts metadata.

**Query Parameters:**
- `url` (required): The news article URL to scrape

**Response:**
```json
{
    "title": "Article Headline",
    "body": "Full article content...",
    "author": "Author Name",
    "editor": "Editor Name",
    "media_group": "Media Group/Publisher",
    "url": "https://example.com/article"
}
```

### POST /api/v1/analyze

Analyzes a journalistic article and returns trust metrics.

**Request Body:**
```json
{
    "body": "Article text...",
    "title": "Article title",
    "author": "Author name",
    "link": "https://example.com/article",
    "date": "2024-03-15",
    "media_type": "article",
    "editor": "Editor name (optional)",
    "media_group": "Media group (optional)"
}
```

**Response:**
```json
[
    {
        "id": 0,
        "criteria_name": "Qualitative Adjectives",
        "explanation": "The qualitative adjective ratio (3.2%) is excellent, indicating objective writing.",
        "flag": 1,
        "score": 0.9
    },
    {
        "id": 1,
        "criteria_name": "Word Count",
        "explanation": "The article has 450 words, indicating adequate coverage.",
        "flag": 0,
        "score": 0.6
    },
    {
        "id": 5,
        "criteria_name": "Signature Transparency",
        "explanation": "Full name author (John Doe), no editor, has media group (Example Media)",
        "flag": 0,
        "score": 0.6
    }
]
```

---

## 📊 Implemented Metrics

### 1. Qualitative Adjectives (LLM-Enhanced + NLP)
- Uses Stanza POS tagging to identify adjectives
- Filters qualitative (opinion) vs descriptive (objective) using OpenRouter + DSPy
- **Thresholds**: ≤5% excellent, ≤10% moderate, >10% high
- **Why it matters**: Excessive qualitative adjectives signal bias or sensationalism

### 2. Word Count (NLP)
- Uses Stanza tokenization for accurate word counting
- Accounts for Spanish language specifics (contractions, multi-word tokens)
- **Why it matters**: Depth of coverage correlates with research quality

### 3. Sentence Complexity (NLP)
- Analyzes average sentence length using dependency parsing
- Optimal range: 15-25 words per sentence
- **Why it matters**: Proper complexity ensures readability without oversimplification

### 4. Verb Tense Analysis (NLP)
- Uses Stanza to detect verb tense features (`Tense=Past/Pres/Fut`)
- News articles: 40-70% past tense verbs expected
- **Why it matters**: Proper tense usage indicates professional news reporting style

### 5. Title-Content Relation (LLM)
- Evaluates whether headline accurately reflects article content
- Classifies as: COINCIDE, CONTRADICE, or EXAGERA
- **Why it matters**: Clickbait and misleading headlines damage credibility

### 6. Signature Transparency (LLM + Scraping)
- Evaluates presence of accountability information
- **Signature Type**: FULL_NAME, INITIALS, or NONE
- **Editor**: Presence of editor/director responsible
- **Media Group**: Presence of publisher information
- **Why it matters**: Transparency in authorship and ownership is fundamental to journalistic credibility

---

## 🚢 Deployment to Google Cloud Run

This project includes automated deployment to Google Cloud Run using GitHub Actions.

### Prerequisites

1. **Google Cloud Project**
   - Create a GCP project at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable the following APIs:
     - Cloud Run API
     - Artifact Registry API
     - Cloud Build API

2. **Service Account**
   - Create a service account with the following roles:
     - Cloud Run Admin
     - Storage Admin
     - Artifact Registry Administrator
   - Download the JSON key file

3. **Artifact Registry Repository**
   ```bash
   gcloud artifacts repositories create cloud-run-source-deploy \
     --repository-format=docker \
     --location=us-central1 \
     --description="Docker repository for Cloud Run"
   ```

### Setup GitHub Secrets

Add the following secrets to your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_REGION`: Deployment region (e.g., `us-central1`)
- `GCP_SERVICE_NAME`: Service name (e.g., `mediaparty-trust-api`)
- `GCP_SA_KEY`: Base64-encoded service account JSON key
- `OPENROUTER_API_KEY`: Your OpenRouter API key

To encode the service account key:
```bash
cat service-account-key.json | base64
```

### Deployment

The deployment happens automatically:

1. **Automatic**: Push to the `main` branch triggers deployment
2. **Manual**: Go to `Actions` → `Deploy to Cloud Run` → `Run workflow`

The workflow will:
1. Build a Docker container
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Test the deployment

### Access Your Deployment

After successful deployment, your API will be available at:
```
https://[SERVICE-NAME]-[RANDOM-HASH]-[REGION].a.run.app
```

Check the deployment logs in GitHub Actions for the exact URL.

### Local Docker Testing

Test the Docker container locally before deploying:

```bash
# Build the image
docker build -t mediaparty-trust-api .

# Run the container
docker run -p 8080:8080 \
  -e OPENROUTER_API_KEY=your_key_here \
  mediaparty-trust-api

# Test the endpoint
curl http://localhost:8080/health
```

### Configuration

The Cloud Run service is configured with:
- **Memory**: 2GB
- **CPU**: 2 vCPU
- **Timeout**: 300 seconds
- **Max instances**: 10
- **Min instances**: 0 (scales to zero)
- **Port**: 8080

Adjust these in [.github/workflows/deploy-cloud-run.yml](.github/workflows/deploy-cloud-run.yml) as needed.

---

## 🛠️ Development

### Adding New Metrics

Edit `src/mediaparty_trust_api/services/metrics.py`:

```python
def get_new_metric(doc: Document, metric_id: int) -> Metric:
    """Your new metric."""
    # Implementation
    return Metric(...)
```

### Testing

```bash
# Run tests (coming soon)
pytest
```

---

## 🐛 Troubleshooting

### Error: uv sync fails on macOS ARM64

See [SETUP.md](SETUP.md) for the complete solution. Summary: use `pip` instead of `uv`.

### Error: OPENROUTER_API_KEY not set

The API will work without LLM-based adjective filtering. To enable full functionality, configure the API key in `.env`.

### Error: Stanza models not found

Stanza downloads models on first run. Ensure you have an internet connection.

### Error: `transformers` not defined

Install the required dependencies:
```bash
pip install transformers torch
```

Then restart the API.

### Error: Scraper returns null fields

Some websites have anti-bot protection. The scraper uses:
- Modern browser headers
- Session cookies
- Encoding detection

If extraction fails, try the manual input option in the Prompt Tester.

---

## 🤝 Contributing

This project was built by a diverse team of journalists, developers, students, and designers who came together at the MediaParty Hackathon with a shared vision: to bring transparency and objectivity to news consumption.

We believe the best solutions emerge when different perspectives collaborate. Whether you're:
- 📰 **A journalist** who understands editorial quality
- 💻 **A developer** passionate about NLP and AI
- 🎓 **A student** eager to learn and contribute
- 🎨 **A designer** focused on user experience
- 🔬 **A researcher** interested in media analysis

...your contributions are welcome! We value diverse viewpoints and skill sets.

### How to Contribute

- **Report Issues**: Found a bug or have a feature idea? [Open an issue](../../issues)
- **Submit PRs**: Code improvements, new metrics, or documentation updates
- **Share Feedback**: Help us understand how journalists use the tool
- **Spread the Word**: Star the repo and share with others interested in media quality

---

## 📄 License

[LICENSE](LICENSE)

---

## 🏆 Acknowledgments

Developed for the MediaParty Hackathon. Built with [Trust](https://github.com/timmd-9216/trust), FastAPI, Stanza, DSPy, and OpenRouter.
