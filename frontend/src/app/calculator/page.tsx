'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Calculator() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Form state
  const [age, setAge] = useState('55')
  const [employmentStatus, setEmploymentStatus] = useState<'working' | 'retired'>('retired')
  const [mortgageBalance, setMortgageBalance] = useState('500000')
  const [mortgageRate, setMortgageRate] = useState('3.0')
  const [mortgageYears, setMortgageYears] = useState('25')
  const [portfolio, setPortfolio] = useState('5000000')
  const [stockAllocation, setStockAllocation] = useState('100')
  const [income, setIncome] = useState('300000')
  const [incomeYears, setIncomeYears] = useState('10')
  const [spending, setSpending] = useState('200000')
  const [spendingIncludesMortgage, setSpendingIncludesMortgage] = useState(true)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Prepare request
      const requestData = {
        age: parseInt(age),
        employment_status: employmentStatus,
        mortgage: {
          balance: parseFloat(mortgageBalance),
          rate: parseFloat(mortgageRate),
          years: parseInt(mortgageYears)
        },
        financial: {
          portfolio: parseFloat(portfolio),
          stock_allocation_pct: parseFloat(stockAllocation),
          ...(employmentStatus === 'working'
            ? {
                income: parseFloat(income),
                income_years: parseInt(incomeYears)
              }
            : {}
          ),
          spending: parseFloat(spending),
          spending_includes_mortgage: spendingIncludesMortgage
        }
      }

      // Submit to API
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })

      if (!response.ok) {
        throw new Error('Failed to create analysis')
      }

      const data = await response.json()

      // Redirect to analysis page
      router.push(`/analysis/${data.analysis_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Tell us about your situation
          </h1>
          <p className="text-gray-600 mb-8">
            We'll analyze your specific scenario using 100 years of market data
          </p>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Age */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                👤 Your current age
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., 55"
                min="18"
                max="100"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                We'll project your finances until age 100
              </p>
            </div>

            <hr className="border-gray-200" />

            {/* Income Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Do you have additional income beyond your portfolio?
              </label>
              <div className="space-y-2">
                <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-blue-50 transition-colors"
                       style={{ borderColor: employmentStatus === 'working' ? '#3B82F6' : '#E5E7EB' }}>
                  <input
                    type="radio"
                    name="employment"
                    value="working"
                    checked={employmentStatus === 'working'}
                    onChange={() => setEmploymentStatus('working')}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">Yes, I have additional income</div>
                    <div className="text-sm text-gray-600">W2 income, business income, rental income, social security, pension, etc.</div>
                  </div>
                </label>

                <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-blue-50 transition-colors"
                       style={{ borderColor: employmentStatus === 'retired' ? '#3B82F6' : '#E5E7EB' }}>
                  <input
                    type="radio"
                    name="employment"
                    value="retired"
                    checked={employmentStatus === 'retired'}
                    onChange={() => setEmploymentStatus('retired')}
                    className="mr-3"
                  />
                  <div>
                    <div className="font-medium">No additional income (portfolio only)</div>
                    <div className="text-sm text-gray-600">Living entirely off investments</div>
                  </div>
                </label>
              </div>
            </div>

            <hr className="border-gray-200" />

            {/* Mortgage Details */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">💰 Your Mortgage</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Balance remaining
                  </label>
                  <input
                    type="number"
                    value={mortgageBalance}
                    onChange={(e) => setMortgageBalance(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 500000"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Interest rate (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={mortgageRate}
                    onChange={(e) => setMortgageRate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 3.0"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Years remaining
                  </label>
                  <input
                    type="number"
                    value={mortgageYears}
                    onChange={(e) => setMortgageYears(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 25"
                    required
                  />
                </div>
              </div>
            </div>

            <hr className="border-gray-200" />

            {/* Financial Situation */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">🏦 Your Financial Situation</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total investment portfolio
                  </label>
                  <input
                    type="number"
                    value={portfolio}
                    onChange={(e) => setPortfolio(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 5000000"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Stocks, bonds, retirement accounts, etc.
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stock allocation (%)
                  </label>
                  <input
                    type="number"
                    value={stockAllocation}
                    onChange={(e) => setStockAllocation(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 60"
                    min="0"
                    max="100"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    What % of your portfolio is in stocks/equities? (Rest assumed in bonds at ~4% return)
                  </p>
                </div>

                {employmentStatus === 'working' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Annual additional income
                      </label>
                      <input
                        type="number"
                        value={income}
                        onChange={(e) => setIncome(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="e.g., 300000"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        W2, business, rental, social security, pension, etc.
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        For how many years will you have this income?
                      </label>
                      <input
                        type="number"
                        value={incomeYears}
                        onChange={(e) => setIncomeYears(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="e.g., 10"
                        min="1"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Number of years until retirement or income stops
                      </p>
                    </div>
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Annual spending
                  </label>
                  <input
                    type="number"
                    value={spending}
                    onChange={(e) => setSpending(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., 200000"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your total annual expenses
                  </p>
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={spendingIncludesMortgage}
                      onChange={(e) => setSpendingIncludesMortgage(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      My spending includes mortgage payment
                    </span>
                  </label>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold px-8 py-4 rounded-lg text-lg transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze My Situation →'}
            </button>

            <p className="text-center text-sm text-gray-500">
              🔒 Your data is never stored • ⚡ Takes 3-5 seconds
            </p>
          </form>
        </div>
      </div>
    </main>
  )
}
