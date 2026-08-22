import React, { useState, useEffect } from "react"
import {
  VideoIcon,
  PlayIcon,
  UploadIcon,
  CheckCircle2Icon,
  ClockIcon,
  SparklesIcon,
  RefreshCwIcon,
  EyeIcon,
  FilmIcon,
  Volume2Icon,
  FileTextIcon,
  ServerIcon,
  LayersIcon,
  PlusIcon,
  Loader2Icon,
  TerminalIcon,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogFooter,
} from "@/components/ui/dialog"

interface RunInfo {
  run_id: string
  topic: string
  status: string
  has_final_mp4: boolean
  has_plan: boolean
  created_at?: number
  completed_at?: string
  errors?: string[]
}

interface HealthStatus {
  status: string
  env: {
    openrouter_configured: boolean
    openrouter_model: string
    kie_configured: boolean
    youtube_auth_configured: boolean
  }
}

interface RunDetail {
  run_id: string
  run_dir: string
  run_data: any
  plan_data: any
  assets: {
    final_mp4: string | null
    raw_video: string | null
    narration_mp3: string | null
    captions_srt: string | null
  }
  quality_gate: {
    passed: boolean
    error: string | null
  }
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [runs, setRuns] = useState<RunInfo[]>([])
  const [loadingRuns, setLoadingRuns] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<"create" | "runs" | "health">("create")

  // Create Run Form State
  const [topic, setTopic] = useState("")
  const [modelName, setModelName] = useState("google/gemini-2.5-flash")
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [pipelineLogs, setPipelineLogs] = useState<Array<{ stage: string; message: string; status: string }>>([])
  const [pipelineStage, setPipelineStage] = useState<string>("idle")
  const [progressPercent, setProgressPercent] = useState<number>(0)

  // Run Detail Modal State
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailTab, setDetailTab] = useState<"video" | "audio" | "plan" | "quality" | "upload">("video")
  const [editingPlanJson, setEditingPlanJson] = useState("")
  const [savingPlan, setSavingPlan] = useState(false)
  const [uploadPrivacy, setUploadPrivacy] = useState<"public" | "private">("private")
  const [isUploading, setIsUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  // Fetch Health & Runs
  const fetchHealth = async () => {
    try {
      const res = await fetch("/api/health")
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch (e) {
      console.error("Failed to fetch health", e)
    }
  }

  const fetchRuns = async () => {
    setLoadingRuns(true)
    try {
      const res = await fetch("/api/runs")
      if (res.ok) {
        const data = await res.json()
        setRuns(data)
      }
    } catch (e) {
      console.error("Failed to fetch runs", e)
    } finally {
      setLoadingRuns(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    fetchRuns()
  }, [])

  // Start Generation
  const handleStartGeneration = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return

    setIsGenerating(true)
    setPipelineLogs([])
    setPipelineStage("init")
    setProgressPercent(5)

    try {
      const res = await fetch("/api/runs/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, model_name: modelName }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Failed to start pipeline")
      }

      const data = await res.json()
      setActiveRunId(data.run_id)
      subscribeToStream(data.run_id)
    } catch (err: any) {
      alert(`Error starting pipeline: ${err.message}`)
      setIsGenerating(false)
    }
  }

  // Subscribe to SSE stream
  const subscribeToStream = (runId: string) => {
    const eventSource = new EventSource(`/api/runs/${runId}/stream`)

    eventSource.addEventListener("progress", (event: MessageEvent) => {
      const data = JSON.parse(event.data)
      setPipelineLogs((prev) => [...prev, data])
      setPipelineStage(data.stage)

      // Calculate progress percentage
      switch (data.stage) {
        case "init":
          setProgressPercent(10)
          break
        case "plan":
          setProgressPercent(25)
          break
        case "plan_complete":
          setProgressPercent(40)
          break
        case "ai_video":
          setProgressPercent(55)
          break
        case "ai_video_complete":
          setProgressPercent(70)
          break
        case "tts":
          setProgressPercent(80)
          break
        case "ffmpeg":
          setProgressPercent(90)
          break
        case "quality":
          setProgressPercent(95)
          break
        case "done":
          setProgressPercent(100)
          setIsGenerating(false)
          eventSource.close()
          fetchRuns()
          break
        case "failed":
          setIsGenerating(false)
          eventSource.close()
          fetchRuns()
          break
      }
    })

    eventSource.onerror = () => {
      eventSource.close()
    }
  }

  // Inspect Run
  const handleInspectRun = async (runId: string) => {
    setSelectedRunId(runId)
    setLoadingDetail(true)
    setUploadMessage(null)
    try {
      const res = await fetch(`/api/runs/${runId}`)
      if (res.ok) {
        const data = await res.json()
        setRunDetail(data)
        setEditingPlanJson(JSON.stringify(data.plan_data || {}, null, 2))
      }
    } catch (e) {
      console.error("Failed to load run detail", e)
    } finally {
      setLoadingDetail(false)
    }
  }

  // Save Plan JSON
  const handleSavePlan = async () => {
    if (!selectedRunId) return
    setSavingPlan(true)
    try {
      const parsed = JSON.parse(editingPlanJson)
      const res = await fetch(`/api/runs/${selectedRunId}/plan`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_data: parsed }),
      })
      if (res.ok) {
        alert("plan.json saved successfully!")
        handleInspectRun(selectedRunId)
      } else {
        const err = await res.json()
        alert(`Failed to save plan: ${err.detail}`)
      }
    } catch (err: any) {
      alert(`Invalid JSON format: ${err.message}`)
    } finally {
      setSavingPlan(false)
    }
  }

  // Upload to YouTube
  const handleUploadToYouTube = async () => {
    if (!selectedRunId) return
    setIsUploading(true)
    setUploadMessage(null)
    try {
      const res = await fetch(`/api/runs/${selectedRunId}/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ publish: uploadPrivacy === "public" }),
      })

      const data = await res.json()
      if (res.ok) {
        setUploadMessage({ type: "success", text: data.message || "Video successfully uploaded to YouTube!" })
        fetchRuns()
      } else {
        setUploadMessage({ type: "error", text: data.detail || "Upload failed." })
      }
    } catch (e: any) {
      setUploadMessage({ type: "error", text: e.message || "Failed to reach backend." })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* 2D Flat Header Bar */}
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-md bg-blue-600 border border-blue-500 flex items-center justify-center font-bold text-white shadow-none">
            <VideoIcon className="size-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              YouTube Agent Studio
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">2D Web UI</Badge>
            </h1>
            <p className="text-xs text-slate-400">Autonomous Grok AI Video & Voiceover Pipeline</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1.5">
          <Button
            variant={activeTab === "create" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("create")}
          >
            <PlusIcon className="size-4" data-icon="inline-start" />
            Create Video
          </Button>
          <Button
            variant={activeTab === "runs" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("runs")}
          >
            <LayersIcon className="size-4" data-icon="inline-start" />
            Runs Library ({runs.length})
          </Button>
          <Button
            variant={activeTab === "health" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("health")}
          >
            <ServerIcon className="size-4" data-icon="inline-start" />
            System Status
          </Button>
        </nav>

        {/* Status Indicators */}
        <div className="flex items-center gap-2 text-xs">
          {health ? (
            <Badge variant={health.env.openrouter_configured && health.env.kie_configured ? "success" : "warning"}>
              <CheckCircle2Icon className="size-3" data-icon="inline-start" />
              API Ready
            </Badge>
          ) : (
            <Badge variant="destructive">Connecting...</Badge>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto flex flex-col gap-6">
        {/* VIEW 1: CREATE VIDEO STUDIO */}
        {activeTab === "create" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Input Form Column */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <SparklesIcon className="size-5 text-blue-400" />
                    New Video Generation
                  </CardTitle>
                  <CardDescription>
                    Enter a topic prompt to trigger AI scriptwriting, Grok Imagine video generation, and TTS audio assembly.
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <form onSubmit={handleStartGeneration} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="topic" className="text-xs font-semibold text-slate-300">
                        Video Topic / Script Prompt
                      </label>
                      <Textarea
                        id="topic"
                        rows={4}
                        placeholder="e.g. How an API request works under the hood in 30 seconds"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        required
                        disabled={isGenerating}
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label htmlFor="model" className="text-xs font-semibold text-slate-300">
                        OpenRouter LLM Model
                      </label>
                      <Input
                        id="model"
                        value={modelName}
                        onChange={(e) => setModelName(e.target.value)}
                        placeholder="google/gemini-2.5-flash"
                        disabled={isGenerating}
                      />
                    </div>

                    <Button
                      type="submit"
                      variant="primary"
                      className="w-full mt-2"
                      disabled={isGenerating || !topic.trim()}
                    >
                      {isGenerating ? (
                        <>
                          <Loader2Icon className="size-4 animate-spin" data-icon="inline-start" />
                          Generating Pipeline...
                        </>
                      ) : (
                        <>
                          <PlayIcon className="size-4" data-icon="inline-start" />
                          Generate Video
                        </>
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Quick Health Summary Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Engine Credentials</CardTitle>
                </CardHeader>
                <CardContent className="text-xs flex flex-col gap-2">
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-400">OpenRouter API</span>
                    {health?.env.openrouter_configured ? (
                      <Badge variant="success">Connected</Badge>
                    ) : (
                      <Badge variant="destructive">Missing</Badge>
                    )}
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-400">Grok Imagine (KIE.ai)</span>
                    {health?.env.kie_configured ? (
                      <Badge variant="success">Connected</Badge>
                    ) : (
                      <Badge variant="destructive">Missing</Badge>
                    )}
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-400">YouTube OAuth</span>
                    {health?.env.youtube_auth_configured ? (
                      <Badge variant="success">Configured</Badge>
                    ) : (
                      <Badge variant="warning">Not Auth</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Live Progress & Log Stream Column */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              <Card className="flex-1">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <TerminalIcon className="size-5 text-emerald-400" />
                      Live Pipeline Execution ({pipelineStage})
                    </span>
                    {activeRunId && (
                      <Badge variant="outline" className="font-mono text-[11px]">
                        ID: {activeRunId}
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>Real-time stage tracking and background SSE execution log.</CardDescription>
                </CardHeader>

                <CardContent className="flex flex-col gap-6">
                  {/* Progress Bar & Stage Metrics */}
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between text-xs font-semibold text-slate-300">
                      <span>Pipeline Progress</span>
                      <span>{progressPercent}%</span>
                    </div>
                    <Progress value={progressPercent} />
                  </div>

                  {/* 5 Visual Pipeline Steps */}
                  <div className="grid grid-cols-5 gap-2 text-center text-[11px]">
                    <div
                      className={`p-2 rounded border flex flex-col items-center gap-1 ${
                        progressPercent >= 25 ? "bg-blue-950/60 border-blue-600 text-blue-300" : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      <FileTextIcon className="size-4" />
                      <span>1. Scripting</span>
                    </div>

                    <div
                      className={`p-2 rounded border flex flex-col items-center gap-1 ${
                        progressPercent >= 55 ? "bg-blue-950/60 border-blue-600 text-blue-300" : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      <FilmIcon className="size-4" />
                      <span>2. AI Video</span>
                    </div>

                    <div
                      className={`p-2 rounded border flex flex-col items-center gap-1 ${
                        progressPercent >= 80 ? "bg-blue-950/60 border-blue-600 text-blue-300" : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      <Volume2Icon className="size-4" />
                      <span>3. Voiceover</span>
                    </div>

                    <div
                      className={`p-2 rounded border flex flex-col items-center gap-1 ${
                        progressPercent >= 90 ? "bg-blue-950/60 border-blue-600 text-blue-300" : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      <LayersIcon className="size-4" />
                      <span>4. FFmpeg</span>
                    </div>

                    <div
                      className={`p-2 rounded border flex flex-col items-center gap-1 ${
                        progressPercent >= 100 ? "bg-emerald-950/60 border-emerald-600 text-emerald-300" : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      <CheckCircle2Icon className="size-4" />
                      <span>5. Quality</span>
                    </div>
                  </div>

                  <Separator />

                  {/* Terminal Log Output */}
                  <div className="bg-slate-950 border border-slate-800 rounded-md p-4 h-64 overflow-y-auto font-mono text-xs text-slate-300 flex flex-col gap-1.5">
                    {pipelineLogs.length === 0 ? (
                      <div className="text-slate-600 italic">Logs will appear here once pipeline starts...</div>
                    ) : (
                      pipelineLogs.map((log, idx) => (
                        <div key={idx} className="flex gap-2">
                          <span className="text-blue-400">[{log.stage}]</span>
                          <span className={log.status === "failed" ? "text-red-400 font-semibold" : ""}>
                            {log.message}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* VIEW 2: HISTORICAL RUNS LIBRARY */}
        {activeTab === "runs" && (
          <div className="flex flex-col gap-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-slate-100">Video Generation Library</h2>
                <p className="text-xs text-slate-400">View, inspect, preview, and upload generated runs.</p>
              </div>

              <Button variant="outline" size="sm" onClick={fetchRuns} disabled={loadingRuns}>
                <RefreshCwIcon className={`size-4 ${loadingRuns ? "animate-spin" : ""}`} data-icon="inline-start" />
                Refresh
              </Button>
            </div>

            {loadingRuns ? (
              <div className="p-12 text-center text-slate-400">Loading historical runs...</div>
            ) : runs.length === 0 ? (
              <Card className="p-12 text-center text-slate-400 flex flex-col items-center gap-3">
                <VideoIcon className="size-10 text-slate-600" />
                <p>No video runs generated yet. Create your first video topic above!</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {runs.map((run) => (
                  <Card key={run.run_id} className="flex flex-col justify-between">
                    <CardHeader className="p-4 pb-2">
                      <div className="flex justify-between items-start gap-2">
                        <Badge
                          variant={
                            run.status === "ready_to_upload"
                              ? "success"
                              : run.status === "failed"
                              ? "destructive"
                              : "default"
                          }
                        >
                          {run.status}
                        </Badge>
                        <span className="text-[11px] font-mono text-slate-500 truncate max-w-[120px]">
                          {run.run_id}
                        </span>
                      </div>

                      <CardTitle className="text-sm line-clamp-2 mt-2" title={run.topic}>
                        {run.topic}
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="p-4 pt-0 text-xs text-slate-400 flex flex-col gap-1.5">
                      <div className="flex items-center gap-1">
                        <ClockIcon className="size-3 text-slate-500" />
                        <span>
                          {run.completed_at ? new Date(run.completed_at).toLocaleString() : "Processing"}
                        </span>
                      </div>
                    </CardContent>

                    <CardFooter className="p-4 pt-0 flex gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        className="w-full"
                        onClick={() => handleInspectRun(run.run_id)}
                      >
                        <EyeIcon className="size-4" data-icon="inline-start" />
                        Inspect & Upload
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* VIEW 3: SYSTEM HEALTH & CREDENTIALS */}
        {activeTab === "health" && (
          <div className="max-w-2xl mx-auto w-full flex flex-col gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ServerIcon className="size-5 text-blue-400" />
                  System & Service Diagnostics
                </CardTitle>
                <CardDescription>Status of local services, API keys, and environment variables.</CardDescription>
              </CardHeader>

              <CardContent className="flex flex-col gap-4">
                <div className="p-4 rounded-md border border-slate-800 bg-slate-950 flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm">OpenRouter LLM Integration</span>
                    {health?.env.openrouter_configured ? (
                      <Badge variant="success">Configured</Badge>
                    ) : (
                      <Badge variant="destructive">Missing Key</Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">
                    Default model: <code className="text-blue-300">{health?.env.openrouter_model}</code>
                  </p>
                </div>

                <div className="p-4 rounded-md border border-slate-800 bg-slate-950 flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm">Grok Imagine (KIE.ai) AI Video Generator</span>
                    {health?.env.kie_configured ? (
                      <Badge variant="success">Configured</Badge>
                    ) : (
                      <Badge variant="destructive">Missing KIE_API_KEY</Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">Provides 30s high-definition vertical text-to-video generation.</p>
                </div>

                <div className="p-4 rounded-md border border-slate-800 bg-slate-950 flex flex-col gap-3">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm">YouTube Data API v3 OAuth</span>
                    {health?.env.youtube_auth_configured ? (
                      <Badge variant="success">Ready for Upload</Badge>
                    ) : (
                      <Badge variant="warning">Missing client_secrets.json</Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">Required to publish video runs directly to YouTube.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* INSPECT RUN DETAIL MODAL */}
      <Dialog open={selectedRunId !== null} onOpenChange={(open) => !open && setSelectedRunId(null)}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-slate-100">
              <FilmIcon className="size-5 text-blue-400" />
              Run Inspector: {selectedRunId}
            </span>
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Preview generated output assets, examine subtitles, edit JSON plan, and publish to YouTube.
          </DialogDescription>
        </DialogHeader>

        <DialogContent>
          {loadingDetail ? (
            <div className="p-8 text-center text-slate-400">Loading run details...</div>
          ) : runDetail ? (
            <div className="flex flex-col gap-4">
              {/* Inner Tab Bar */}
              <div className="flex border-b border-slate-800 gap-2 pb-2">
                <Button
                  variant={detailTab === "video" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setDetailTab("video")}
                >
                  <FilmIcon className="size-4" data-icon="inline-start" />
                  Video Preview
                </Button>
                <Button
                  variant={detailTab === "audio" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setDetailTab("audio")}
                >
                  <Volume2Icon className="size-4" data-icon="inline-start" />
                  Audio & SRT
                </Button>
                <Button
                  variant={detailTab === "plan" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setDetailTab("plan")}
                >
                  <FileTextIcon className="size-4" data-icon="inline-start" />
                  Plan JSON
                </Button>
                <Button
                  variant={detailTab === "quality" ? "primary" : "ghost"}
                  size="sm"
                  onClick={() => setDetailTab("quality")}
                >
                  <CheckCircle2Icon className="size-4" data-icon="inline-start" />
                  Quality Gate
                </Button>
                <Button
                  variant={detailTab === "upload" ? "success" : "ghost"}
                  size="sm"
                  onClick={() => setDetailTab("upload")}
                >
                  <UploadIcon className="size-4" data-icon="inline-start" />
                  YouTube Upload
                </Button>
              </div>

              {/* TAB 1: VIDEO PREVIEW */}
              {detailTab === "video" && (
                <div className="flex flex-col gap-4">
                  {runDetail.assets.final_mp4 ? (
                    <div className="flex flex-col items-center gap-2">
                      <span className="text-xs text-slate-400 font-semibold">Composed Final Video (final.mp4)</span>
                      <video
                        src={runDetail.assets.final_mp4}
                        controls
                        className="max-h-80 w-auto rounded border border-slate-800 bg-black"
                      />
                    </div>
                  ) : (
                    <div className="p-8 text-center text-slate-500 border border-slate-800 rounded">
                      final.mp4 not generated yet.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: AUDIO & SRT */}
              {detailTab === "audio" && (
                <div className="flex flex-col gap-4">
                  {runDetail.assets.narration_mp3 && (
                    <div className="flex flex-col gap-2">
                      <span className="text-xs text-slate-400 font-semibold">TTS Narration Audio</span>
                      <audio src={runDetail.assets.narration_mp3} controls className="w-full" />
                    </div>
                  )}

                  {runDetail.plan_data?.voice_script && (
                    <div className="flex flex-col gap-2">
                      <span className="text-xs text-slate-400 font-semibold">Script Text</span>
                      <div className="p-3 rounded border border-slate-800 bg-slate-950 text-xs font-mono text-slate-200">
                        {runDetail.plan_data.voice_script}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: PLAN JSON EDITOR */}
              {detailTab === "plan" && (
                <div className="flex flex-col gap-3">
                  <span className="text-xs text-slate-400 font-semibold">Editable plan.json</span>
                  <Textarea
                    rows={10}
                    value={editingPlanJson}
                    onChange={(e) => setEditingPlanJson(e.target.value)}
                  />
                  <Button variant="outline" size="sm" onClick={handleSavePlan} disabled={savingPlan}>
                    {savingPlan ? "Saving..." : "Save plan.json"}
                  </Button>
                </div>
              )}

              {/* TAB 4: QUALITY GATE */}
              {detailTab === "quality" && (
                <div className="flex flex-col gap-3 p-4 rounded border border-slate-800 bg-slate-950">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold">Quality Check Gate Status</span>
                    {runDetail.quality_gate.passed ? (
                      <Badge variant="success">PASSED</Badge>
                    ) : (
                      <Badge variant="destructive">FAILED</Badge>
                    )}
                  </div>
                  {runDetail.quality_gate.error && (
                    <div className="text-xs text-red-400 font-mono p-2 rounded bg-red-950/40 border border-red-900">
                      {runDetail.quality_gate.error}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: YOUTUBE UPLOAD */}
              {detailTab === "upload" && (
                <div className="flex flex-col gap-4 p-4 rounded border border-slate-800 bg-slate-950">
                  <div className="flex flex-col gap-1">
                    <h3 className="text-sm font-bold text-slate-100">Upload Video to YouTube</h3>
                    <p className="text-xs text-slate-400">
                      Publish directly to your connected YouTube channel using official API credentials.
                    </p>
                  </div>

                  <div className="flex items-center gap-4 py-2">
                    <label className="text-xs font-semibold text-slate-300">Privacy Status:</label>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant={uploadPrivacy === "private" ? "primary" : "outline"}
                        size="sm"
                        onClick={() => setUploadPrivacy("private")}
                      >
                        Private
                      </Button>
                      <Button
                        type="button"
                        variant={uploadPrivacy === "public" ? "primary" : "outline"}
                        size="sm"
                        onClick={() => setUploadPrivacy("public")}
                      >
                        Public
                      </Button>
                    </div>
                  </div>

                  {uploadMessage && (
                    <div
                      className={`p-3 rounded text-xs border ${
                        uploadMessage.type === "success"
                          ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                          : "bg-red-950/60 border-red-800 text-red-300"
                      }`}
                    >
                      {uploadMessage.text}
                    </div>
                  )}

                  <Button
                    variant="success"
                    onClick={handleUploadToYouTube}
                    disabled={isUploading || !runDetail.quality_gate.passed}
                  >
                    {isUploading ? (
                      <>
                        <Loader2Icon className="size-4 animate-spin" data-icon="inline-start" />
                        Uploading to YouTube...
                      </>
                    ) : (
                      <>
                        <UploadIcon className="size-4" data-icon="inline-start" />
                        Confirm & Upload Video ({uploadPrivacy.toUpperCase()})
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => setSelectedRunId(null)}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  )
}
