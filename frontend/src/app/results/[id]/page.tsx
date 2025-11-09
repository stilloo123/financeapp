'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

interface PeriodDetail {
  period: string
  start_year: number
  end_year: number
  final_balance: number
  success: boolean
  ran_out_year: number | null
}

interface Strategy {
  name: string
  emoji: string
  tags: string[]
  rank: number
  avg_outcome: number
  median_outcome: number  // At end of projection (age 100)
  p10_outcome: number
  p90_outcome: number
  median_at_payoff: number  // At mortgage payoff milestone
  p10_at_payoff: number
  p90_at_payoff: number
  success_rate: number
  min_outcome: number
  max_outcome: number
  mortgage_payoff_year: number
  projection_years: number
  bond_type?: 'fund' | 'treasury'
  period_details?: PeriodDetail[]
  worst_periods?: PeriodDetail[]
  best_periods?: PeriodDetail[]
}

interface RiskDetail {
  type: string
  severity: string
  title: string
  description: string
  mitigation: string[]
  withdrawal_rate?: number
}

interface AnalysisResult {
  recommended: Strategy
  strategies: Strategy[]
  risk_level: string
  risks?: RiskDetail[]
  insights: Array<{
    message: string
  }>
  user_input?: {
    age: number
    [key: string]: any
  }
  bond_return_used?: number
}

export default function ResultsPage() {
  const params = useParams()
  const router = useRouter()
  const analysisId = params.id as string

  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState('')
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null)

  useEffect(() => {
    // Fetch the completed analysis result
    const fetchResult = async () => {
      try {
        // For now, get from sessionStorage (the analysis page will store it)
        const storedResult = sessionStorage.getItem(`analysis_${analysisId}`)
        if (storedResult) {
          setResult(JSON.parse(storedResult))
        } else {
          // If no stored result, redirect back to analysis page
          router.push(`/analysis/${analysisId}`)
        }
      } catch (err) {
        setError('Failed to load results')
      }
    }

    fetchResult()
  }, [analysisId, router])

  if (error) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        </div>
      </main>
    )
  }

  if (!result) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center">Loading results...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white py-12">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* 2-Column Layout (Sticky Summary + Scrollable Details) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* LEFT: Sticky Summary Card */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-8 space-y-6">
              {/* Recommendation Summary */}
              <div className="bg-white rounded-lg shadow-lg p-6 animate-fade-in">
                <div className="text-center mb-6">
                  <div className="text-5xl mb-3">
                    {result.recommended.name === 'Keep 100% Invested' ? '📈' : '🏠'}
                  </div>
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">
                    {result.recommended.name === 'Keep 100% Invested' ? 'KEEP IT INVESTED' : 'PAY OFF MORTGAGE'}
                  </h1>
                  {result.recommended.tags && (
                    <div className="flex gap-2 mb-2 justify-center">
                      {result.recommended.tags.map((tag, i) => (
                        <span
                          key={i}
                          className={`text-xs px-3 py-1 rounded-full font-semibold ${
                            tag === 'Most Money' ? 'bg-green-100 text-green-800' :
                            tag === 'Most Safety' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  {/* Portfolio Allocation */}
                  {result.user_input && (() => {
                    const portfolio = result.user_input.financial?.portfolio || 0
                    const stockPct = result.user_input.financial?.stock_allocation_pct || 100
                    const bondPct = 100 - stockPct
                    const mortgageBalance = result.user_input.mortgage?.balance || 0

                    const portfolioAfterPayoff = result.recommended.name === 'Pay Off Completely'
                      ? portfolio - mortgageBalance
                      : portfolio

                    const stockAmount = portfolioAfterPayoff * (stockPct / 100)
                    const bondAmount = portfolioAfterPayoff * (bondPct / 100)

                    return (
                      <div className="text-xs text-gray-600 mb-3">
                        {stockPct}% S&P 500 (${(stockAmount / 1000000).toFixed(2)}M) + {bondPct}% Bonds (${(bondAmount / 1000000).toFixed(2)}M){result.bond_return_used && ` at ${result.bond_return_used.toFixed(2)}% (today's 30-yr treasury)`}
                      </div>
                    )
                  })()}
                  <p className="text-sm text-gray-600">
                    {result.recommended.tags && result.recommended.tags.includes('Most Money') && result.recommended.tags.includes('Most Safety')
                      ? 'Best on both money and safety'
                      : result.recommended.tags && result.recommended.tags.includes('Most Money')
                      ? `$${((result.strategies[0].median_outcome - result.strategies[1].median_outcome) / 1000000).toFixed(1)}M more in typical scenario`
                      : 'Lower risk, peace of mind'
                    }
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Success Rate */}
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">Success Rate</div>
                    <div className="text-3xl font-bold text-gray-900">
                      {(result.recommended.success_rate * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">chance of success</div>
                  </div>

                  {/* Two Milestone Outcomes */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
                    <div className="text-xs font-semibold text-gray-700 mb-3">Most Likely Outcomes</div>

                    {/* Mortgage Payoff Milestone */}
                    <div className="mb-3 pb-3 border-b border-green-200">
                      <div className="text-xs text-gray-600 mb-1">
                        At Mortgage Payoff (Age {(result.user_input?.age || 55) + result.recommended.mortgage_payoff_year}, Year {result.recommended.mortgage_payoff_year})
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        ${(result.recommended.median_at_payoff / 1000000).toFixed(1)}M
                      </div>
                    </div>

                    {/* End of Life Milestone */}
                    <div>
                      <div className="text-xs text-gray-600 mb-1">
                        At End (Age {(result.user_input?.age || 55) + result.recommended.projection_years})
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        ${(result.recommended.median_outcome / 1000000).toFixed(1)}M
                      </div>
                    </div>
                  </div>

                  {/* Conservative/Downside */}
                  {result.recommended.p10_outcome >= 0 ? (
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Conservative Estimate</div>
                      <div className="text-2xl font-bold text-gray-900">
                        ${(result.recommended.p10_outcome / 1000000).toFixed(1)}M+
                      </div>
                      <div className="text-xs text-gray-500">
                        at age {(result.user_input?.age || 55) + result.recommended.projection_years} (90% chance)
                      </div>
                    </div>
                  ) : (
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <div className="text-xs text-gray-600 mb-1">⚠️ Downside Risk</div>
                      <div className="text-lg font-bold text-red-700">
                        Could run out
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        In bad market scenarios, portfolio may deplete before age {(result.user_input?.age || 55) + result.recommended.projection_years}
                      </div>
                    </div>
                  )}

                  {/* Risk factors */}
                  {result.risks && result.risks.length > 0 && (
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Important Considerations</div>
                      <div className="text-lg font-bold text-purple-800">
                        {result.risks.length} {result.risks.length === 1 ? 'Factor' : 'Factors'}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">Scroll down to learn more</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Insight */}
              <div className="bg-white rounded-lg shadow-lg p-4 text-sm">
                <div className="font-semibold text-gray-900 mb-2">💡 Key Insight</div>
                <div className="text-gray-700">
                  {result.insights[0]?.message || 'Analysis complete based on historical data.'}
                </div>
              </div>

              {/* Data Credibility */}
              <div className="bg-white rounded-lg shadow-lg p-4 text-xs text-gray-600">
                <div className="font-semibold text-gray-900 mb-2">📊 Analysis Based On:</div>
                <div className="space-y-1">
                  <div>• Real (inflation-adjusted) returns</div>
                  <div>• Your spending maintains purchasing power</div>
                  <div>• Mortgage payment stays constant</div>
                  <div>• 100 years of S&P 500 data (1926-2025)</div>
                  <div>• 97 years of bond data (1928-2024)</div>
                  <div>• 75 historical 25-year periods</div>
                  <div>• 300 backtested scenarios</div>
                  {result.bond_return_used && (
                    <div>• Treasury: {result.bond_return_used.toFixed(2)}% (30-year)</div>
                  )}
                  <div>• Bond Fund: Damodaran 10-yr Treasury</div>
                  <div className="text-gray-500 italic mt-2">Source: NYU Stern / CRSP / FRED</div>
                </div>
              </div>

              {/* Back Button */}
              <button
                onClick={() => router.push('/calculator')}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold px-4 py-3 rounded-lg transition-colors"
              >
                ← Run New Analysis
              </button>
            </div>
          </div>

          {/* RIGHT: Scrollable Details */}
          <div className="lg:col-span-2 space-y-8">
            {/* Data Credibility Banner (Mobile/Desktop top) */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center gap-3">
                <div className="text-3xl">📊</div>
                <div>
                  <div className="font-semibold text-gray-900 text-sm">Research-Grade Analysis with Inflation Adjustment</div>
                  <div className="text-xs text-gray-600 mt-1">
                    Based on <span className="font-semibold">real (inflation-adjusted) returns</span> •
                    <span className="font-semibold"> 100 years of S&P 500</span> (1926-2025) +
                    <span className="font-semibold"> 97 years of bond data</span> (Damodaran 1928-2024) •
                    <span className="font-semibold"> FRED CPI data</span> (1948-2024) •
                    <span className="font-semibold"> 300 backtested scenarios</span> across 75 historical periods •
                    Your spending maintains purchasing power
                  </div>
                </div>
              </div>
            </div>

            {/* Recommended Strategy */}
            <div className="bg-white rounded-lg shadow-lg p-8 animate-fade-in" style={{ animationDelay: '0.15s' }}>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Recommended Strategy</h2>
              <p className="text-sm text-gray-600 mb-6">Based on {result.strategies.length} different scenarios analyzed across 75 historical periods:</p>

              <div className="grid grid-cols-1 gap-6">
                {[result.recommended].map((strategy, index) => {
                  const isKeepInvested = strategy.name.includes('Keep')
                  const isPayOff = strategy.name.includes('Pay Off')

                  // Find the comparison strategy (opposite action, same bond type)
                  const comparisonStrategy = result.strategies.find(s =>
                    s.bond_type === strategy.bond_type &&
                    (isKeepInvested ? s.name.includes('Pay Off') : s.name.includes('Keep'))
                  )

                  const medianDifference = comparisonStrategy
                    ? ((strategy.median_outcome - comparisonStrategy.median_outcome) / 1000000).toFixed(1)
                    : '0.0'

                  return (
                    <div key={strategy.name} className={`border-2 rounded-lg p-5 ${
                      strategy.tags && strategy.tags.length > 1 ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">{strategy.emoji}</span>
                        <div>
                          <div className="font-bold text-lg">{strategy.name}</div>
                          {strategy.tags && (
                            <div className="flex gap-1 mt-1">
                              {strategy.tags.map((tag, i) => (
                                <span key={i} className={`text-xs px-2 py-0.5 rounded ${
                                  tag === 'Most Money' ? 'bg-green-100 text-green-800' :
                                  tag === 'Most Safety' ? 'bg-blue-100 text-blue-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                      {/* Portfolio Allocation */}
                      {result.user_input && (() => {
                        const portfolio = result.user_input.financial?.portfolio || 0
                        const stockPct = result.user_input.financial?.stock_allocation_pct || 100
                        const bondPct = 100 - stockPct
                        const mortgageBalance = result.user_input.mortgage?.balance || 0

                        const portfolioAfterPayoff = strategy.name === 'Pay Off Completely'
                          ? portfolio - mortgageBalance
                          : portfolio

                        const stockAmount = portfolioAfterPayoff * (stockPct / 100)
                        const bondAmount = portfolioAfterPayoff * (bondPct / 100)

                        return (
                          <div className="text-xs text-gray-600 mb-3">
                            {stockPct}% S&P 500 (${(stockAmount / 1000000).toFixed(2)}M) + {bondPct}% Bonds (${(bondAmount / 1000000).toFixed(2)}M)
                            {strategy.bond_type === 'fund' && bondPct > 0 && (
                              <span className="text-blue-600 font-semibold"> • 10-yr Treasury Bond Fund (Damodaran) w/ Annual Rebalancing</span>
                            )}
                            {strategy.bond_type === 'treasury' && bondPct > 0 && result.bond_return_used && (
                              <span> • 30-yr Treasury at {result.bond_return_used.toFixed(2)}%</span>
                            )}
                          </div>
                        )
                      })()}

                      <div className="space-y-3 text-sm">
                        <div>
                          <div className="font-semibold text-gray-900 mb-1">Best for you if:</div>
                          <ul className="space-y-1 text-gray-700">
                            {isKeepInvested ? (
                              <>
                                <li>• You're comfortable with market volatility</li>
                                <li>• You want to maximize long-term wealth</li>
                                <li>• Your mortgage rate is low (3-4%)</li>
                                <li>• You have strong cash reserves</li>
                              </>
                            ) : (
                              <>
                                <li>• You value peace of mind over max returns</li>
                                <li>• You want guaranteed savings (mortgage rate)</li>
                                <li>• You prefer lower monthly obligations</li>
                                <li>• You're risk-averse or near retirement</li>
                              </>
                            )}
                          </ul>
                        </div>

                        <div>
                          <div className="font-semibold text-gray-900 mb-1">Trade-off:</div>
                          <div className="text-gray-700">
                            {isKeepInvested ? (
                              <>You'll likely have ${medianDifference}M more, but keep your mortgage payment obligation.</>
                            ) : (
                              <>You'll have about ${Math.abs(parseFloat(medianDifference)).toFixed(1)}M less, but eliminate your mortgage payment and reduce risk.</>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Strategy Comparison */}
            <div className="bg-white rounded-lg shadow-lg p-8 animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Breakdown</h2>
              <p className="text-sm text-gray-600 mb-4">Click any strategy to see complete historical analysis</p>
              <div className="space-y-4">
                {result.strategies.map((strategy, index) => {
                  const isExpanded = expandedStrategy === strategy.name
                  return (
                    <div
                      key={strategy.name}
                      className={`border-2 rounded-lg transition-all cursor-pointer hover:shadow-md ${
                        strategy.tags && strategy.tags.length > 1 ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                      }`}
                      onClick={() => setExpandedStrategy(isExpanded ? null : strategy.name)}
                    >
                      <div className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <span className="text-2xl">{strategy.emoji}</span>
                              <span className="font-bold text-lg">{strategy.name}</span>
                              {strategy.tags && strategy.tags.map((tag, i) => (
                                <span
                                  key={i}
                                  className={`text-xs px-2 py-1 rounded ${
                                    tag === 'Most Money' ? 'bg-green-100 text-green-800' :
                                    tag === 'Most Safety' ? 'bg-blue-100 text-blue-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}
                                >
                                  {tag}
                                </span>
                              ))}
                              <span className="ml-auto text-gray-400">{isExpanded ? '▼' : '▶'}</span>
                            </div>
                            {/* Portfolio Allocation Breakdown */}
                            {result.user_input && (() => {
                              const portfolio = result.user_input.financial?.portfolio || 0
                              const stockPct = result.user_input.financial?.stock_allocation_pct || 100
                              const bondPct = 100 - stockPct
                              const mortgageBalance = result.user_input.mortgage?.balance || 0

                              // Calculate portfolio value after mortgage payoff if applicable
                              const portfolioAfterPayoff = strategy.name === 'Pay Off Completely'
                                ? portfolio - mortgageBalance
                                : portfolio

                              const stockAmount = portfolioAfterPayoff * (stockPct / 100)
                              const bondAmount = portfolioAfterPayoff * (bondPct / 100)

                              return (
                                <div className="text-xs text-gray-600 mb-2">
                                  {stockPct}% S&P 500 (${(stockAmount / 1000000).toFixed(2)}M) + {bondPct}% Bonds (${(bondAmount / 1000000).toFixed(2)}M)
                                  {strategy.bond_type === 'fund' && bondPct > 0 && (
                                    <span className="text-blue-600 font-semibold"> • 10-yr Treasury Bond Fund (Damodaran) w/ Annual Rebalancing</span>
                                  )}
                                  {strategy.bond_type === 'treasury' && bondPct > 0 && result.bond_return_used && (
                                    <span> • 30-yr Treasury at {result.bond_return_used.toFixed(2)}%</span>
                                  )}
                                </div>
                              )
                            })()}
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <div className="text-gray-600">Success Rate</div>
                                <div className="font-semibold">{(strategy.success_rate * 100).toFixed(0)}%</div>
                              </div>
                              <div>
                                <div className="text-gray-600">Most Likely</div>
                                <div className="font-semibold">${(strategy.median_outcome / 1000000).toFixed(1)}M</div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {isExpanded && (
                          <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                            {/* Dual Milestone Outcomes */}
                            <div>
                              <div className="font-semibold text-gray-900 mb-3">What to Expect</div>

                              {/* Mortgage Payoff Milestone */}
                              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                                <div className="font-semibold text-blue-900 mb-2 text-sm">
                                  📅 At Mortgage Payoff (Age {(result.user_input?.age || 55) + strategy.mortgage_payoff_year}, Year {strategy.mortgage_payoff_year})
                                </div>
                                <div className="space-y-2 text-sm">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-700">Most Likely:</span>
                                    <span className="font-bold text-lg">${(strategy.median_at_payoff / 1000000).toFixed(1)}M</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-700">Conservative (10th %ile):</span>
                                    <span className="font-semibold">${(strategy.p10_at_payoff / 1000000).toFixed(1)}M</span>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-700">Optimistic (90th %ile):</span>
                                    <span className="font-semibold">${(strategy.p90_at_payoff / 1000000).toFixed(1)}M</span>
                                  </div>
                                </div>
                              </div>

                              {/* End of Projection Milestone */}
                              <div className="p-4 bg-green-50 rounded-lg">
                                <div className="font-semibold text-green-900 mb-2 text-sm">
                                  🎯 At End of Projection (Age {(result.user_input?.age || 55) + strategy.projection_years})
                                </div>
                                <div className="space-y-2 text-sm">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-700">Most Likely:</span>
                                    <span className="font-bold text-lg">${(strategy.median_outcome / 1000000).toFixed(1)}M</span>
                                  </div>
                                  {strategy.p10_outcome >= 0 ? (
                                    <div className="flex justify-between items-center">
                                      <span className="text-gray-700">Conservative (10th %ile):</span>
                                      <span className="font-semibold">${(strategy.p10_outcome / 1000000).toFixed(1)}M</span>
                                    </div>
                                  ) : (
                                    <div className="bg-red-100 p-2 rounded">
                                      <div className="text-red-800 font-semibold text-xs">⚠️ Could run out in bad scenarios</div>
                                    </div>
                                  )}
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-700">Optimistic (90th %ile):</span>
                                    <span className="font-semibold">${(strategy.p90_outcome / 1000000).toFixed(1)}M</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Best Performing Periods */}
                            {strategy.best_periods && strategy.best_periods.length > 0 && (
                              <div>
                                <div className="font-semibold text-gray-900 mb-2">Top 5 Best Periods</div>
                                <div className="space-y-1 text-sm">
                                  {strategy.best_periods.map((period, i) => (
                                    <div key={i} className="flex justify-between items-center bg-green-50 p-2 rounded">
                                      <span className="text-gray-700">{period.period}</span>
                                      <span className="text-green-600 font-semibold">
                                        ${(period.final_balance / 1000000).toFixed(1)}M
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Worst Performing Periods */}
                            {strategy.worst_periods && strategy.worst_periods.length > 0 && (
                              <div>
                                <div className="font-semibold text-gray-900 mb-2">
                                  Worst Periods {strategy.worst_periods.length > 5 && '(includes 2000-2025)'}
                                </div>
                                <div className="space-y-1 text-sm">
                                  {strategy.worst_periods.map((period, i) => {
                                    const is2000Period = period.start_year === 2000
                                    return (
                                      <div key={i} className={`flex justify-between items-center p-2 rounded ${
                                        period.final_balance < 0 ? 'bg-red-50' : 'bg-yellow-50'
                                      } ${is2000Period ? 'ring-2 ring-blue-400' : ''}`}>
                                        <span className="text-gray-700">
                                          {period.period}
                                          {is2000Period && <span className="ml-2 text-xs text-blue-600 font-semibold">📉 Lost Decade</span>}
                                        </span>
                                        <span className={`font-semibold ${
                                          period.final_balance < 0 ? 'text-red-600' : 'text-yellow-600'
                                        }`}>
                                          {period.final_balance < 0 ? (
                                            period.ran_out_year ? `Ran out in Year ${period.ran_out_year}` : 'Ran out'
                                          ) : (
                                            `$${(period.final_balance / 1000000).toFixed(1)}M`
                                          )}
                                        </span>
                                      </div>
                                    )
                                  })}
                                </div>
                              </div>
                            )}

                            {/* Success/Failure Stats */}
                            <div className="bg-gray-50 p-3 rounded">
                              <div className="text-sm">
                                <span className="font-semibold">Out of 75 historical periods:</span>
                                <div className="mt-1">
                                  <span className="text-green-600">✓ {Math.round(strategy.success_rate * 75)} periods succeeded</span>
                                  {' • '}
                                  <span className="text-red-600">✗ {75 - Math.round(strategy.success_rate * 75)} periods failed</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Risk Assessment */}
            {result.risks && result.risks.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-8 animate-fade-in" style={{ animationDelay: '0.4s' }}>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Things to Consider</h2>
                <p className="text-sm text-gray-600 mb-6">
                  Based on your financial situation, here are some important factors to keep in mind:
                </p>

                <div className="space-y-4">
                  {result.risks.map((risk, index) => (
                    <div
                      key={index}
                      className={`border-l-4 p-5 rounded-lg ${
                        risk.severity === 'high'
                          ? 'border-red-500 bg-red-50'
                          : risk.severity === 'medium'
                          ? 'border-yellow-500 bg-yellow-50'
                          : 'border-blue-500 bg-blue-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5 text-xl">
                          {risk.severity === 'high' ? '⚠️' : risk.severity === 'medium' ? '💡' : 'ℹ️'}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900 mb-2 text-base">{risk.title}</div>
                          <div className="text-sm text-gray-700 mb-4 leading-relaxed">{risk.description}</div>
                          {risk.mitigation && risk.mitigation.length > 0 && (
                            <div className="bg-white bg-opacity-70 p-3 rounded">
                              <div className="font-medium text-gray-900 text-sm mb-2">💪 Here's what you can do:</div>
                              <ul className="text-sm text-gray-700 space-y-1.5">
                                {risk.mitigation.map((item, i) => (
                                  <li key={i} className="flex items-start gap-2">
                                    <span className="text-green-600 font-bold mt-0.5">→</span>
                                    <span>{item}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {result.risks.length === 0 && (
                  <div className="text-center py-8 text-gray-600">
                    <div className="text-4xl mb-3">✅</div>
                    <div className="font-semibold">Your financial situation looks solid!</div>
                    <div className="text-sm mt-1">No major risk factors identified.</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
          opacity: 0;
        }
      `}</style>
    </main>
  )
}
