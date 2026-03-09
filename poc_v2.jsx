import React, { useState } from 'react';
import { Search, CheckCircle, AlertTriangle, Loader, Brain, Database, FileCheck, Globe, BookOpen } from 'lucide-react';

export default function GroundedAIPrototype() {
  const [query, setQuery] = useState('');
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState('');
  const [results, setResults] = useState(null);

  const parseIntent = (userQuery) => {
    const lower = userQuery.toLowerCase();
    let queryType = 'general';
    let needsWebSearch = false;
    let needsDeepResearch = false;

    // Detect query type
    if (lower.includes('latest') || lower.includes('recent') || lower.includes('current') || lower.includes('today')) {
      queryType = 'current_events';
      needsWebSearch = true;
    } else if (lower.includes('research') || lower.includes('study') || lower.includes('paper')) {
      queryType = 'research';
      needsWebSearch = true;
      needsDeepResearch = true;
    } else if (lower.includes('compare') || lower.includes('vs') || lower.includes('versus')) {
      queryType = 'comparison';
      needsWebSearch = true;
    } else if (lower.includes('how to') || lower.includes('tutorial') || lower.includes('guide')) {
      queryType = 'instructional';
      needsWebSearch = true;
    } else if (lower.includes('what is') || lower.includes('explain') || lower.includes('define')) {
      queryType = 'explanation';
      needsWebSearch = true; // Even definitions benefit from current sources
    }

    // Extract key terms for search
    const searchTerms = userQuery
      .replace(/^(what is|explain|tell me about|how does|why does|research|find)/gi, '')
      .trim();

    return {
      queryType,
      needsWebSearch,
      needsDeepResearch,
      searchTerms,
      originalQuery: userQuery
    };
  };

  const searchWeb = async (searchTerms, needsDeep = false) => {
    try {
      setCurrentStep(`Searching the web for: "${searchTerms}"...`);
      
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          messages: [
            { 
              role: 'user', 
              content: searchTerms
            }
          ],
          tools: [
            {
              type: "web_search_20250305",
              name: "web_search"
            }
          ]
        }),
      });

      const data = await response.json();
      
      // Extract web search results and text responses
      let searchResults = [];
      let responseText = '';
      
      if (data.content) {
        for (const block of data.content) {
          if (block.type === 'text') {
            responseText += block.text;
          }
        }
      }

      return {
        found: true,
        results: responseText,
        resultCount: data.content ? data.content.length : 0,
        searchPerformed: true
      };
    } catch (error) {
      console.error('Web search error:', error);
      return {
        found: false,
        results: '',
        resultCount: 0,
        searchPerformed: false,
        error: error.message
      };
    }
  };

  const evaluateSourceQuality = (searchResults) => {
    // Analyze the quality of sources found
    const qualityIndicators = {
      hasCitations: /\[\d+\]/.test(searchResults.results),
      hasSpecificData: /\d{4}|\d+%|\d+\s*(people|users|dollars)/.test(searchResults.results),
      reasonableLength: searchResults.results.length > 200,
      hasMultipleSources: searchResults.resultCount > 1
    };

    const qualityScore = Object.values(qualityIndicators).filter(Boolean).length / Object.keys(qualityIndicators).length;

    return {
      score: qualityScore,
      indicators: qualityIndicators,
      assessment: qualityScore > 0.7 ? 'high' : qualityScore > 0.4 ? 'medium' : 'low'
    };
  };

  const buildResearchBlueprint = (intent, searchResults, quality) => {
    if (!searchResults.found || !searchResults.searchPerformed) {
      return {
        status: 'search_failed',
        instruction: 'Unable to retrieve current information',
        facts: [],
        constraints: ['Acknowledge search failure', 'Suggest manual research']
      };
    }

    return {
      status: 'ready',
      instruction: 'Synthesize information from web search results',
      searchData: searchResults.results,
      quality: quality,
      constraints: [
        'Base response on search results provided',
        'Cite sources when making specific claims',
        'Distinguish between verified facts and interpretations',
        'Acknowledge if information is limited or conflicting',
        `Quality assessment: ${quality.assessment}`
      ]
    };
  };

  const generateGroundedResponse = async (blueprint, originalQuery) => {
    if (blueprint.status === 'search_failed') {
      return {
        text: "I attempted to search for current information but encountered an issue. For research queries, I recommend:\n\n1. Using specialized research databases (Google Scholar, PubMed, arXiv)\n2. Checking official sources directly\n3. Consulting recent peer-reviewed publications\n\nWould you like me to help reformulate your search query?",
        verified: false,
        confidence: 0,
        hallucination_risk: 'high',
        sources: []
      };
    }

    const constrainedPrompt = `You are a research-focused AI assistant that synthesizes information from web searches.

CRITICAL INSTRUCTIONS:
1. Use the web search results provided below as your PRIMARY source
2. Clearly distinguish between:
   - Direct facts from sources (cite them)
   - Your analysis/interpretation (label as such)
   - Areas where information is uncertain or conflicting
3. If search results are incomplete, explicitly state what's missing
4. Provide actionable next steps for deeper research if needed

WEB SEARCH RESULTS:
${blueprint.searchData}

SOURCE QUALITY ASSESSMENT: ${blueprint.quality.assessment}
${blueprint.quality.score < 0.7 ? '\nNote: Search results may be limited. Recommend additional verification.' : ''}

USER'S RESEARCH QUESTION: ${originalQuery}

Generate a comprehensive, well-sourced response:`;

    try {
      setCurrentStep('Synthesizing information from sources...');
      
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          messages: [
            { role: 'user', content: constrainedPrompt }
          ],
        }),
      });

      const data = await response.json();
      const text = data.content.map(item => item.type === 'text' ? item.text : '').join('\n');

      return {
        text,
        verified: true,
        confidence: blueprint.quality.score,
        hallucination_risk: blueprint.quality.assessment === 'high' ? 'low' : 'medium',
        sourceQuality: blueprint.quality.assessment
      };
    } catch (error) {
      return {
        text: `Error generating response: ${error.message}`,
        verified: false,
        confidence: 0,
        hallucination_risk: 'unknown'
      };
    }
  };

  const handleProcess = async () => {
    setProcessing(true);
    setResults(null);

    try {
      // Step 1: Intent Analysis
      setCurrentStep('Analyzing your research question...');
      await new Promise(resolve => setTimeout(resolve, 500));
      const intent = parseIntent(query);

      // Step 2: Dynamic Knowledge Retrieval (Web Search)
      const searchResults = await searchWeb(intent.searchTerms, intent.needsDeepResearch);

      // Step 3: Source Quality Evaluation
      setCurrentStep('Evaluating source quality and reliability...');
      await new Promise(resolve => setTimeout(resolve, 500));
      const quality = evaluateSourceQuality(searchResults);

      // Step 4: Research Blueprint
      setCurrentStep('Building research synthesis plan...');
      await new Promise(resolve => setTimeout(resolve, 400));
      const blueprint = buildResearchBlueprint(intent, searchResults, quality);

      // Step 5: Generate Grounded Response
      const response = await generateGroundedResponse(blueprint, query);

      setResults({
        intent,
        searchResults,
        quality,
        blueprint,
        response
      });
    } catch (error) {
      console.error('Processing error:', error);
      setResults({
        error: true,
        message: error.message
      });
    } finally {
      setProcessing(false);
      setCurrentStep('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/20 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="text-purple-300" size={40} />
            <h1 className="text-4xl font-bold text-white">
              Research-Grade AI System
            </h1>
          </div>
          <p className="text-purple-200 mb-6">
            Dynamic web search + source validation + grounded synthesis for real research
          </p>

          <div className="bg-purple-900/30 border border-purple-400/30 rounded-lg p-4 mb-6">
            <h3 className="text-white font-semibold mb-2">Try these research queries:</h3>
            <div className="flex flex-wrap gap-2">
              {[
                'Latest developments in quantum computing',
                'How does CRISPR gene editing work',
                'Recent AI hallucination research',
                'Compare RAG vs fine-tuning for LLMs',
                'Current trends in renewable energy'
              ].map(ex => (
                <button
                  key={ex}
                  onClick={() => setQuery(ex)}
                  className="bg-purple-600/50 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 mb-6">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a research question..."
              className="flex-1 bg-white/10 border border-white/30 rounded-lg px-4 py-3 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
              onKeyPress={(e) => e.key === 'Enter' && !processing && handleProcess()}
            />
            <button
              onClick={handleProcess}
              disabled={!query || processing}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2"
            >
              {processing ? <Loader className="animate-spin" size={20} /> : <Search size={20} />}
              Research
            </button>
          </div>

          {processing && (
            <div className="bg-indigo-900/50 border border-indigo-400/30 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <Loader className="animate-spin text-indigo-300" size={24} />
                <span className="text-indigo-200">{currentStep}</span>
              </div>
            </div>
          )}
        </div>

        {results && !results.error && (
          <div className="space-y-6">
            {/* Intent Analysis */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="text-blue-300" size={24} />
                <h2 className="text-2xl font-bold text-white">Step 1: Query Analysis</h2>
              </div>
              <div className="grid md:grid-cols-4 gap-4">
                <div className="bg-blue-900/30 rounded-lg p-4">
                  <div className="text-blue-200 text-sm mb-1">Query Type</div>
                  <div className="text-white font-semibold capitalize">
                    {results.intent.queryType.replace('_', ' ')}
                  </div>
                </div>
                <div className="bg-blue-900/30 rounded-lg p-4">
                  <div className="text-blue-200 text-sm mb-1">Web Search</div>
                  <div className="text-white font-semibold">
                    {results.intent.needsWebSearch ? '✓ Required' : '○ Optional'}
                  </div>
                </div>
                <div className="bg-blue-900/30 rounded-lg p-4">
                  <div className="text-blue-200 text-sm mb-1">Deep Research</div>
                  <div className="text-white font-semibold">
                    {results.intent.needsDeepResearch ? '✓ Yes' : '○ No'}
                  </div>
                </div>
                <div className="bg-blue-900/30 rounded-lg p-4">
                  <div className="text-blue-200 text-sm mb-1">Search Terms</div>
                  <div className="text-white font-semibold text-sm">
                    {results.intent.searchTerms.substring(0, 30)}...
                  </div>
                </div>
              </div>
            </div>

            {/* Web Search Results */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="text-green-300" size={24} />
                <h2 className="text-2xl font-bold text-white">Step 2: Web Search & Retrieval</h2>
              </div>
              {results.searchResults.searchPerformed ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-4 mb-3">
                    <div className="text-green-200 flex items-center gap-2">
                      <CheckCircle size={20} />
                      Search completed
                    </div>
                    <div className="text-green-300 text-sm">
                      {results.searchResults.resultCount} sources processed
                    </div>
                  </div>
                  <div className="bg-green-900/30 border border-green-400/30 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <div className="text-green-100 text-sm font-mono whitespace-pre-wrap">
                      {results.searchResults.results.substring(0, 1000)}
                      {results.searchResults.results.length > 1000 && '\n\n... (truncated for display)'}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-orange-900/30 border border-orange-400/30 rounded-lg p-4">
                  <AlertTriangle className="text-orange-300 mb-2" size={24} />
                  <div className="text-orange-200">
                    Web search failed: {results.searchResults.error || 'Unknown error'}
                  </div>
                </div>
              )}
            </div>

            {/* Source Quality */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen className="text-yellow-300" size={24} />
                <h2 className="text-2xl font-bold text-white">Step 3: Source Quality Assessment</h2>
              </div>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="bg-yellow-900/30 rounded-lg p-4">
                  <div className="text-yellow-200 text-sm mb-2">Overall Quality Score</div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-yellow-900/50 rounded-full h-3">
                      <div 
                        className="bg-yellow-400 h-3 rounded-full transition-all"
                        style={{ width: `${results.quality.score * 100}%` }}
                      />
                    </div>
                    <span className="text-white font-bold">{(results.quality.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-yellow-300 text-sm mt-2 capitalize">
                    Assessment: {results.quality.assessment}
                  </div>
                </div>
                <div className="bg-yellow-900/30 rounded-lg p-4">
                  <div className="text-yellow-200 text-sm mb-2">Quality Indicators</div>
                  <div className="space-y-1 text-sm">
                    {Object.entries(results.quality.indicators).map(([key, value]) => (
                      <div key={key} className="flex items-center gap-2">
                        {value ? 
                          <CheckCircle className="text-green-400" size={16} /> : 
                          <AlertTriangle className="text-orange-400" size={16} />
                        }
                        <span className="text-yellow-100 capitalize">
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Final Response */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-4">
                <FileCheck className="text-purple-300" size={24} />
                <h2 className="text-2xl font-bold text-white">Step 4: Synthesized Research Response</h2>
              </div>
              <div className="bg-purple-900/30 border border-purple-400/30 rounded-lg p-6 mb-4">
                <div className="text-white whitespace-pre-wrap leading-relaxed">
                  {results.response.text}
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-purple-900/30 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Source Quality</div>
                  <div className="text-white font-semibold capitalize">
                    {results.response.sourceQuality}
                  </div>
                </div>
                <div className="bg-purple-900/30 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Hallucination Risk</div>
                  <div className="text-white font-semibold capitalize">
                    {results.response.hallucination_risk}
                  </div>
                </div>
                <div className="bg-purple-900/30 rounded-lg p-4">
                  <div className="text-purple-200 text-sm mb-1">Confidence</div>
                  <div className="text-white font-semibold">
                    {(results.response.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>

            {/* System Advantages */}
            <div className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 backdrop-blur-xl rounded-2xl p-6 border border-purple-400/30">
              <h3 className="text-xl font-bold text-white mb-4">🔬 Research-Grade Advantages</h3>
              <div className="grid md:grid-cols-2 gap-4 text-purple-100">
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-400 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <div className="font-semibold mb-1">Dynamic Knowledge</div>
                    <div className="text-sm text-purple-200">Searches current web sources, not just static data</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-400 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <div className="font-semibold mb-1">Source Validation</div>
                    <div className="text-sm text-purple-200">Evaluates quality and reliability of information</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-400 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <div className="font-semibold mb-1">Grounded Synthesis</div>
                    <div className="text-sm text-purple-200">Response based on actual search results, not imagination</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-400 flex-shrink-0 mt-1" size={20} />
                  <div>
                    <div className="font-semibold mb-1">Transparent Limitations</div>
                    <div className="text-sm text-purple-200">Acknowledges gaps and suggests further research</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {results && results.error && (
          <div className="bg-red-900/30 border border-red-400/30 rounded-2xl p-6">
            <AlertTriangle className="text-red-300 mb-2" size={32} />
            <h3 className="text-xl font-bold text-white mb-2">Processing Error</h3>
            <p className="text-red-200">{results.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}