SmartScrape
What This Is
SmartScrape is a private, personal desktop application that acts as a self-curated digital newspaper and long-term knowledge archive. It automatically pulls content from Reddit, Telegram channels, and RSS feeds on topics the user follows (football/Real Madrid, history, classic rock), removes duplicate/overlapping stories using semantic similarity, and generates clean AI-synthesized summaries. Beyond news consumption, it doubles as a "Knowledge Vault" — a searchable personal database where the user can permanently save timeless facts they encounter, separate from the transient news feed.
This is a real, daily-use application being built by the developer for their own long-term use — not a portfolio demo or throwaway exercise.
Why This Project Exists
The developer is a backend-focused CS student (Node.js/Express, PostgreSQL/Supabase background) intentionally using this project to force three new skill areas through real, load-bearing code rather than isolated tutorials:

Python — new language for this developer
Desktop application development — new paradigm, distinct from their web-only background
Docker + automated testing (pytest) — existing skill gaps in their current stack

The project's scope and feature set were chosen specifically because they require these skills to function, not because the features were designed first.
Core Goals

Aggregate content from multiple source types (Reddit, Telegram, RSS) into one unified feed
Deduplicate overlapping stories across sources using embedding-based similarity, not just exact text matching
Synthesize raw source material into clean, readable summaries using an LLM (Groq API)
Allow the user to save specific facts/insights into a persistent, full-text-searchable Knowledge Vault (SQLite + FTS5), independent of the news feed's lifecycle
Produce a genuinely usable daily-driver application, not a technical demo

Explicit Non-Goals

Twitter/X and Facebook are intentionally excluded. Their current APIs do not support this use case without paid tier access. The architecture leaves room to add them later if paid access is ever obtained, but nothing is being built against them now, and no code should assume their eventual inclusion.

Architecture
The application is split into two independent parts communicating over localhost HTTP:

Desktop Client (PyQt) — The GUI. Handles all user interaction, rendering, and the Qt event loop. Contains no scraping, deduplication, or synthesis logic itself — it calls the backend service and displays results.
Backend Service (FastAPI, headless) — Contains all actual logic: fetching from Reddit/Telegram/RSS, deduplication via embedding similarity, summary synthesis via Groq, and Knowledge Vault storage/search. Runs as a separate local process. This is the part that gets Dockerized and covered by pytest, since GUI applications do not containerize or test well in isolation.

This separation exists specifically so the backend logic is testable, containerizable, and swappable (a different frontend could replace PyQt later) without needing to test or containerize the GUI itself.
Data Flow (high level)
Reddit API ─┐
Telegram    ├──► FastAPI backend ──► embedding-based dedup ──► Groq synthesis ──► PyQt client displays feed
RSS feeds ──┘                                                        │
                                                                      ▼
                                                          User saves fact ──► SQLite Knowledge Vault (FTS5)
Tech Stack

Frontend: PyQt (desktop GUI)
Backend: FastAPI (Python), running as a local headless service
Data sources: Reddit API, Telegram via MTProto (not Bot API — required for reading channels not owned by the user), RSS feeds
Deduplication: Local embedding model (e.g. sentence-transformers) for semantic similarity — Groq does not provide an embeddings endpoint, so this is handled separately from summary generation
Synthesis: Groq API (LLM inference) for turning raw/duplicate source material into a single clean summary
Storage: SQLite with FTS5 for full-text search over the Knowledge Vault
Testing: pytest, targeting the FastAPI backend
Deployment: Docker, for the FastAPI backend only (not the GUI)

Development Roles
This project is built through a specific division of labor between the developer and their AI collaborators:

Backend/logic code (FastAPI service: fetching, deduplication, synthesis orchestration, Vault storage/search) is written by the developer, with architectural guidance. This is the code the developer is actively learning from and must understand deeply.
Frontend/GUI code (PyQt client) is generated directly by an AI coding agent (Codex), based on architecture and behavior specified collaboratively. The developer is not aiming to deeply learn PyQt syntax at this stage — the priority is a functional, correct GUI shell that the backend can plug into safely (particularly around threading, since PyQt's event loop must never be blocked by network calls to the backend).
Architecture and sequencing decisions (what gets built when, what concept must be understood before which piece of code, catching design mistakes before they compound) are made collaboratively before implementation, one step at a time — not planned exhaustively upfront and not discovered by trial and error mid-build.

Expected Result
A working desktop application that:

Opens to a feed of deduplicated, AI-summarized stories from the user's chosen sources and topics
Lets the user browse this feed daily as a replacement for manually checking multiple platforms
Lets the user save any fact or insight into a permanent, searchable personal knowledge base
Runs its logic layer inside Docker, backed by a pytest test suite
Is actively used by the developer after completion, not archived as a finished exercise

Status
In active development. Being built incrementally over an approximate 8-day plan (subject to change), covering: PyQt shell → Reddit/RSS integration → Telegram integration → deduplication/synthesis engine → Knowledge Vault → FastAPI/Docker service split → pytest coverage → polish and packaging.
