'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface AnalysisProgress {
  phase: string
  message: string
  progress: number
}

export default function AnalysisPage() {
  const params = useParams()
  const router = useRouter()
  const analysisId = params.id as string

  const [currentPhase, setCurrentPhase] = useState<AnalysisProgress>({
    phase: 'loading',
    message: 'Loading historical data...',
    progress: 0
  })

  const [error, setError] = useState('')
  const [backendComplete, setBackendComplete] = useState(false)  // Backend done, start step animations
  const [allStepsComplete, setAllStepsComplete] = useState(false)  // All animations done
  const [numPeriods, setNumPeriods] = useState(75)  // Dynamic, updated from backend
  const [projectionYears, setProjectionYears] = useState(25)  // Dynamic
  const [completionStep, setCompletionStep] = useState(0)  // Track which completion step to show
  const [stepProgress, setStepProgress] = useState(0)  // Progress for current completion step

  // Generate completion steps based on dynamic values
  const getCompletionSteps = () => [
    { message: 'Fetched 100 years of S&P 500 historical data (1926-2025)' },
    { message: `Filtered to ${numPeriods} relevant ${projectionYears}-year periods for your timeframe` },
    { message: `Backtesting Pay off mortgage completely (${numPeriods} simulations)` },
    { message: `Backtesting Keep 100% invested (${numPeriods} simulations)` },
    { message: 'Analyzed risk factors specific to your financial situation' },
    { message: 'Generated personalized insights from historical patterns' },
    { message: 'Ranking strategies by expected value and success rate' }
  ]

  // Helper function to smoothly increment progress
  const smoothProgress = (targetProgress: number, message: string, phase: string) => {
    setCurrentPhase(prev => {
      const current = prev.progress
      if (current < targetProgress) {
        // Slow increment for analyzing phase (1% every 800ms)
        // This makes the progress feel deliberate and thorough
        setTimeout(() => {
          smoothProgress(targetProgress, message, phase)
        }, 800)
        return {
          phase,
          message,
          progress: Math.min(current + 1, targetProgress)
        }
      }
      return { phase, message, progress: targetProgress }
    })
  }

  useEffect(() => {
    const eventSource = new EventSource(`/api/analysis/${analysisId}/progress`)

    eventSource.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data)

        if (update.agent === 'complete') {
          smoothProgress(100, 'Analysis complete!', 'complete')

          // Extract dynamic values from result
          if (update.result?.num_periods) {
            setNumPeriods(update.result.num_periods)
          }
          if (update.result?.projection_years) {
            setProjectionYears(update.result.projection_years)
          }

          // Store result in sessionStorage
          sessionStorage.setItem(`analysis_${analysisId}`, JSON.stringify(update.result))

          // Start completion step animations
          setBackendComplete(true)

          eventSource.close()
        } else if (update.agent === 'data') {
          if (update.status === 'working') {
            smoothProgress(15, '📈 Loading 100 years of S&P 500 returns...', 'data')
          } else if (update.status === 'complete') {
            smoothProgress(25, '✓ Found 75 historical time periods', 'data')
          }
        } else if (update.agent === 'strategy') {
          if (update.message.includes('Strategy 1')) {
            smoothProgress(40, '🔄 Backtesting: What if you paid it off today?', 'strategy')
          } else if (update.message.includes('Strategy 2')) {
            smoothProgress(70, '🔄 Backtesting: What if you kept it invested?', 'strategy')
          } else if (update.status === 'complete') {
            smoothProgress(85, '✓ Tested strategies across all 75 periods', 'strategy')
          }
        } else if (update.agent === 'risk') {
          if (update.status === 'working') {
            smoothProgress(90, '🎯 Identifying risks specific to your situation...', 'risk')
          } else if (update.status === 'complete') {
            smoothProgress(95, `✓ Risk assessment complete: ${update.message}`, 'risk')
          }
        }
      } catch (err) {
        console.error('Error parsing SSE:', err)
      }
    }

    eventSource.onerror = () => {
      setError('Connection error. Please refresh the page.')
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [analysisId, router])

  // Handle completion step animation sequence
  useEffect(() => {
    if (!backendComplete) return

    const completionSteps = getCompletionSteps()
    const totalSteps = completionSteps.length

    const showNextStep = (stepIndex: number) => {
      if (stepIndex >= totalSteps) {
        // All steps complete
        setAllStepsComplete(true)
        // Redirect after 1 second
        setTimeout(() => {
          router.push(`/results/${analysisId}`)
        }, 1000)
        return
      }

      // Show this step
      setCompletionStep(stepIndex + 1)
      setStepProgress(0)

      // Animate progress bar to 100% over 1 second
      let progress = 0
      const animationInterval = setInterval(() => {
        progress += 10
        if (progress >= 100) {
          setStepProgress(100)
          clearInterval(animationInterval)
          // Move to next step immediately after animation completes
          setTimeout(() => showNextStep(stepIndex + 1), 0)
        } else {
          setStepProgress(progress)
        }
      }, 100) // Update every 100ms, so 100% in 1 second
    }

    // Start the sequence
    showNextStep(0)
  }, [backendComplete, analysisId, router, numPeriods, projectionYears])

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Analysis Progress Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8 transition-all duration-500">
          <div className="flex items-center gap-4 mb-4">
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full ${allStepsComplete ? 'bg-green-100' : 'bg-blue-100 animate-pulse'}`}>
              <span className="text-2xl">{allStepsComplete ? '✓' : '🔍'}</span>
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-gray-900">
                Analyzing Your Situation
              </h2>
              <p className="text-sm text-gray-600">
                {backendComplete ? 'Breaking down the analysis...' : 'Crunching 100 years of market data...'}
              </p>
            </div>
          </div>

          {/* Progress Bar - Show only during initial analysis, hide during completion steps */}
          {!backendComplete && (
            <div className="mb-4">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-700 ease-linear"
                  style={{ width: `${currentPhase.progress}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span className="font-medium text-blue-600">
                  {currentPhase.progress}%
                </span>
                <span>Est. 3-5 seconds</span>
              </div>
            </div>
          )}

          {/* Current Status or Completion Summary */}
          {!backendComplete ? (
            <>
              <div className="bg-blue-50 border-l-4 border-blue-500 p-3 mb-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    <div className="animate-spin">⚙️</div>
                  </div>
                  <div>
                    <div className="font-medium text-blue-900 text-sm">{currentPhase.message}</div>
                    {currentPhase.phase === 'strategy' && (
                      <div className="text-xs text-blue-700 mt-1">
                        Running simulations across all {numPeriods} historical periods...
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* What We're Doing */}
              <div className="grid grid-cols-1 gap-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className={currentPhase.progress >= 25 ? 'text-green-600 font-bold' : 'text-gray-400'}>
                    {currentPhase.progress >= 25 ? '✓' : '○'}
                  </span>
                  <span className={currentPhase.progress >= 25 ? 'text-gray-900' : 'text-gray-500'}>
                    Loading market returns from 1926-2025
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={currentPhase.progress >= 85 ? 'text-green-600 font-bold' : 'text-gray-400'}>
                    {currentPhase.progress >= 85 ? '✓' : '○'}
                  </span>
                  <span className={currentPhase.progress >= 85 ? 'text-gray-900' : 'text-gray-500'}>
                    Testing 2 strategies across 75 time periods (150 simulations)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={currentPhase.progress >= 95 ? 'text-green-600 font-bold' : 'text-gray-400'}>
                    {currentPhase.progress >= 95 ? '✓' : '○'}
                  </span>
                  <span className={currentPhase.progress >= 95 ? 'text-gray-900' : 'text-gray-500'}>
                    Analyzing risks and generating insights
                  </span>
                </div>
              </div>
            </>
          ) : (
            /* Completion Steps with Individual Progress Bars */
            <div className="space-y-3">
              {getCompletionSteps().map((step, index) => {
                const stepNumber = index + 1
                const isCompleted = completionStep > stepNumber
                const isCurrent = completionStep === stepNumber
                const isPending = completionStep < stepNumber

                return (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border-l-4 transition-all duration-300 ${
                      isCompleted
                        ? 'bg-green-50 border-green-500'
                        : isCurrent
                        ? 'bg-blue-50 border-blue-500'
                        : 'bg-gray-50 border-gray-300 opacity-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {isCompleted ? (
                          <span className="text-green-600 text-lg font-bold">✓</span>
                        ) : isCurrent ? (
                          <div className="animate-spin">⚙️</div>
                        ) : (
                          <span className="text-gray-400">○</span>
                        )}
                      </div>
                      <div className="flex-1">
                        <div className={`text-sm font-medium mb-2 ${
                          isCompleted ? 'text-green-900' : isCurrent ? 'text-blue-900' : 'text-gray-500'
                        }`}>
                          {step.message}
                        </div>
                        {isCurrent && (
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-100 ease-linear"
                              style={{ width: `${stepProgress}%` }}
                            />
                          </div>
                        )}
                        {isCompleted && (
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-green-500" style={{ width: '100%' }} />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Redirect message - show when all steps complete */}
              {completionStep > getCompletionSteps().length && (
                <div className="mt-4 text-center text-sm text-gray-600 animate-fade-in">
                  Redirecting to results...
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mt-4">
              {error}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
