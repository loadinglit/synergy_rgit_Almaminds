import React, { useState, useEffect } from 'react';
import { Copy, Download, Loader } from 'lucide-react';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

// Define types for our ad data
interface AdCreative {
  ad_type: string;
  headline: string;
  description: string;
  call_to_action: string;
  target_audience: string;
  clip_path: string;
  start_time: number;
  end_time: number;
}

interface AdStrategy {
  campaign_objective: string;
  audience_segments: string[];
  bidding_strategy: string;
  targeting_recommendations: string[];
  performance_metrics: string[];
}

interface AdResults {
  video_id: string;
  title: string;
  ad_creatives: AdCreative[];
  ad_strategy: AdStrategy;
}

export const AdCreatives = () => {
  const [adResults, setAdResults] = useState<AdResults | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Hardcoded video path - this is what the user specified
  const VIDEO_PATH = "../backend/processed_videos/20250319_035810/source_video.mp4";
  
  useEffect(() => {
    // Automatically process the video file on component mount
    processVideo();
  }, []);
  
  const processVideo = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Call backend to process the video file directly
      const response = await fetch('http://localhost:8000/process-local-video/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_path: VIDEO_PATH
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process video');
      }
      
      const data = await response.json();
      setAdResults(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    alert("Text copied to clipboard!");
  };
  
  const handleExportVideo = (clipPath: string) => {
    window.open(`http://localhost:8000/download/?path=${encodeURIComponent(clipPath)}`, '_blank');
  };
  
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-red-600">Ad Creatives</h1>
      
      {loading ? (
        <Card className="border-red-400 flex items-center justify-center p-12">
          <div className="text-center">
            <Loader className="w-12 h-12 animate-spin text-red-500 mx-auto mb-4" />
            <p className="text-red-600 text-lg">Processing video from {VIDEO_PATH}</p>
            <p className="text-red-400 text-sm mt-2">This may take a minute or two</p>
          </div>
        </Card>
      ) : error ? (
        <Card className="border-red-400 p-6 bg-red-50">
          <CardTitle className="text-red-600">Error</CardTitle>
          <CardContent>
            <p className="text-red-500 mb-4">{error}</p>
            <Button onClick={processVideo} className="bg-red-500 text-white hover:bg-red-600">
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : adResults && adResults.ad_creatives?.length > 0 ? (
        <div className="grid gap-8">
          <Card className="border-red-400">
            <CardTitle className="text-red-600 p-6">Generated Ad from {VIDEO_PATH}</CardTitle>
            <CardContent>
              <div className="space-y-6">
                {adResults.ad_creatives.map((creative, index) => (
                  <div key={index} className="border border-red-400 rounded-lg p-6 bg-red-50">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-xl mb-2 text-red-700">{creative.headline}</h3>
                        <p className="text-red-600">{creative.description}</p>
                        <div className="mt-2 text-sm bg-red-100 inline-block px-2 py-1 rounded">
                          {creative.ad_type} • {Math.round(creative.end_time - creative.start_time)}s
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-red-500 text-red-600 hover:bg-red-500 hover:text-white"
                          onClick={() => handleCopyText(`${creative.headline}\n${creative.description}\nCTA: ${creative.call_to_action}`)}
                        >
                          <Copy className="w-4 h-4 mr-2" />
                          Copy
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-red-500 text-red-600 hover:bg-red-500 hover:text-white"
                          onClick={() => handleExportVideo(creative.clip_path)}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </div>
                    
                    {/* Video preview */}
                    {creative.clip_path && (
                      <div className="mt-4 bg-black rounded-lg overflow-hidden relative">
                        <video 
                          className="w-full h-auto" 
                          controls
                        >
                          <source src={`http://localhost:8000/stream/?path=${encodeURIComponent(creative.clip_path)}`} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    )}

                    {/* Headlines, Description and CTA Section */}
                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                        <h4 className="font-medium mb-2 text-red-700">Headline</h4>
                        <p className="text-sm text-red-600">{creative.headline}</p>
                      </div>
                      <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                        <h4 className="font-medium mb-2 text-red-700">Description</h4>
                        <p className="text-sm text-red-600">{creative.description}</p>
                      </div>
                      <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                        <h4 className="font-medium mb-2 text-red-700">Call to Action</h4>
                        <p className="text-sm text-red-600">{creative.call_to_action}</p>
                      </div>
                    </div>
                    
                    {/* Target audience info */}
                    <div className="mt-4 bg-red-50 p-4 rounded-lg border border-red-300">
                      <h4 className="font-medium mb-2 text-red-700">Target Audience</h4>
                      <p className="text-sm text-red-600">{creative.target_audience}</p>
                    </div>
                  </div>
                ))}

                {/* Campaign Strategy Section */}
                {adResults.ad_strategy && (
                  <Card className="border-red-400 mt-8">
                    <CardTitle className="text-red-600 p-6">Ad Campaign Strategy</CardTitle>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                          <h4 className="font-medium mb-2 text-red-700">Campaign Objective</h4>
                          <p className="text-red-600">{adResults.ad_strategy.campaign_objective}</p>
                        </div>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                          <h4 className="font-medium mb-2 text-red-700">Bidding Strategy</h4>
                          <p className="text-red-600">{adResults.ad_strategy.bidding_strategy}</p>
                        </div>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                          <h4 className="font-medium mb-2 text-red-700">Audience Segments</h4>
                          <ul className="text-sm space-y-1 text-red-600">
                            {adResults.ad_strategy.audience_segments.map((segment, idx) => (
                              <li key={idx}>• {segment}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="bg-red-50 p-4 rounded-lg border border-red-300">
                          <h4 className="font-medium mb-2 text-red-700">Performance Metrics</h4>
                          <ul className="text-sm space-y-1 text-red-600">
                            {adResults.ad_strategy.performance_metrics.map((metric, idx) => (
                              <li key={idx}>• {metric}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card className="border-red-400 p-6">
          <CardTitle className="text-red-600">No Ad Creatives</CardTitle>
          <CardContent>
            <p className="mb-4">No ad creatives were generated from the video.</p>
            <Button
              className="bg-red-500 text-white hover:bg-red-700"
              onClick={processVideo}
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
